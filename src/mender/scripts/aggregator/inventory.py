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
from typing import List

from mender.scripts import artifactinfo, devicetype
from mender.scripts.aggregator.aggregator import ScriptKeyValueAggregator


def aggregate(script_path: str, device_type_path: str, artifact_info_path: str) -> dict:
    """Runs all the inventory scripts in 'path', and parses the 'key=value' pairs
    into a data-structure ready for passing it on to the Mender server"""
    log.info(f"Aggregating inventory data from {script_path}")
    keyvals: dict = {}
    for inventory_script in inventory_scripts(script_path):
        keyvals.update(inventory_script.run())
    device_type = devicetype.get(device_type_path)
    log.info(f"Found the device type: {device_type}")
    if device_type:
        keyvals.update(device_type)
    artifact_name = artifactinfo.get(artifact_info_path)
    log.info(f"Found the artifact_name: {artifact_name}")
    if artifact_name:
        keyvals.update(artifact_name)
    return keyvals


def inventory_scripts(inventory_dir: str) -> List[ScriptKeyValueAggregator]:
    """Returns all the inventory scripts in a directory.

    An inventory scripts needs to:

    * Be executable
    * Be located in '/usr/share/mender/inventory'
    """
    scripts = []
    for f in os.listdir(inventory_dir):
        filepath = os.path.join(inventory_dir, f)
        if os.path.isfile(filepath) and os.access(filepath, os.X_OK):
            scripts.append(ScriptKeyValueAggregator(filepath))
    return scripts
