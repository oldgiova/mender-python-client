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
import json
import logging
import os.path

import pytest

from mender.log import menderlogger
from mender.settings import settings

log = logging.getLogger("mender.logTesting")


@pytest.fixture(name="set_up_menderlogger", autouse=True)
def fixture_set_up_menderlogger(tmpdir):
    d = tmpdir.mkdir("test_logger")
    log_file = os.path.join(d, "deployment.log")
    settings.PATHS.deployment_log = d

    class Args:
        log_file = False
        log_level = "debug"
        no_syslog = False

    menderlogger.setup(Args())
    return log_file


@pytest.fixture(name="set_log_level_info", autouse=True)
def fixture_set_log_level_info(caplog):
    """Set the log-level capture to info for all tests"""
    caplog.set_level(logging.INFO)


class TestDeploymentLogger:
    def test_logger(self, caplog, set_up_menderlogger):
        log_file = set_up_menderlogger
        log.info("Foobar")
        # Should not show up in log, as the logger is not enabled
        assert os.path.getsize(log_file) == 0
        log.parent.deployment_log_handler.enable()
        log.info("BarBaz")
        assert os.path.getsize(log_file) != 0
        with open(log_file) as fh:
            data = json.loads(fh.read().strip())
            assert data["message"] == "BarBaz"
            assert data["level"] == "INFO"
        assert "Foobar" in caplog.text
        assert "BarBaz" in caplog.text

    def test_log_marshalling(self, caplog):
        log.parent.deployment_log_handler.enable()
        log.info("foo")
        log.error("bar")
        data = log.parent.deployment_log_handler.marshal()
        assert data[0]["message"] == "foo"
        assert data[0]["level"] == "INFO"
        assert data[1]["message"] == "bar"
        assert data[1]["level"] == "ERROR"
        # stream log
        assert "foo" in caplog.text
        assert "bar" in caplog.text
