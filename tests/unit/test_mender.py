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

import pytest

from mender import mender as main
from mender.bootstrap import bootstrap
from mender.client import authorize, deployments
from mender.log import menderlogger
from mender.log.log import DeploymentLogHandler
from mender.settings import settings
from mender.statemachine import statemachine


@pytest.fixture(autouse=True)
def set_log_level_info(caplog):
    """Set the log-level capture to info for all tests"""
    caplog.set_level(log.DEBUG)


@pytest.fixture(autouse=True)
def setup_mender_logger():
    """Set the mender logger and deployment handler"""

    class Args:
        log_file = False
        log_level = "debug"
        no_syslog = False

    menderlogger.setup(Args())


@pytest.fixture(name="ctx")
def fixture_ctx():
    settings.PATHS.deployment_log = os.getcwd()
    context = statemachine.Context()
    context.JWT = "foobar"
    return context


@pytest.fixture(name="args")
def fixture_args():
    class Args:
        forcebootstrap = False
        success = False
        failure = False

    return Args()


def test_run_daemon(args, monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(statemachine, "run", lambda *args, **kwargs: None)
        main.run_daemon(args)


def test_show_artifact(caplog, monkeypatch, tmpdir):
    d = tmpdir.mkdir("test_show_artifact")
    with monkeypatch.context() as m:
        m.setattr(settings.PATHS, "artifact_info", "/i/do/not/exist/")
        main.show_artifact({})
        assert "No device_type file found" in caplog.text
    with monkeypatch.context() as m:
        artifact_info = d.join("artifact_info")
        artifact_info.write("artifact_name=release-0.1")
        m.setattr(settings.PATHS, "artifact_info", artifact_info)
        main.show_artifact({})
        assert "artifact_name=release-0.1" in caplog.text


def test_run_bootstrap(args, monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(bootstrap, "now", lambda *args, **kwargs: None)
        main.run_bootstrap(args)


def test_run_version(capsys):
    main.run_version({})
    assert "version: master" in capsys.readouterr().out


def test_report(args, ctx, caplog, tmpdir, monkeypatch):
    d = tmpdir.mkdir("test_report")
    # Failed to authorize
    with monkeypatch.context() as m:
        m.setattr(statemachine, "Context", lambda *args, **kwargs: ctx)
        m.setattr(authorize, "request", lambda *args, **kwargs: "")
        with pytest.raises(SystemExit):
            main.report(args)
        assert "Failed to authorize with the Mender server" in caplog.text
    # No lock-file present
    with monkeypatch.context() as m:
        m.setattr(statemachine, "Context", lambda *args, **kwargs: ctx)
        m.setattr(authorize, "request", lambda *args, **kwargs: "")
        with pytest.raises(SystemExit):
            main.report(args)
            assert "No update in progress" in caplog.text
    # Lockfile is present for the rest of the tests
    lock_file = d.join("update.lock")
    lock_file.write("deployment-10101010")
    monkeypatch.setattr(settings.PATHS, "lockfile_path", lock_file)
    # Report success - Fail
    with monkeypatch.context() as m:
        m.setattr(statemachine, "Context", lambda *args, **kwargs: ctx)
        m.setattr(authorize, "request", lambda *args, **kwargs: "JWTToken")
        m.setattr(args, "success", True)
        m.setattr(deployments, "report", lambda *args, **kwargs: False)
        with pytest.raises(SystemExit):
            main.report(args)
        assert "Reporting a successful update to the Mender server" in caplog.text
        assert (
            "Failed to report the successful update status to the Mender server"
            in caplog.text
        )
    # Report success - Success
    with monkeypatch.context() as m:
        m.setattr(statemachine, "Context", lambda *args, **kwargs: ctx)
        m.setattr(authorize, "request", lambda *args, **kwargs: "jwtTokenText")
        m.setattr(args, "success", True)
        m.setattr(deployments, "report", lambda *args, **kwargs: True)
        main.report(args)
        assert "Reporting a successful update to the Mender server" in caplog.text
    # Report failure - Fail: No deploymentLogHandler
    with monkeypatch.context() as m:
        m.setattr(statemachine, "Context", lambda *args, **kwargs: ctx)
        m.setattr(authorize, "request", lambda *args, **kwargs: "JWTToken")
        m.setattr(args, "failure", True)
        with pytest.raises(SystemExit):
            main.report(args)
        assert "Reporting a failed update to the Mender server" in caplog.text

    class MockLogger:
        handlers = [DeploymentLogHandler()]

    # Report failure - Fail: Report
    with monkeypatch.context() as m:
        m.setattr(statemachine, "Context", lambda *args, **kwargs: ctx)
        m.setattr(authorize, "request", lambda *args, **kwargs: "JWTToken")
        m.setattr(args, "failure", True)
        m.setattr(deployments, "report", lambda *args, **kwargs: False)
        with pytest.raises(SystemExit):
            main.report(args)
        assert "Reporting a failed update to the Mender server" in caplog.text
        assert (
            "Failed to report the failed update status to the Mender server"
            in caplog.text
        )
    # No report status given
    with monkeypatch.context() as m:
        m.setattr(statemachine, "Context", lambda *args, **kwargs: ctx)
        m.setattr(authorize, "request", lambda *args, **kwargs: "JWTToken")
        m.setattr(log, "getLogger", lambda name: MockLogger)
        with pytest.raises(SystemExit):
            main.report(args)
        assert "No report status given" in caplog.text


def test_run_main(caplog, capsys, tmpdir):
    d = tmpdir.mkdir("test_run_main")
    # No arguments given
    with pytest.raises(SystemExit):
        main.main([""])
    assert "choose from" in capsys.readouterr().err
    # Custom data directory path
    main.main(["--data", str(d)])
    # Custom log-level
    main.main(["--data", str(d), "--log-level=debug"])
    assert "Log level set to DEBUG" in caplog.text
    # Non valid log-level
    main.main(["--data", str(d), "--log-level=whatever"])
    assert "Log level set to INFO" in caplog.text
