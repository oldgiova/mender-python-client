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
import os
import os.path

from mender.bootstrap import bootstrap


class TestBootstrap:
    def test_bootstrap(self, tmpdir):
        d = tmpdir.mkdir("test_bootstrap")
        key_path = os.path.join(d, "mender-agent.pem")
        assert bootstrap.now(private_key_path=key_path)
        assert bootstrap.key_already_generated(key_path)

    def test_force_bootstrap(self, tmpdir):
        d = tmpdir.mkdir("test_force_bootstrap")
        key_path = os.path.join(d, "mender-agent.pem")
        assert bootstrap.now(private_key_path=key_path)
        assert bootstrap.now(force_bootstrap=True, private_key_path=key_path)

    def test_key_already_generated(self, tmpdir):
        d = tmpdir.mkdir("test_key_already_generated")
        key_path = os.path.join(d, "mender-agent.pem")
        assert bootstrap.now(private_key_path=key_path)
        assert bootstrap.key_already_generated(key_path)
        os.unlink(key_path)
        assert not bootstrap.key_already_generated(key_path)

    def test_bootstrap_non_existing_directory(self):
        key_path = "/foo/bar"
        key = bootstrap.now(force_bootstrap=False, private_key_path=key_path)
        assert not key
