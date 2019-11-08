# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser # An input for some functions we're testing.
import os.path # To find the integration test .ini files.
import pytest # To register tests with.
import unittest.mock # To mock the application, plug-in and container registry out.
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import UM.Application # To mock the application out.
import UM.PluginRegistry # To mock the plug-in registry out.
import UM.Settings.ContainerRegistry # To mock the container registry out.
import UM.Settings.InstanceContainer # To intercept the serialised data from the read() function.

import LegacyProfileReader as LegacyProfileReaderModule # To get the directory of the module.

@pytest.fixture
def legacy_profile_reader():
    try:
        return LegacyProfileReaderModule.LegacyProfileReader()
    except TypeError:
        return LegacyProfileReaderModule.LegacyProfileReader.LegacyProfileReader()

test_prepareDefaultsData = [
    {
        "defaults":
        {
            "foo": "bar"
        },
        "cheese": "delicious"
    },
    {
        "cat": "fluffy",
        "dog": "floofy"
    }
]

@pytest.mark.parametrize("input", test_prepareDefaultsData)
def test_prepareDefaults(legacy_profile_reader, input):
    output = legacy_profile_reader.prepareDefaults(input)
    if "defaults" in input:
        assert input["defaults"] == output
    else:
        assert output == {}

test_prepareLocalsData = [
    ( # Ordinary case.
        { # Parser data.
            "profile":
            {
                "layer_height": "0.2",
                "infill_density": "30"
            }
        },
        { # Defaults.
            "layer_height": "0.1",
            "infill_density": "20",
            "line_width": "0.4"
        }
    ),
    ( # Empty data.
        { # Parser data.
            "profile":
            {
            }
        },
        { # Defaults.
        }
    ),
    ( # All defaults.
        { # Parser data.
            "profile":
            {
            }
        },
        { # Defaults.
            "foo": "bar",
            "boo": "far"
        }
    ),
    ( # Multiple config sections.
        { # Parser data.
            "some_other_name":
            {
                "foo": "bar"
            },
            "profile":
            {
                "foo": "baz" #Not the same as in some_other_name
            }
        },
        { # Defaults.
            "foo": "bla"
        }
    )
]

@pytest.mark.parametrize("parser_data, defaults", test_prepareLocalsData)
def test_prepareLocals(legacy_profile_reader, parser_data, defaults):
    parser = configparser.ConfigParser()
    parser.read_dict(parser_data)

    output = legacy_profile_reader.prepareLocals(parser, "profile", defaults)

    assert set(defaults.keys()) <= set(output.keys()) # All defaults must be in there.
    assert set(parser_data["profile"]) <= set(output.keys()) # All overwritten values must be in there.
    for key in output:
        if key in parser_data["profile"]:
            assert output[key] == parser_data["profile"][key] # If overwritten, must be the overwritten value.
        else:
            assert output[key] == defaults[key] # Otherwise must be equal to the default.

test_prepareLocalsNoSectionErrorData = [
    ( # Section does not exist.
        { # Parser data.
            "some_other_name":
            {
                "foo": "bar"
            },
        },
        { # Defaults.
            "foo": "baz"
        }
    )
]

##  Test cases where a key error is expected.
@pytest.mark.parametrize("parser_data, defaults", test_prepareLocalsNoSectionErrorData)
def test_prepareLocalsNoSectionError(legacy_profile_reader, parser_data, defaults):
    parser = configparser.ConfigParser()
    parser.read_dict(parser_data)

    with pytest.raises(configparser.NoSectionError):
        legacy_profile_reader.prepareLocals(parser, "profile", defaults)

intercepted_data = ""

@pytest.mark.parametrize("file_name", ["normal_case.ini"])
def test_read(legacy_profile_reader, file_name):
    # Mock out all dependencies. Quite a lot!
    global_stack = unittest.mock.MagicMock()
    global_stack.getProperty = unittest.mock.MagicMock(return_value = 1) # For machine_extruder_count setting.
    def getMetaDataEntry(key, default_value = ""):
        if key == "quality_definition":
            return "mocked_quality_definition"
        if key == "has_machine_quality":
            return "True"
    global_stack.definition.getMetaDataEntry = getMetaDataEntry
    global_stack.definition.getId = unittest.mock.MagicMock(return_value = "mocked_global_definition")
    application = unittest.mock.MagicMock()
    application.getGlobalContainerStack = unittest.mock.MagicMock(return_value = global_stack)
    application_getInstance = unittest.mock.MagicMock(return_value = application)
    container_registry = unittest.mock.MagicMock()
    container_registry_getInstance = unittest.mock.MagicMock(return_value = container_registry)
    container_registry.uniqueName = unittest.mock.MagicMock(return_value = "Imported Legacy Profile")
    container_registry.findDefinitionContainers = unittest.mock.MagicMock(return_value = [global_stack.definition])
    UM.Settings.InstanceContainer.setContainerRegistry(container_registry)
    plugin_registry = unittest.mock.MagicMock()
    plugin_registry_getInstance = unittest.mock.MagicMock(return_value = plugin_registry)
    plugin_registry.getPluginPath = unittest.mock.MagicMock(return_value = os.path.dirname(LegacyProfileReaderModule.__file__))

    # Mock out the resulting InstanceContainer so that we can intercept the data before it's passed through the version upgrader.
    def deserialize(self, data): # Intercepts the serialised data that we'd perform the version upgrade from when deserializing.
        global intercepted_data
        intercepted_data = data

        parser = configparser.ConfigParser()
        parser.read_string(data)
        self._metadata["position"] = parser["metadata"]["position"]
    def duplicate(self, new_id, new_name):
        self._metadata["id"] = new_id
        self._metadata["name"] = new_name
        return self

    with unittest.mock.patch.object(UM.Application.Application, "getInstance", application_getInstance):
        with unittest.mock.patch.object(UM.Settings.ContainerRegistry.ContainerRegistry, "getInstance", container_registry_getInstance):
            with unittest.mock.patch.object(UM.PluginRegistry.PluginRegistry, "getInstance", plugin_registry_getInstance):
                with unittest.mock.patch.object(UM.Settings.InstanceContainer.InstanceContainer, "deserialize", deserialize):
                    with unittest.mock.patch.object(UM.Settings.InstanceContainer.InstanceContainer, "duplicate", duplicate):
                        result = legacy_profile_reader.read(os.path.join(os.path.dirname(__file__), file_name))

    assert len(result) == 1

    # Let's see what's inside the actual output file that we generated.
    parser = configparser.ConfigParser()
    parser.read_string(intercepted_data)
    assert parser["general"]["definition"] == "mocked_quality_definition"
    assert parser["general"]["version"] == "4" # Yes, before we upgraded.
    assert parser["general"]["name"] == "Imported Legacy Profile" # Because we overwrote uniqueName.
    assert parser["metadata"]["type"] == "quality_changes"
    assert parser["metadata"]["quality_type"] == "normal"
    assert parser["metadata"]["position"] == "0"
    assert parser["metadata"]["setting_version"] == "5" # Yes, before we upgraded.