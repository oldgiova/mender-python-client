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
import stat

import pytest

from mender.scripts import artifactinfo, devicetype
from mender.scripts.aggregator import aggregator, identity, inventory


class TestScriptKeyValueAggregator:
    TEST_DATA = [
        (
            "key=value\nkey2=value2\nkey=value2",
            {"key": ["value", "value2"], "key2": ["value2"]},
        ),
        ("key=value key=value", {"key": ["value key=value"]}),
        ("key=value\nkey=val2\nkey=value", {"key": ["value", "val2", "value"]}),
        ("key=val\tkey=val2", {"key": ["val\tkey=val2"]}),
        ("", {}),
    ]

    @pytest.mark.parametrize("data, expected", TEST_DATA)
    def test_parse_key_values(self, data, expected):
        vals = aggregator.ScriptKeyValueAggregator("foo").parse(data)
        assert vals == expected


class TestArtifactInfo:

    TEST_DATA = [
        (
            """
            artifact_name=release-0.1
            artifact_group=test
            """,
            {"artifact_name": ["release-0.1"], "artifact_group": ["test"]},
        ),
        (
            """
            artifact_name=release-0.1
            artifact_name=release-1.0
            """,
            {"artifact_name": ["release-1.0"]},
        ),
    ]

    @pytest.fixture
    def file_create_fixture(self, tmpdir):
        d = tmpdir.mkdir("aggregator")

        def create_script(data):
            f = d.join("script")
            f.write(data)
            os.chmod(f, stat.S_IRWXU | stat.S_IRWXO | stat.S_IRWXG)
            return str(f)

        return create_script

    @pytest.mark.parametrize("data, expected", TEST_DATA)
    def test_get_artifact_info(self, data, expected, file_create_fixture):
        fpath = file_create_fixture(data)
        ainfo = artifactinfo.get(fpath)
        assert ainfo == expected


class TestDeviceType:

    TEST_DATA = [
        (
            """
            device_type=qemux86-64
            """,
            {"device_type": ["qemux86-64"]},
        ),
        (
            """
            device_type=qemux86-64
            device_type=qemux86-65
            """,
            {"device_type": ["qemux86-65"]},
        ),
    ]

    @pytest.fixture
    def file_create_fixture(self, tmpdir):
        d = tmpdir.mkdir("aggregator")

        def create_script(data):
            f = d.join("script")
            f.write(data)
            os.chmod(f, stat.S_IRWXU | stat.S_IRWXO | stat.S_IRWXG)
            return str(f)

        return create_script

    @pytest.mark.parametrize("data, expected", TEST_DATA)
    def test_get_device_type_info(self, data, expected, file_create_fixture):
        fpath = file_create_fixture(data)
        dtype_info = devicetype.get(fpath)
        assert dtype_info == expected

    def test_get_device_type_info_error(self, file_create_fixture):
        """Test that multiple different keys in the device_type file fails."""
        fpath = file_create_fixture("""device_type=foo\nkey=val""")
        dtype_info = devicetype.get(fpath)
        if dtype_info:
            pytest.fail("Multiple different keys in device_type file should fail")


class TestInventory:

    TEST_DATA = [
        (
            """#!/bin/sh
            echo key=val
            echo key2=val
            echo key=val2
            """,
            {"key": ["val", "val2"], "key2": ["val"]},
        )
    ]

    @pytest.fixture
    def file_create_fixture(self, tmpdir):
        d = tmpdir.mkdir("inventoryaggregator")

        def create_script(data):
            f = d.join("script")
            f.write(data)
            os.chmod(f, stat.S_IRWXU | stat.S_IRWXO | stat.S_IRWXG)
            return str(d)

        return create_script

    @pytest.mark.parametrize("data, expected", TEST_DATA)
    def test_inventory_aggregator(self, data, expected, file_create_fixture):
        tpath = file_create_fixture(data)
        assert (
            inventory.aggregate(tpath, device_type_path="", artifact_info_path="")
            == expected
        )


class TestIdentityAggregator:
    @pytest.fixture(autouse=True)
    def set_log_level(self, caplog):
        caplog.set_level(log.INFO)

    @pytest.fixture
    def file_create_fixture(self, tmpdir):
        d = tmpdir.mkdir("inventoryaggregator")

        def create_script(data):
            f = d.join("script")
            f.write(data)
            os.chmod(f, stat.S_IRWXU | stat.S_IRWXO | stat.S_IRWXG)
            return str(f)

        return create_script

    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                """#! /bin/sh
        echo mac=c8:5b:76:fb:c8:75
    """,
                {"mac": ["c8:5b:76:fb:c8:75"]},
            ),
            (
                """#! /bin/sh
                echo foo=bar
                echo bar=baz""",
                {"foo": ["bar"], "bar": ["baz"],},
            ),
        ],
    )
    def test_identity(self, data, expected, file_create_fixture):
        tpath = file_create_fixture(data)
        identity_data = identity.aggregate(tpath)
        assert identity_data
        assert identity_data == expected

    def test_no_identity(self, caplog):
        identity_data = identity.aggregate(path="/i/do/not/exist")
        assert not identity_data
        assert "No identity can be collected" in caplog.text

    def test_identity_not_executable(self, caplog, tmpdir):
        d = tmpdir.mkdir("identity-test")
        f = d.join("mender-device-identity")
        f.write(
            """#! /bin/sh
        echo mac=c8:5b:76:fb:c8:75"""
        )
        identity_data = identity.aggregate(path=f)
        assert not identity_data
        assert "is not executable" in caplog.text
