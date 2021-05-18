SUMMARY = "A Python implementation of the Mender client API interface"
HOMEPAGE = "https://github.com/mendersoftware/mender-python-client"

FILES_${PN}_append = " ${bindir}mender-sub-updater \
         /var/lib/mender/install \
         ${systemd_unitdir}/system/mender-sub-updater.service \
         ${systemd_unitdir}/system/mender-python-client.service"

LICENSE = "Apache-2.0"
LIC_FILES_CHKSUM = "file://LICENSE;md5=dcac2e5bf81a6fe99b034aaaaf1b2019"

MENDER_PYTHON_CLIENT_BUILD_BRANCH ?= "master"

SRC_URI = "git://github.com/mendersoftware/mender-python-client;protocol=https;branch=${MENDER_PYTHON_CLIENT_BUILD_BRANCH}"

SRC_URI_append = " \
    file://mender-sub-updater \
    file://mender-sub-updater.service"

PV = "0.0.1+git${SRCPV}"
SRCREV = "${AUTOREV}"

S = "${WORKDIR}/git"

inherit setuptools3 systemd

SYSTEMD_SERVICE_${PN} = "mender-sub-updater.service \
                         mender-python-client.service"
SYSTEMD_AUTO_ENABLE = "enable"

DEPENDS += " mender-client"

RDEPENDS_${PN} += "python3-core \
                   python3-modules \
                   python3-cryptography \
                   python3-requests \
                   python3-websockets \
                   python3-msgpack \
                   bash"

do_install_append () {

    install -d ${D}${systemd_unitdir}/system
    install -m 644 ${S}/support/mender-python-client.service ${D}${systemd_unitdir}/system

    install -d ${D}${bindir}
    install -m 0755 ${WORKDIR}/mender-sub-updater ${D}${bindir}/mender-sub-updater
    install -d ${D}${systemd_unitdir}/system
    bbwarn Installing the mender-sub-updater.service file
    install -m 0644 ${WORKDIR}/mender-sub-updater.service ${D}${systemd_unitdir}/system
}

