# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser #To check whether the appropriate exceptions are raised.
import pytest #To register tests with.
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import VersionUpgrade26to27 #The module we're testing.

##  Creates an instance of the upgrader to test with.
@pytest.fixture
def upgrader():
    return VersionUpgrade26to27.VersionUpgrade26to27()

test_cfg_version_good_data = [
    {
        "test_name": "Simple",
        "file_data": """[general]
version = 1
""",
        "version": 1000000
    },
    {
        "test_name": "Other Data Around",
        "file_data": """[nonsense]
life = good

[general]
version = 3

[values]
layer_height = 0.12
infill_sparse_density = 42
""",
        "version": 3000000
    },
    {
        "test_name": "Negative Version", #Why not?
        "file_data": """[general]
version = -20
""",
        "version": -20000000
    },
    {
        "test_name": "Setting Version",
        "file_data": """[general]
version = 1
[metadata]
setting_version = 1
""",
        "version": 1000001
    },
    {
        "test_name": "Negative Setting Version",
        "file_data": """[general]
version = 1
[metadata]
setting_version = -3
""",
        "version": 999997
    }
]

##  Tests the technique that gets the version number from CFG files.
#
#   \param data The parametrised data to test with. It contains a test name
#   to debug with, the serialised contents of a CFG file and the correct
#   version number in that CFG file.
#   \param upgrader The instance of the upgrade class to test.
@pytest.mark.parametrize("data", test_cfg_version_good_data)
def test_cfgVersionGood(data, upgrader):
    version = upgrader.getCfgVersion(data["file_data"])
    assert version == data["version"]

test_cfg_version_bad_data = [
    {
        "test_name": "Empty",
        "file_data": "",
        "exception": configparser.Error #Explicitly not specified further which specific error we're getting, because that depends on the implementation of configparser.
    },
    {
        "test_name": "No General",
        "file_data": """[values]
layer_height = 0.1337
""",
        "exception": configparser.Error
    },
    {
        "test_name": "No Version",
        "file_data": """[general]
true = false
""",
        "exception": configparser.Error
    },
    {
        "test_name": "Not a Number",
        "file_data": """[general]
version = not-a-text-version-number
""",
        "exception": ValueError
    },
    {
        "test_name": "Setting Value NaN",
        "file_data": """[general]
version = 4
[metadata]
setting_version = latest_or_something
""",
        "exception": ValueError
    },
    {
        "test_name": "Major-Minor",
        "file_data": """[general]
version = 1.2
""",
        "exception": ValueError
    }
]

##  Tests whether getting a version number from bad CFG files gives an
#   exception.
#
#   \param data The parametrised data to test with. It contains a test name
#   to debug with, the serialised contents of a CFG file and the class of
#   exception it needs to throw.
#   \param upgrader The instance of the upgrader to test.
@pytest.mark.parametrize("data", test_cfg_version_bad_data)
def test_cfgVersionBad(data, upgrader):
    with pytest.raises(data["exception"]):
        upgrader.getCfgVersion(data["file_data"])

test_upgrade_stacks_with_not_supported_data = [
    {
        "test_name": "Global stack with Not Supported quality profile",
        "file_data": """[general]
version = 3
name = Ultimaker 3
id = Ultimaker 3

[metadata]
type = machine

[containers]
0 = Ultimaker 3_user
1 = empty
2 = um3_global_Normal_Quality
3 = empty
4 = empty
5 = empty
6 = ultimaker3
"""
    },
    {
        "test_name": "Extruder stack left with Not Supported quality profile",
        "file_data": """[general]
version = 3
name = Extruder 1
id = ultimaker3_extruder_left #2

[metadata]
position = 0
machine = Ultimaker 3
type = extruder_train

[containers]
0 = ultimaker3_extruder_left #2_user
1 = empty
2 = um3_aa0.4_PVA_Not_Supported_Quality
3 = generic_pva_ultimaker3_AA_0.4
4 = ultimaker3_aa04
5 = ultimaker3_extruder_left #2_settings
6 = ultimaker3_extruder_left
"""
    }
]

##  Tests whether the "Not Supported" quality profiles in the global and extruder stacks are renamed for the 2.7
#   version of preferences.
@pytest.mark.parametrize("data", test_upgrade_stacks_with_not_supported_data)
def test_upgradeStacksWithNotSupportedQuality(data, upgrader):
    # Read old file
    original_parser = configparser.ConfigParser(interpolation = None)
    original_parser.read_string(data["file_data"])

    # Perform the upgrade.
    _, upgraded_stacks = upgrader.upgradeStack(data["file_data"], "<string>")
    upgraded_stack = upgraded_stacks[0]

    # Find whether the not supported profile has been renamed
    parser = configparser.ConfigParser(interpolation = None)
    parser.read_string(upgraded_stack)
    assert("Not_Supported" not in parser.get("containers", "2"))
