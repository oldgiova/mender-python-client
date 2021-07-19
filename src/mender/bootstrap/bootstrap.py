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

import logging
import os.path
from typing import Optional

from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKeyWithSerialization

from mender.security import key

log = logging.getLogger(__name__)


def now(
    private_key_path: str, force_bootstrap: bool = False
) -> Optional[RSAPrivateKeyWithSerialization]:
    """Bootstrap the device

    This includes loading the key assymetric key, or generating it if it is not
    present.

    :param force_bootstrap: regenerate the key even if already present
    :param private_key_path: full path (including the filename) to the pem formatted key
    :rtype An instance of `RSAPrivateKey`
    """
    log.info("Bootstrapping the device")
    private_key: Optional[RSAPrivateKeyWithSerialization] = None
    try:
        if not force_bootstrap:
            private_key = key_already_generated(private_key_path)
        if not private_key:
            log.info("Generating a new RSA key pair..")
            if force_bootstrap and os.path.exists(private_key_path):
                os.unlink(private_key_path)
            private_key = key.generate_key()
            key.store_key(private_key, private_key_path)
        log.info("Device bootstrapped successfully")
        return private_key
    except FileNotFoundError:
        log.error(f"The directory in the path: {private_key_path} not found")
        return None


def key_already_generated(
    private_key_path: str,
) -> Optional[RSAPrivateKeyWithSerialization]:
    """Check if a private key already exists in private_key_path

    If the key already exists load and return it

    :param private_key_path: The full path (including the filename) to the key
    :rtype `None` if not found, `RSAPrivateKey` otherwise
    """
    log.debug("Checking if a key already exists for the device")
    try:
        return key.load_key(private_key_path)
    except FileNotFoundError:
        return None
    except (ValueError, TypeError):
        log.error(f"Failed to decode the file: {private_key_path}")
    except UnsupportedAlgorithm:
        log.error("Unsupported key type")
    return None
