# Copyright 2022 Northern.tech AS
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

import requests

from mender.client.http_requests import MenderRequestsException, http_request

log = logging.getLogger(__name__)


def request(
    server_url: str,
    JWT: str,
    inventory_data: dict,
    server_certificate: str,
    method: str,
) -> bool:
    if not server_url:
        log.error("ServerURL not provided, unable to upload the inventory")
        return False
    if not JWT:
        log.error("No JWT not provided, unable to upload the inventory")
        return False
    if not inventory_data:
        log.info("No inventory_data provided")
        return False
    log.debug(
        f"inventory request: server_url: {server_url}\nJWT: {JWT}\ninventory_data: {inventory_data}"
    )
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + JWT}
    log.debug(f"inventory headers: {headers}")
    raw_data = json.dumps([{"name": k, "value": v} for k, v in inventory_data.items()])
    try:
        request_method = requests.patch if method == "PATCH" else requests.put
        r = http_request(
            request_method,
            server_url + "/api/devices/v1/inventory/device/attributes",
            headers=headers,
            data=raw_data,
            verify=server_certificate or True,
        )

    except MenderRequestsException as e:
        log.error(f"Failed to upload the inventory: {e}")
        return False
    log.debug(f"inventory response: {r}")
    if r.status_code != 200:
        log.error(
            f"Inventory request returned code: {r.status_code}, error: {r.reason}"
        )
        if r.status_code in (400, 500):
            log.error(f"Got inventory response error: {r.json()}")
        return False
    return True
