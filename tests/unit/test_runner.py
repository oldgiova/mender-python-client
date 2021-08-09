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

import logging as log
import os
import os.path
import stat

import pytest

from mender.scripts import runner
from mender.settings import settings


@pytest.fixture(autouse=True)
def set_log_level_info(caplog):
    """Set the log-level capture to info for all tests"""
    caplog.set_level(log.INFO)


def test_run_sub_updater(monkeypatch, tmpdir):
    d = tmpdir.mkdir("test_lockfile")
    lockfile = os.path.join(d, "lockfile.test")
    install_script = d.join("install")
    install_script.write("#!/bin/sh echo foo")
    os.chmod(install_script, stat.S_IRWXU | stat.S_IRWXO | stat.S_IRWXG)
    with monkeypatch.context() as m:
        m.setattr(settings.PATHS, "lockfile_path", lockfile)
        m.setattr(settings.PATHS, "install_script", install_script)
        assert runner.run_sub_updater("deploymentid-2") == runner.INSTALL_SCRIPT_OK
        assert os.path.exists(lockfile)


def test_no_install_script(caplog, monkeypatch, tmpdir):
    d = tmpdir.mkdir("test_install_script")
    lockfile = os.path.join(d, "lockfile.test")
    install_script = os.path.join(d, "install")
    with monkeypatch.context() as m:
        m.setattr(settings.PATHS, "lockfile_path", lockfile)
        m.setattr(settings.PATHS, "install_script", install_script)
        assert (
            runner.run_sub_updater("deploymentid-2")
            == runner.INSTALL_SCRIPT_NOT_FOUND_ERROR
        )
        assert "No install script found" in caplog.text


def test_install_script_permissions(caplog, monkeypatch, tmpdir):
    d = tmpdir.mkdir("test_install_script")
    lockfile = os.path.join(d, "lockfile.test")
    install_script = d.join("install")
    install_script.write("jibberish")
    with monkeypatch.context() as m:
        m.setattr(settings.PATHS, "lockfile_path", lockfile)
        m.setattr(settings.PATHS, "install_script", install_script)
        assert (
            runner.run_sub_updater("deploymentid-2")
            == runner.INSTALL_SCRIPT_PERMISSION_ERROR
        )
        assert (
            f"The install script '{settings.PATHS.install_script}' has the wrong permissions"
            in caplog.text
        )
