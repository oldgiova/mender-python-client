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

import time

import pytest

import mender_integration.tests.conftest as cf

cf.machine_name = "qemux86-64"

from mender_integration.tests.common_setup import standard_setup_one_client_bootstrapped
from mender_integration.tests.MenderAPI import deploy, devauth
from mender_integration.tests.tests.common_update import (
    update_image,
    update_image_failed,
    common_update_procedure,
)


def test_update_successful(standard_setup_one_client_bootstrapped):
    """Test that the Python API client successfully installs a new update

    This is done through running it in an image, with the original mender-client
    installed, using it as the sub-updater agent, and letting it install the
    Artifact through:

    mender install <path-to-artifact>

    In the sub-updater install script.

    """

    update_image(
        standard_setup_one_client_bootstrapped.device,
        standard_setup_one_client_bootstrapped.get_virtual_network_host_ip(),
        install_image="core-image-full-cmdline-%s.ext4" % "qemux86-64",
    )


def test_update_error(standard_setup_one_client_bootstrapped):
    """Test that the client behaves as expected upon failure.

    This means that the deployment log from both the client itself, and the
    sub-updater should be uploaded to the Mender server upon an error.

    """

    device = standard_setup_one_client_bootstrapped.device
    update_image_failed(
        standard_setup_one_client_bootstrapped.device,
        standard_setup_one_client_bootstrapped.get_virtual_network_host_ip(),
        install_image="broken_update.ext4",
        expected_log_message="An update was seemingly in progress, and failed",
        expected_number_of_reboots=1,
    )


from mender_integration.tests.MenderAPI import devauth, inv


def extract_inventory():
    """Get the device inventory"""
    for _ in range(10):
        inv_json = inv.get_devices()
        assert len(inv_json) > 0
        auth_json = devauth.get_devices()
        auth_ids = [device["id"] for device in auth_json]
        for device in inv_json:
            assert device["id"] in auth_ids
            attrs = device["attributes"]
            attrs = [{"name": x.get("name"), "value": x.get("value")} for x in attrs]
            if len(attrs) > 3:
                return attrs
            else:
                time.sleep(20)
                continue
    return None


def test_inventory(standard_setup_one_client_bootstrapped):
    """
    Test that device reports inventory after having bootstrapped and performed
    a rootfs update.

    After the update the inventory should differ.

    """

    inventory_pre_update = extract_inventory()
    assert inventory_pre_update
    update_image(
        standard_setup_one_client_bootstrapped.device,
        standard_setup_one_client_bootstrapped.get_virtual_network_host_ip(),
        install_image="core-image-full-cmdline-%s.ext4" % "qemux86-64",
    )
    inventory_post_update = extract_inventory()
    assert inventory_post_update
    assert inventory_pre_update != inventory_post_update


def test_missing_install_script(standard_setup_one_client_bootstrapped):
    """Test that the client uploads the deployment log upon a missing install script"""

    device = standard_setup_one_client_bootstrapped.device
    device.run("rm /usr/share/mender/install")

    deployment_id, _ = common_update_procedure("broken_update.ext4", make_artifact=None)

    deploy.check_expected_statistics(deployment_id, "failure", 1)

    for d in devauth.get_devices():
        assert expected_log_message in deploy.get_logs(d["id"], deployment_id)
