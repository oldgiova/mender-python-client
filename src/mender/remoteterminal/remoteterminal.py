# Copyright 2020 Northern.tech AS
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

import logging
import asyncio
import os
import pty
import select
import ssl
import subprocess
import threading

import msgpack
import websockets

from websockets.exceptions import WebSocketException

log = logging.getLogger(__name__)

#mender-connect protocol messeges, taken from:
#/mendersoftware/go-lib-micro/ws/shell/model.go
MESSAGE_TYPE_SHELL_COMMAND = 'shell'
MESSAGE_TYPE_SPAWN_SHELL   = 'new'
MESSAGE_TYPE_STOP_SHELL    = 'stop'


class RemoteTerminal:
    """ This class serves the RemoteTerminal aka remote shell feature
        over the WebSocket. This supposed to be the only instance and
        serves single or many concurrent connections (next release?)
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
        '''connects to backed websocket server'''

        # from config we receive sth like: "ServerURL": "https://docker.mender.io"
        # we need replace the protcol and API entry point to achive like this:
        # "wss://docker.mender.io/api/devices/v1/deviceconnect/connect"
        uri = self.context.config.ServerURL.replace(
            "https", "wss") + "/api/devices/v1/deviceconnect/connect"
        try:
            self.client = await websockets.connect(
                uri, ssl=self.ssl_context, extra_headers=self.ext_headers)
            self.ws_connected = True
            log.debug(f'connected to: {uri}')
        except WebSocketException as ws_exception:
            log.error(f'ws_connect: {ws_exception}')

    async def proto_msg_processor(self):
        '''after having connected to the backend it processes the protocol messages'''

        await self.ws_connect()
        if self.client is None:
            log.debug('Websocket connection failed')
            return -1
        log.debug('Websocket connected')
        try:
            while True:
                packed_msg = await self.client.recv()
                msg: dict = msgpack.unpackb(packed_msg, raw=False)
                hdr = msg['hdr']
                if hdr['typ'] == MESSAGE_TYPE_SPAWN_SHELL and not self.session_started:
                    self.sid = hdr['sid']
                    self.session_started = True
                    self.open_terminal()
                    self.start_transmitting_thread()
                if hdr['typ'] == MESSAGE_TYPE_SHELL_COMMAND:
                    self.write_command_to_shell(msg)
                if hdr['typ'] == MESSAGE_TYPE_STOP_SHELL:
                    self.shell.kill()
                    self.master = None
                    self.slave = None
                    self.session_started = False

        except WebSocketException as ws_exception:
            log.error(f'proto_msg_processor: {ws_exception}')

    async def send_terminal_stdout_to_backend(self):
        '''reads the data from the shell's stdout descriptor, packs into the protocol msg
        and send to the backend'''

        if not self.ws_connected:
            log.debug('leaving send_terminal_stdout_to_backend')
            return -1
        while True:
            try:
                data = os.read(self.master, 102400)
                resp_header = {'proto': 1, 'typ': MESSAGE_TYPE_SHELL_COMMAND, 'sid': self.sid}
                resp_props = {'status': 1}
                response = {'hdr': resp_header,
                            'props': resp_props, 'body': data}
                await self.client.send(msgpack.packb(response, use_bin_type=True))
                log.debug('data sent')
            except TypeError as type_error:
                log.error(type_error)
            except IOError as io_error:
                log.error(f'send_stdout: {io_error}')

    def write_command_to_shell(self, msg):
        '''writes the command to the shell's stdin file descriptor'''

        _, ready, _, = select.select([], [self.master], [])
        for stream in ready:
            try:
                os.write(stream, msg['body'])
            except IOError as io_error:
                log.error(f'while writing to master: {io_error}')

    def thread_f_transmit(self):
        try:
            asyncio.run(self.send_terminal_stdout_to_backend())
        except Exception as inst:
            log.error(f'in thread_f_transmit: {inst}')

    def thread_f_ws(self):
        try:
            asyncio.run(self.proto_msg_processor())
        except Exception as inst:
            log.error(f'in thread_f_ws: {inst}')

    def start_transmitting_thread(self):
        log.debug('about to start send thread')
        thread_send = threading.Thread(target=self.thread_f_transmit)
        thread_send.start()

    def run_main_working_thread(self):
        log.debug('about to start never ending thread, websocket connection')
        thread_ws = threading.Thread(target=self.thread_f_ws)
        thread_ws.start()

    def open_terminal(self):
        '''opens new pty/tty, invokes the new shell and connects them'''
        self.master, self.slave = pty.openpty()
        #by default the shell owner is root
        self.shell = subprocess.Popen(
            [self.context.config.ShellCommand, "-i"],
            start_new_session=True,
            stdin=self.slave,
            stdout=self.slave,
            stderr=self.slave
        )

    def run(self, context):
        self.context = context
        if context.remoteTerminalConfig.RemoteTerminal and context.authorized and not self.ws_connected:
            self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

            if context.config.ServerCertificate:
                self.ssl_context.load_verify_locations(
                    context.config.ServerCertificate)
            else:
                self.ssl_context = ssl.create_default_context()

            # the JWT should already be acquired as we supposed to be in AuthorizedState
            self.ext_headers = {
                'Authorization': 'Bearer ' + context.JWT
            }

            self.run_main_working_thread()
            log.debug("i've just invoked the websocket thread")
