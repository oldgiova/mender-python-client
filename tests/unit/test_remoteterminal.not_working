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

import logging as log

import pytest
import pytest_asyncio

import mender.remoteterminal.remoteterminal as rt

@pytest.fixture
def params():
    testInstance = rt.RemoteTerminal()
    testInstance.client = "websocket.test"
    #xtestInstance._context.config.ServerURL = "https://docker.mender.io"
    return testInstance

@pytest.fixture
def mock_sleep(create_mock_coro, monkeypatch):
    mock_sleep, _ = create_mock_coro(to_patch="rt.asyncio.sleep")
    return mock_sleep

@pytest.fixture
def create_mock_coro(mocker, monkeypatch):
    def _create_mock_patch_coro(to_patch=None):
        mock = mocker.Mock()

        async def _coro(*args, **kwargs):
            return mock(*args, **kwargs)

        if to_patch: 
            monkeypatch.setattr(to_patch, _coro)
        return mock, _coro

    return _create_mock_patch_coro

@pytest.mark.asyncio
async def test_ws_connect(params):  
    assert not params._ws_connected  
    await rt.RemoteTerminal.ws_connect(params)
    assert params._ws_connected
    assert 1 == mock_sleep.call_count