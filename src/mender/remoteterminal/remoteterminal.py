# Copyright 2021 Northern.tech AS
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import asyncio
import logging
import os
import pty
import select
import ssl
import subprocess
import threading

import msgpack  # type: ignore
import websockets
from websockets.exceptions import WebSocketException

log = logging.getLogger(__name__)

# mender-connect protocol messages, taken from:
# /mendersoftware/go-lib-micro/ws/shell/model.go
MESSAGE_TYPE_SHELL_COMMAND = "shell"
MESSAGE_TYPE_SPAWN_SHELL = "new"
MESSAGE_TYPE_STOP_SHELL = "stop"


class RemoteTerminal:
    """ This class serves the RemoteTerminal aka a remote shell feature
        over the WebSocket. This supposed to be the only instance and
        serves single connection
    """

    def __init__(self):
        log.info("RemoteTerminal initialized")

        self.client = None
        self.sid = None
        self.ws_connected = False
        self.context = None
        self.session_started = False
        self.ext_headers = None
        self.ssl_context = None
        self.master = None
        self.slave = None
        self.shell = None

    async def ws_connect(self):
        """connects to the backend websocket server."""

        # from config we receive sth like: "ServerURL": "https://docker.mender.io"
        # we need replace the protcol and API entry point to achive like this:
        # "wss://docker.mender.io/api/devices/v1/deviceconnect/connect"
        uri = (
            self.context.config.ServerURL.replace("https", "wss")
            + "/api/devices/v1/deviceconnect/connect"
        )
        try:
            self.client = await websockets.connect(
                uri, ssl=self.ssl_context, extra_headers=self.ext_headers
            )
            self.ws_connected = True
            log.debug(f"connected to: {uri}")
        except WebSocketException as ws_exception:
            log.error(f"ws_connect: {ws_exception}")

    async def proto_msg_processor(self):
        """after having connected to the backend it processes the protocol messages.
        This function is called in a thread."""

        await self.ws_connect()
        if self.client is None:
            log.debug("Websocket connection failed")
            return -1
        log.debug("Websocket connected")
        try:
            while True:
                packed_msg = await self.client.recv()
                msg: dict = msgpack.unpackb(packed_msg, raw=False)
                hdr = msg["hdr"]
                if hdr["typ"] == MESSAGE_TYPE_SPAWN_SHELL and not self.session_started:
                    self.sid = hdr["sid"]
                    self.session_started = True
                    await self.send_client_status_to_backend(MESSAGE_TYPE_SPAWN_SHELL)
                    self.open_terminal()
                    self.start_transmitting_thread()
                elif hdr["typ"] == MESSAGE_TYPE_SHELL_COMMAND:
                    self.write_command_to_shell(msg)
                elif hdr["typ"] == MESSAGE_TYPE_STOP_SHELL:
                    self.shell.kill()
                    self.master = None
                    self.slave = None
                    await self.send_client_status_to_backend(MESSAGE_TYPE_STOP_SHELL)
                    self.session_started = False

        except WebSocketException as ws_exception:
            log.error(f"proto_msg_processor: {ws_exception}")

    async def send_terminal_stdout_to_backend(self):
        """reads the data from the shell's stdout descriptor, packs into the protocol msg
        and sends to the backend.
        This function is called in a thread."""

        if not self.ws_connected:
            log.debug("leaving send_terminal_stdout_to_backend")
            return -1
        while True:
            try:
                shell_stdout = os.read(self.master, 102400)
                resp_header = {
                    "proto": 1,
                    "typ": MESSAGE_TYPE_SHELL_COMMAND,
                    "sid": self.sid,
                }
                resp_props = {"status": 1}
                response = {
                    "hdr": resp_header,
                    "props": resp_props,
                    "body": shell_stdout,
                }
                await self.client.send(msgpack.packb(response, use_bin_type=True))
            except TypeError as type_error:
                log.error(f"send_terminal_stdout_to_backend: {type_error}")
            except IOError as io_error:
                log.error(f"send_terminal_stdout_to_backend: {io_error}")

    async def send_client_status_to_backend(self, status):
        """send connection status to backend"""

        try:
            resp_header = {"proto": 1, "typ": status, "sid": self.sid}
            resp_props = {"status": 1}
            response = {"hdr": resp_header, "props": resp_props, "body": ""}
            await self.client.send(msgpack.packb(response, use_bin_type=True))
            log.debug(f"Status: {status} sent successfully")
        except TypeError as type_error:
            log.error(f"send_client_status_to_backend: {type_error}")
        except IOError as io_error:
            log.error(f"send_client_status_to_backend: {io_error}")

    def write_command_to_shell(self, msg):
        """writes the command to the shell's stdin file descriptor"""

        _, ready, _, = select.select([], [self.master], [])
        for stream in ready:
            try:
                os.write(stream, msg["body"])
            except IOError as io_error:
                log.error(f"write_command_to_shell: {io_error}")

    def start_transmitting_thread(self):
        """starts transmitting thread"""

        log.debug("about to start transmitting thread")
        thread_send = threading.Thread(
            target=lambda: asyncio.run(self.send_terminal_stdout_to_backend())
        )
        thread_send.start()

    def run_msg_processor_thread(self):
        """starts the protocol messages thread"""

        log.debug("about to start msg processor thread")
        thread_ws = threading.Thread(
            target=lambda: asyncio.run(self.proto_msg_processor())
        )
        thread_ws.start()

    def open_terminal(self):
        """opens new pty/tty, invokes the new shell and connects them"""
        self.master, self.slave = pty.openpty()
        # by default the shell owner is root
        self.shell = subprocess.Popen(
            [self.context.remoteTerminalConfig.ShellCommand, "-i"],
            start_new_session=True,
            stdin=self.slave,
            stdout=self.slave,
            stderr=self.slave,
        )

    def load_server_certificate(self):
        """tries to load SSL certificate from config file

        and if not found then creates default context based on CAs"""

        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        if self.context.config.ServerCertificate:
            self.ssl_context.load_verify_locations(
                self.context.config.ServerCertificate
            )
        else:
            self.ssl_context = ssl.create_default_context()

    def run(self, context):
        """the main entry point for running the whole functionality. Supposed to be run
        after the device has authorized and JWT token obtained. """

        self.context = context
        try:
            if context.remoteTerminalConfig.RemoteTerminal:
                if context.authorized and not self.ws_connected:
                    self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

                    self.load_server_certificate()

                    # the JWT should already be acquired as we supposed to be in AuthorizedState
                    self.ext_headers = {"Authorization": "Bearer " + context.JWT}

                    self.run_msg_processor_thread()
                    log.debug("The websocket msg processor started.")
            else:
                log.info("RemoteTerminal not enabled in mender-connect.conf")
        except AttributeError:
            log.error("Missing configuration file: mender-connect.conf")
