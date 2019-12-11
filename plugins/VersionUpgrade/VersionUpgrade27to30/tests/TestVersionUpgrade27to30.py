# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import configparser #To parse the resulting config files.
import pytest #To register tests with.

import VersionUpgrade27to30 #The module we're testing.

##  Creates an instance of the upgrader to test with.
@pytest.fixture
def upgrader():
    return VersionUpgrade27to30.VersionUpgrade27to30()

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

test_translate_theme_data = [
    (
        "Original Cura theme",
        """[general]
version = 4
theme = cura
[metadata]
setting_version = 2
""",
        "cura-light"
    ),
    (
        "No theme",
        """[general]
version = 4
[metadata]
setting_version = 2
""",
        None #Indicates that the theme should be absent in the new file.
    )
]

##  Tests whether the theme is properly translated.
@pytest.mark.parametrize("test_name, file_data, new_theme", test_translate_theme_data)
def test_translateTheme(test_name, file_data, new_theme, upgrader):
    #Read old file.
    original_parser = configparser.ConfigParser(interpolation = None)
    original_parser.read_string(file_data)

    #Perform the upgrade.
    _, upgraded_stacks = upgrader.upgradePreferences(file_data, "<string>")
    upgraded_stack = upgraded_stacks[0]
    parser = configparser.ConfigParser(interpolation = None)
    parser.read_string(upgraded_stack)

    #Check whether the theme was properly translated.
    if not new_theme:
        assert "theme" not in parser["general"]
    else:
        assert "theme" in parser["general"]
        assert parser["general"]["theme"] == new_theme