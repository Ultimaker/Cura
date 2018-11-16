# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import pytest
import json

import unittest.mock
from cura.CuraApplication import CuraApplication

from UM.Version import Version

from plugins.FirmwareUpdateChecker.FirmwareUpdateCheckerJob import FirmwareUpdateCheckerJob
from plugins.FirmwareUpdateChecker.FirmwareUpdateCheckerLookup import FirmwareUpdateCheckerLookup

json_data = \
    {
        "ned":
            {
                "id": 1,
                "name": "ned",
                "check_urls": ["http://urlecho.appspot.com/echo?status=200&body=5.1.2.3"],
                "update_url": "https://ultimaker.com/en/resources/20500-upgrade-firmware",
                "version_parser": "default"
            },
        "olivia":
            {
                "id": 3,
                "name": "olivia",
                "check_urls": ["http://urlecho.appspot.com/echo?status=200&body=4.3.2.1", "https://this-url-clearly-doesnt-exist.net"],
                "update_url": "https://ultimaker.com/en/resources/20500-upgrade-firmware",
                "version_parser": "default"
            },
        "emmerson":
            {
                "id": 5,
                "name": "emmerson",
                "check_urls": ["http://urlecho.appspot.com/echo?status=200&body=0.2.2.2", "http://urlecho.appspot.com/echo?status=200&body=6.7.8.1"],
                "update_url": "https://ultimaker.com/en/resources/20500-upgrade-firmware",
                "version_parser": "default"
            }
    }

def dummyCallback():
    pass

@pytest.mark.parametrize("name, id", [
    ("ned"     , 1),
    ("olivia"  , 3),
    ("emmerson", 5),
])
def test_FirmwareUpdateCheckerLookup(id, name):
    lookup = FirmwareUpdateCheckerLookup(name, json_data.get(name))

    assert lookup.getMachineName() == name
    assert lookup.getMachineId() == id
    assert len(lookup.getCheckUrls()) >= 1
    assert lookup.getRedirectUserUrl() is not None

@pytest.mark.parametrize("name, version", [
    ("ned"     , Version("5.1.2.3")),
    ("olivia"  , Version("4.3.2.1")),
    ("emmerson", Version("6.7.8.1")),
])
def test_FirmwareUpdateCheckerJob_getCurrentVersion(name, version):
    machine_data = json_data.get(name)
    job = FirmwareUpdateCheckerJob(False, name, machine_data, dummyCallback)
    job._headers = {"User-Agent": "Cura-UnitTests 0"}

    assert job.getCurrentVersion() == version
