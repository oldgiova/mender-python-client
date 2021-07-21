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

import pytest

from mender.client import inventory


@pytest.fixture(name="server_url")
def fixture_server_url(httpserver):
    return httpserver.url_for("")


class TestParameters:
    @pytest.fixture(autouse=True)
    def set_log_level(self, caplog):
        caplog.set_level(log.DEBUG)

    @pytest.fixture(autouse=True)
    def set_up_expected_request(self, httpserver):
        httpserver.expect_request(
            "/api/devices/v1/inventory/device/attributes"
        ).respond_with_json({"foo": "bar"}, content_type="text/plain")

    @pytest.mark.parametrize(
        "method", [("PUT"), ("PATCH"),],
    )
    def test_all_parameters_are_correct(self, server_url, caplog, method):
        inventory.request(
            server_url,
            "this is the JWT",
            {"this is inventory": "data"},
            "this is the server certificate",
            method,
        )
        assert "inventory response" in caplog.text

    @pytest.mark.parametrize(
        "method", [("PUT"), ("PATCH"),],
    )
    @pytest.mark.parametrize(
        "test_input,expected",
        [
            ("", "ServerURL not provided, unable to upload the inventory"),
            ("this is an invalid serverURL", "Invalid URL"),
        ],
    )
    def test_server_url(self, caplog, test_input, expected, method):
        inventory.request(
            test_input,
            "this is the JWT",
            {"this is inventory": "data"},
            "this is the server certificate",
            method,
        )
        assert expected in caplog.text

    @pytest.mark.parametrize(
        "method", [("PUT"), ("PATCH"),],
    )
    def test_no_jwt(self, caplog, server_url, method):
        inventory.request(
            server_url,
            "",
            {"this is inventory": "data"},
            "this is the server certificate",
            method,
        )
        assert "No JWT not provided, unable to upload the inventory" in caplog.text

    @pytest.mark.parametrize(
        "method", [("PUT"), ("PATCH"),],
    )
    def test_no_inventory_data(self, caplog, server_url, method):
        inventory.request(
            server_url, "this is the JWT", {}, "this is the server certificate", method,
        )
        assert "No inventory_data provided" in caplog.text

    @pytest.mark.parametrize(
        "method", [("PUT"), ("PATCH"),],
    )
    @pytest.mark.parametrize(
        "status_code,expected_log,return_value",
        [
            (200, "inventory response", True),
            (204, "Inventory request returned code", False),
            (400, "Got inventory response error", False),
        ],
    )
    def test_staus_codes(
        self, httpserver, caplog, method, status_code, expected_log, return_value
    ):
        httpserver.expect_request(
            "/testStatusCodes/api/devices/v1/inventory/device/attributes"
        ).respond_with_json({"foo": "bar"}, status=status_code)
        r = inventory.request(
            httpserver.url_for("testStatusCodes"),
            "this is the JWT",
            {"this is inventory": "data"},
            "this is the server certificate",
            method,
        )
        assert r == return_value
        assert expected_log in caplog.text
