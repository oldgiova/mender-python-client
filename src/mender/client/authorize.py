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
from typing import Optional

import requests
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKeyWithSerialization

from mender.client.http_requests import MenderRequestsException, http_request
from mender.security import key

log = logging.getLogger(__name__)


JWTToken = str


def request(
    server_url: str,
    tenant_token: str,
    id_data: dict,
    private_key: RSAPrivateKeyWithSerialization,
    server_certificate: str,
) -> Optional[JWTToken]:
    return authorize(server_url, id_data, tenant_token, private_key, server_certificate)


def authorize(
    server_url: str,
    id_data: dict,
    tenant_token: str,
    private_key: RSAPrivateKeyWithSerialization,
    server_certificate: str,
) -> Optional[JWTToken]:
    if not server_url:
        log.error("ServerURL not provided, unable to authorize")
        return None
    if not id_data:
        log.error("Identity data not provided, unable to authorize")
        return None
    if not private_key:
        log.error("No private key provided, unable to authorize")
        return None

    id_data_json = json.dumps(id_data)
    public_key = key.public_key(private_key)
    body = {"id_data": id_data_json, "pubkey": public_key, "tenant_token": tenant_token}
    raw_data = json.dumps(body)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-MEN-Signature": key.sign(private_key, raw_data),
        "Authorization": "API_KEY",
    }
    try:
        if server_certificate:
            log.info(
                f"Trying to authorize with the server-certificate: {server_certificate}"
            )
        r = http_request(
            requests.post,
            server_url + "/api/devices/v1/authentication/auth_requests",
            data=raw_data,
            headers=headers,
            verify=server_certificate or True,
        )
    except MenderRequestsException as e:
        log.error("Failed to post to the authentication endpoint")
        log.error(e)
        return None
    log.debug(f"response: {r.status_code}")
    if r.status_code == 200:
        log.info("The client successfully authenticated with the Mender server")
        return r.text
    log.error("The client failed to authorize with the Mender server.")
    log.error(f"Error {r.reason}. code: {r.status_code}")
    if r.status_code in (400, 401, 500):
        log.error(f"Error: {r.json()}")
    return None
