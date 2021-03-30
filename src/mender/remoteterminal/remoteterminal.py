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
import fcntl
import os
import pty
import select
import ssl
import subprocess
import threading

import msgpack
import websockets

log = logging.getLogger(__name__)

class RemoteTerminal:
    ''' this class serves the RemoteTerminal aka remote shell feature over the WebSocket.
        This supposed to be the only instance and serves single or many concurrent connections (next release?)
    '''

    def __init__(self):
        log.debug("RemoteTerminal initialized")
        self._ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        # @fixme: check if the file exists
        self._ssl_context.load_verify_locations("/etc/mender/server.crt")

        self._client = None
        self._sid = None
        self._ws_connected = False
        self._hello_failed = False

    async def ws_connect(self):
        # @fixme change to a proper server name
        uri = "wss://docker.mender.io/api/devices/v1/deviceconnect/connect"
        try:
            self._client = await websockets.connect(
                uri, ssl=self._ssl_context, extra_headers=self._ext_headers)
            log.debug(f'connected: {self._client}')
        except Exception as inst:
            log.debug(f'ws_connect: {type(inst)}')
            log.debug(f'ws_connect: {inst}')

    async def ws_send_termina_stdout_to_backend(self):
        # wait for connection in another coroutine
        while not self._ws_connected and not self._hello_failed:
            await asyncio.sleep(1)
        if self._hello_failed:
            log.debug('leaving send_stdout2')
            return -1
        log.debug('send_stdout GO!')
        while True:
            try:
                await asyncio.sleep(1)
                data = os.read(self._master, 102400)
                resp_header = {'proto': 1, 'typ': 'shell', 'sid': self._sid}
                resp_props = {'status': 1}
                response = {'hdr': resp_header, 'props': resp_props, 'body': data}
                log.debug(f'resp: {response}')
                await self._client.send(msgpack.packb(response))
                log.debug('wyslalem')

                # @fixme try another approach: instead of making the fd non-blocking run in a separate asyncio.to_thread (same fixme is down there)
            except Exception as ex_instance:
                log.debug(f'send_stdout: {type(ex_instance)}')
                log.debug(f'send_stdout: {ex_instance}')

    async def ws_read_from_backend_write_to_terminal(self):
#        while self._client is None:
 #           await asyncio.sleep(1)
        await self.ws_connect()
        if self._client is None:
            self._hello_failed = True
            log.debug('hello failed')
            return -1
        log.debug('hello GO!')
        try:
            while True:
                log.debug('about to waiting for msg from backend')
                greeting = await self._client.recv()
                msg: dict = msgpack.unpackb(greeting)
                log.debug(f'msg: {msg}')
                hdr = msg['hdr']
                if hdr['typ'] == 'new':
                    self._sid = hdr['sid']
                    self._ws_connected = True
                if hdr['typ'] == 'shell' :
                    log.debug('waiting for _master for writing')
                    _, ready, _, = select.select([], [self._master], [])
                    for stream in ready:
                        log.debug('stream in _master READY for WRITING')
                        try:
                            os.write(stream, msg['body'])
                            # os.write(stream, 'ls\n'.encode('utf-8'))
                        except Exception as ex_instance:
                            log.debug(f'while writing to master: {type(ex_instance)}')
                            log.debug(f'while writing to master: {ex_instance}')

        except Exception as inst:
            log.debug(f'hello: {type(inst)}')
            log.debug(f'hello: {inst}')

    async def gather(self):
        await asyncio.gather(self.ws_read_from_backend_write_to_terminal(), self.ws_send_termina_stdout_to_backend())

    def thread_f(self):
        try:
            log.debug('about to run asyncio.gather')
            asyncio.run(self.gather())
        except Exception as inst:
            log.debug(f'in Run: {type(inst)}')
            log.debug(f'in Run: {inst}')

    def run(self, context):
        if context.config.RemoteTerminal and context.authorized and not self._ws_connected:
            # the JWT should already be acquired as we supposed to be in AuthorizedState
            self._ext_headers = {
                'Authorization': 'Bearer ' + context.JWT
            }

            # @fixme the following part needs to be moved "after the connection has been established"

            self._master, self._slave = pty.openpty()

            # @fixme try another approach: instead of making the fd non-blocking run in a separate asyncio.to_thread (same fixme is in ws_send_termina_stdout_to_backend)
            fl = fcntl.fcntl(self._master, fcntl.F_GETFL)
            fcntl.fcntl(self._master, fcntl.F_SETFL, fl | os.O_NONBLOCK)

            self._shell = subprocess.Popen(
                ["bash", "-i"], start_new_session=True,
                stdin=self._slave, stdout=self._slave, stderr=self._slave)
            self.background_ws_thread = threading.Thread(target=self.thread_f)
            self.background_ws_thread.start()
            log.debug("i've just invoked the websocket thread")




