#!/bin/bash
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

set -e

MENDER_VERSION=${MENDER_VERSION:-master}

# Generate docker-compose.testing.yml like integration's run.sh
sed -e '/9000:9000/d' -e '/8080:8080/d' -e '/443:443/d' -e '/80:80/d' -e '/ports:/d' mender_integration/docker-compose.demo.yml > mender_integration/docker-compose.testing.yml
sed -e 's/DOWNLOAD_SPEED/#DOWNLOAD_SPEED/' -i mender_integration/docker-compose.testing.yml
sed -e 's/ALLOWED_HOSTS: .*/ALLOWED_HOSTS: ~./' -i mender_integration/docker-compose.testing.yml

# Workaround bug in master
sed -e 's/mender-master/latest/' -i mender_integration/docker-compose.yml
sed -e 's/master/latest/' -i mender_integration/docker-compose.yml

# Extract file system images from Docker images
mkdir -p output
docker run --rm --privileged --entrypoint /extract_fs -v $PWD/output:/output \
       mendersoftware/mender-client-qemu:${MENDER_VERSION}
mv output/* .
rmdir output
dd if=/dev/urandom of=broken_update.ext4 bs=10M count=5
cp core-image-full-cmdline-qemux86-64.ext4 mender_integration/tests

python3 -m pytest --junit-xml=report.xml -v "$@"
