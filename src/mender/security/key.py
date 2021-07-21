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

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKeyWithSerialization

from mender.security import rsa

log = logging.getLogger(__name__)


def generate_key() -> RSAPrivateKeyWithSerialization:
    log.debug("generate_key: ")
    private_key = rsa.generate_key()
    return private_key


def public_key(private_key: RSAPrivateKeyWithSerialization) -> str:
    log.debug("key: public_key()")
    return rsa.public_key(private_key)


def store_key(private_key: RSAPrivateKeyWithSerialization, path: str):
    log.info(f"Storing key to: {path}")
    rsa.store_key(private_key, path)


def load_key(where: str) -> RSAPrivateKeyWithSerialization:
    log.info(f"Loading key from: {where}")
    return rsa.load_key(where)


def sign(private_key: RSAPrivateKeyWithSerialization, data: str) -> str:
    log.debug("key: Signing the message body")
    return rsa.sign(private_key, data)
