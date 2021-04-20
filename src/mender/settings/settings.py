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
import os.path

SLEEP_INTERVAL = 60


class Path:
    """Hold all the path configuration for the client

    Usage::

      >>> import mender.settings.settings as settings
      >>> private_key_location = settings.PATHS.key


    """

    def __init__(self, data_store="/var/lib/mender"):
        self.conf = "/etc/mender"
        self.data_store = data_store
        self.data_dir = "/usr/share/mender"
        self.key_filename = "mender-agent.pem"

        self.local_conf = os.path.join(self.conf, "mender.conf")
        self.global_conf = os.path.join(self.data_store, "mender.conf")

        self.identity_scripts = os.path.join(
            self.data_dir, "identity", "mender-device-identity"
        )
        self.inventory_scripts = os.path.join(self.data_dir, "inventory")
        self.key = os.path.join(self.data_store, self.key_filename)
        self.key_path = self.data_store

        self.artifact_info = os.path.join(self.conf, "artifact_info")
        self.device_type = os.path.join(self.data_store, "device_type")

        self.artifact_download = self.data_store

        self.deployment_log = self.data_store

        self.lockfile_path = self.data_store + "/update.lock"

        self.install_script = "/usr/share/mender/install"

        self.remote_terminal_conf = os.path.join(self.conf, "mender-connect.conf")


# Global singleton
PATHS = Path()
