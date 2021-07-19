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
import logging as log
import os

import pytest

from mender.config import config

GLOBAL_TESTDATA = {
    "InventoryPollIntervalSeconds": 200,
    "RootfsPartA": "/dev/hda2",
    "RootfsPartB": "/dev/hda3",
    "ServerURL": "https://hosted.mender.io",
    "TenantToken": """eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJtZW5k
ZXIudGVuYW50IjoiNTllMGIwNzA3ZDZmMGQwMGYwYzFmZTM4IiwiaXNzIjoiTWVuZ
GVyIiwic3ViIjoiNTllMGIwNzA3ZDZmMGQwMGYwYzFmZTM4In0.uAw2KPrwH6DPT
2ZnDLm4p6lZPlIDbK07QA2I4qcWrLQ7R-WVEuQSx4WmlXYPAgRGU0zeOPiRW-i9_faoY
56tJuLA2-DRMPcoQTn9kieyu8eCB60-gMg10RPa_XCwTAIot8eBjUSPSxjTvFm0pZ3N8
GeBi412EBUw_N2ZVsdto4bhivOZHzJwS5qZoRrCY15_5qa6-9lVbSWVZdzAjoruZKteH
a_KSGtDdg_586QZRzDUXH-kwhItkDJz5LlyiWXpVpk3f4ujX8iwk-u42WBwYbuWN4g
Ti4mNozX4tR_C9OgE-Xf3vmFkIBc_JfJeNUxsp-rPKERDrVxA_sE2l0OVoEZzcquw3c
df2ophsIFIu7scEWavKjZlmEm_VB6vZVfy1NtMkq1xJnrzssJf-eDYti-CJM3E6lSsO
_OmbrDbLa4-bxl8GJjRNH86LX6UOxjgatxaZyKEZhDG-gK6_f57c7MiA0KglOGuA
GNWAxI8A7jyOqKOvY3iemL9TvbKpoIP""",
}

LOCAL_TESTDATA = {
    "InventoryPollIntervalSeconds": 100,
    "UpdatePollIntervalSeconds": 100,
    "RetryPollIntervalSeconds": 100,
}


@pytest.fixture(scope="session", name="local_and_global")
def fixture_local_and_global():
    return config.load(
        "tests/unit/data/configs/local_mender.conf",
        "tests/unit/data/configs/global_medner.conf",
    )


@pytest.fixture(scope="session", name="global_only")
def fixture_():
    with open("tests/unit/data/configs/global_mender_testdata.conf", "w") as f:
        json.dump(GLOBAL_TESTDATA, f)
    yield config.load("", "tests/unit/data/configs/global_mender_testdata.conf")
    if os.path.isfile("tests/unit/data/configs/global_mender_testdata.conf"):
        os.remove("tests/unit/data/configs/global_mender_testdata.conf")


@pytest.fixture(scope="session", name="local_only")
def fixture_local_only():
    with open("tests/unit/data/configs/local_mender_testdata.conf", "w") as f:
        json.dump(LOCAL_TESTDATA, f)
    yield config.load("", "tests/unit/data/configs/local_mender_testdata.conf")
    if os.path.isfile("tests/unit/data/configs/local_mender_testdata.conf"):
        os.remove("tests/unit/data/configs/local_mender_testdata.conf")


@pytest.fixture(scope="session", name="local_priority")
def fixture_local_priority():
    with open("tests/unit/data/configs/local_mender_testdata.conf", "w") as f:
        json.dump(LOCAL_TESTDATA, f)
    with open("tests/unit/data/configs/global_mender_testdata.conf", "w") as f:
        json.dump(GLOBAL_TESTDATA, f)

    yield config.load(
        "tests/unit/data/configs/local_mender_testdata.conf",
        "tests/unit/data/configs/global_mender_testdata.conf",
    )
    if os.path.isfile("tests/unit/data/configs/global_mender_testdata.conf"):
        os.remove("tests/unit/data/configs/global_mender_testdata.conf")
    if os.path.isfile("tests/unit/data/configs/local_mender_testdata.conf"):
        os.remove("tests/unit/data/configs/local_mender_testdata.conf")


class TestConfigInstance:
    def test_both_instance(self, local_and_global):
        assert isinstance(local_and_global, config.Config)

    def test_glob_instance(self, global_only):
        assert isinstance(global_only, config.Config)

    def test_local_instance(self, local_only):
        assert isinstance(local_only, config.Config)

    def test_no_path_instance(self):
        with pytest.raises(config.NoConfigurationFileError):
            config.load("", "")


class TestLocal:
    def test_local_values(self, local_only):
        assert local_only.ServerURL == ""
        assert local_only.RootfsPartA == ""
        assert local_only.RootfsPartB == ""
        assert local_only.TenantToken == ""
        assert local_only.InventoryPollIntervalSeconds == 100
        assert local_only.UpdatePollIntervalSeconds == 100
        assert local_only.RetryPollIntervalSeconds == 100
        assert local_only.ServerCertificate == ""


