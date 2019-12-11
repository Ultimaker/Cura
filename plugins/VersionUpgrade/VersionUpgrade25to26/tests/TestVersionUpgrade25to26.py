# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import configparser #To check whether the appropriate exceptions are raised.
import pytest #To register tests with.

import VersionUpgrade25to26 #The module we're testing.

##  Creates an instance of the upgrader to test with.
@pytest.fixture
def upgrader():
    return VersionUpgrade25to26.VersionUpgrade25to26()

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

test_upgrade_preferences_removed_settings_data = [
    {
        "test_name": "Removed Setting",
        "file_data": """[general]
visible_settings = baby;you;know;how;I;like;to;start_layers_at_same_position
""",
    },
    {
        "test_name": "No Removed Setting",
        "file_data": """[general]
visible_settings = baby;you;now;how;I;like;to;eat;chocolate;muffins
"""
},
    {
        "test_name": "No Visible Settings Key",
        "file_data": """[general]
cura = cool
"""
    },
    {
        "test_name": "No General Category",
        "file_data": """[foos]
foo = bar
"""
    }
]

##  Tests whether the settings that should be removed are removed for the 2.6
#   version of preferences.
@pytest.mark.parametrize("data", test_upgrade_preferences_removed_settings_data)
def test_upgradePreferencesRemovedSettings(data, upgrader):
    #Get the settings from the original file.
    original_parser = configparser.ConfigParser(interpolation = None)
    original_parser.read_string(data["file_data"])
    settings = set()
    if original_parser.has_section("general") and "visible_settings" in original_parser["general"]:
        settings = set(original_parser["general"]["visible_settings"].split(";"))

    #Perform the upgrade.
    _, upgraded_preferences = upgrader.upgradePreferences(data["file_data"], "<string>")
    upgraded_preferences = upgraded_preferences[0]

    #Find whether the removed setting is removed from the file now.
    settings -= VersionUpgrade25to26._removed_settings
    parser = configparser.ConfigParser(interpolation = None)
    parser.read_string(upgraded_preferences)
    assert (parser.has_section("general") and "visible_settings" in parser["general"]) == (len(settings) > 0) #If there are settings, there must also be a preference.
    if settings:
        assert settings == set(parser["general"]["visible_settings"].split(";"))

test_upgrade_instance_container_removed_settings_data = [
    {
        "test_name": "Removed Setting",
        "file_data": """[values]
layer_height = 0.1337
start_layers_at_same_position = True
"""
    },
    {
        "test_name": "No Removed Setting",
        "file_data": """[values]
oceans_number = 11
"""
    },
    {
        "test_name": "No Values Category",
        "file_data": """[general]
type = instance_container
"""
    }
]

##  Tests whether the settings that should be removed are removed for the 2.6
#   version of instance containers.
@pytest.mark.parametrize("data", test_upgrade_instance_container_removed_settings_data)
def test_upgradeInstanceContainerRemovedSettings(data, upgrader):
    #Get the settings from the original file.
    original_parser = configparser.ConfigParser(interpolation = None)
    original_parser.read_string(data["file_data"])
    settings = set()
    if original_parser.has_section("values"):
        settings = set(original_parser["values"])

    #Perform the upgrade.
    _, upgraded_container = upgrader.upgradeInstanceContainer(data["file_data"], "<string>")
    upgraded_container = upgraded_container[0]

    #Find whether the forbidden setting is still in the container.
    settings -= VersionUpgrade25to26._removed_settings
    parser = configparser.ConfigParser(interpolation = None)
    parser.read_string(upgraded_container)
    assert parser.has_section("values") == (len(settings) > 0) #If there are settings, there must also be the values category.
    if settings:
        assert settings == set(parser["values"])
