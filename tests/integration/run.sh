#! /bin/bash

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