class TestGlobal:
    def test_no_path(self, global_only):
        assert global_only.ServerURL == "https://hosted.mender.io"
        assert global_only.RootfsPartA == "/dev/hda2"
        assert global_only.RootfsPartB == "/dev/hda3"
        assert (
            global_only.TenantToken
            == """eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJtZW5k
ZXIudGVuYW50IjoiNTllMGIwNzA3ZDZmMGQwMGYwYzFmZTM4IiwiaXNzIjoiTWVuZ
GVyIiwic3ViIjoiNTllMGIwNzA3ZDZmMGQwMGYwYzFmZTM4In0.uAw2KPrwH6DPT
2ZnDLm4p6lZPlIDbK07QA2I4qcWrLQ7R-WVEuQSx4WmlXYPAgRGU0zeOPiRW-i9_faoY
56tJuLA2-DRMPcoQTn9kieyu8eCB60-gMg10RPa_XCwTAIot8eBjUSPSxjTvFm0pZ3N8
GeBi412EBUw_N2ZVsdto4bhivOZHzJwS5qZoRrCY15_5qa6-9lVbSWVZdzAjoruZKteH
a_KSGtDdg_586QZRzDUXH-kwhItkDJz5LlyiWXpVpk3f4ujX8iwk-u42WBwYbuWN4g
Ti4mNozX4tR_C9OgE-Xf3vmFkIBc_JfJeNUxsp-rPKERDrVxA_sE2l0OVoEZzcquw3c
df2ophsIFIu7scEWavKjZlmEm_VB6vZVfy1NtMkq1xJnrzssJf-eDYti-CJM3E6lSsO
_OmbrDbLa4-bxl8GJjRNH86LX6UOxjgatxaZyKEZhDG-gK6_f57c7MiA0KglOGuA
GNWAxI8A7jyOqKOvY3iemL9TvbKpoIP"""
        )
        assert global_only.InventoryPollIntervalSeconds == 200
        assert global_only.UpdatePollIntervalSeconds == 5
        assert global_only.RetryPollIntervalSeconds == 5
        assert global_only.ServerCertificate == ""


class TestLocalPriority:
    def test_local_priority(self, local_priority):
        # Local IventoryPollIntervalSeconds == 100 and Global IventoryPollIntervalSeconds == 200
        assert local_priority.InventoryPollIntervalSeconds == 100

    def test_with_no_local_server_url(self, local_priority):
        # Local serverURL is non existing and Global is https://hosted.mender.io
        assert local_priority.ServerURL == "https://hosted.mender.io"


class TestFaultyJSONfile:
    def test_both_faulty_json(self):
        with open("tests/unit/data/configs/local_mender_faulty.conf", "w") as f:
            json.dump(LOCAL_TESTDATA, f)
            f.write("this makes the json file faulty")
        with open("tests/unit/data/configs/global_mender_faulty.conf", "w") as f:
            json.dump(GLOBAL_TESTDATA, f)
            f.write("this makes the json file faulty")

        with pytest.raises(json.decoder.JSONDecodeError):
            config.load(
                "tests/unit/data/configs/local_mender_faulty.conf",
                "config/global_mender_faulty.conf",
            )
        os.remove("tests/unit/data/configs/global_mender_faulty.conf")

    def test_local_faulty_json(self):
        with open("tests/unit/data/configs/local_mender_faulty.conf", "w") as f:
            json.dump(LOCAL_TESTDATA, f)
            f.write("this makes the json file faulty")
        with pytest.raises(json.decoder.JSONDecodeError):
            config.load(
                "tests/unit/data/configs/local_mender_faulty.conf",
                "config/global_mender.conf",
            )
        os.remove("tests/unit/data/configs/local_mender_faulty.conf")

    def test_global_faulty_json(self):
        with open("tests/unit/data/configs/global_mender_faulty.conf", "w") as f:
            json.dump(GLOBAL_TESTDATA, f)
            f.write("this makes the json file faulty")
        with pytest.raises(json.decoder.JSONDecodeError):
            config.load(
                "tests/unit/data/configs/local_mender.conf",
                "tests/unit/data/configs/global_mender_faulty.conf",
            )
        os.remove("tests/unit/data/configs/global_mender_faulty.conf")


class TestFileNotFound:
    @pytest.fixture(autouse=True)
    def set_log_level(self, caplog):
        caplog.set_level(log.DEBUG)

    def test_file_not_found_error_both(self, caplog):
        with pytest.raises(config.NoConfigurationFileError):
            config.load("", "")
        assert "Global configuration file: '' not found" in caplog.text
        assert "Local configuration file: '' not found" in caplog.text

    def test_file_not_found_error_local(self, caplog):
        config.load("tests/unit/data/configs/local_mender.conf", "")
        assert "Global configuration file: '' not found" in caplog.text
        assert "Local configuration file: '' not found" not in caplog.text

    def test_file_not_found_error_(self, caplog):
        config.load("", "tests/unit/data/configs/global_mender.conf")
        assert "Global configuration file: '' not found" not in caplog.text
        assert "Local configuration file: '' not found" in caplog.text
