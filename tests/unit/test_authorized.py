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

from mender.client import authorize
from mender.security import key


@pytest.fixture(name="server_url")
def fixture_server_url(httpserver):
    return httpserver.url_for("")


class TestParameters:
    @pytest.fixture(autouse=True)
    def set_log_level(self, caplog):
        caplog.set_level(log.INFO)

    @pytest.fixture(autouse=True)
    def set_up_expected_request(self, httpserver):
        httpserver.expect_request(
            "/api/devices/v1/authentication/auth_requests", method="post"
        ).respond_with_data("jwttoken", content_type="text/plain")

    def test_all_parameters_are_correct(self, server_url):
        request = authorize.request(
            server_url,
            "this is a tenant tolken",
            {"this is identity": "data"},
            key.generate_key(),
            "this is the server certificate",
        )
        assert request == "jwttoken"

    @pytest.mark.parametrize(
        "test_input,expected",
        [
            ("", "ServerURL not provided, unable to authorize"),
            ("this is an invalid serverURL", "Invalid URL"),
        ],
    )
    def test_server_url(self, caplog, test_input, expected):
        request = authorize.request(
            test_input,
            "this is a tenant token",
            {"this is identity": "data"},
            key.generate_key(),
            "this is the server certificate",
        )
        assert expected in caplog.text
        assert request is None

    def test_no_identity_data(self, caplog, server_url):
        request = authorize.request(
            server_url,
            "this is a tenant token",
            {},
            key.generate_key(),
            "this is the server certificate",
        )
        assert request is None
        assert "Identity data not provided, unable to authorize" in caplog.text

    def test_no_key(self, caplog, server_url):
        request = authorize.request(
            server_url,
            "this is a tenant token",
            {"this is identity": "data"},
            None,
            "this is the server certificate",
        )
        assert request is None
        assert "No private key provided, unable to authorize" in caplog.text


class TestStatusCode:
    def test_staus_codes(self, httpserver, caplog, server_url):
        caplog.set_level(log.ERROR)
        httpserver.expect_request(
            "/api/devices/v1/authentication/auth_requests", method="post"
        ).respond_with_json({"jwt": "token"}, status=201)

        request = authorize.request(
            server_url,
            "this is a tenant tolken",
            {"this is identity": "data"},
            key.generate_key(),
            "this is the server certificate",
        )
        assert "The client failed to authorize with the Mender server." in caplog.text
        assert request is None
