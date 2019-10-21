# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import json  # To check files for unnecessarily overridden properties.
import os
import os.path
import pytest #This module contains automated tests.
from typing import Any, Dict
import uuid

import UM.Settings.ContainerRegistry #To create empty instance containers.
import UM.Settings.ContainerStack #To set the container registry the container stacks use.
from UM.Settings.DefinitionContainer import DefinitionContainer #To check against the class of DefinitionContainer.

from UM.Resources import Resources
Resources.addSearchPath(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources")))


machine_filepaths = sorted(os.listdir(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "definitions")))
all_meshes = os.listdir(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "meshes"))
all_images = os.listdir(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "images"))

@pytest.fixture
def definition_container():
    uid = str(uuid.uuid4())
    result = UM.Settings.DefinitionContainer.DefinitionContainer(uid)
    assert result.getId() == uid
    return result


##  Tests all definition containers
@pytest.mark.parametrize("file_name", machine_filepaths)
def test_validateMachineDefinitionContainer(file_name, definition_container):
    if file_name == "fdmprinter.def.json" or file_name == "fdmextruder.def.json":
        return  # Stop checking, these are root files.

    definition_path = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "definitions")
    assertIsDefinitionValid(definition_container, definition_path, file_name)


def assertIsDefinitionValid(definition_container, path, file_name):
    with open(os.path.join(path, file_name), encoding = "utf-8") as data:
        json = data.read()
        parser, is_valid = definition_container.readAndValidateSerialized(json)
        assert is_valid #The definition has invalid JSON structure.
        metadata = DefinitionContainer.deserializeMetadata(json, "whatever")

        # If the definition defines a platform file, it should be in /resources/meshes/
        if "platform" in metadata[0]:
            assert metadata[0]["platform"] in all_meshes

        if "platform_texture" in metadata[0]:
            assert metadata[0]["platform_texture"] in all_images

##  Tests whether setting values are not being hidden by parent containers.
#
#   When a definition container defines a "default_value" but inherits from a
#   definition that defines a "value", the "default_value" is ineffective. This
#   test fails on those things.
@pytest.mark.parametrize("file_name", machine_filepaths)
def test_validateOverridingDefaultValue(file_name):
    definition_path = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "definitions", file_name)
    with open(definition_path, encoding = "utf-8") as f:
        doc = json.load(f)

    if "inherits" not in doc:
        return  # We only want to check for documents where the inheritance overrides the children. If there's no inheritance, this can't happen so it's fine.
    if "overrides" not in doc:
        return  # No settings are being overridden. No need to check anything.
    parent_settings = getInheritedSettings(doc["inherits"])
    for key, val in doc["overrides"].items():
        if "value" in parent_settings[key]:
            assert "default_value" not in val, "Unnecessary default_value for {key} in {file_name}".format(key = key, file_name = file_name)  # If there is a value in the parent settings, then the default_value is not effective.

def getInheritedSettings(definition_id: str) -> Dict[str, Any]:
    definition_path = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "definitions", definition_id + ".def.json")
    with open(definition_path, encoding = "utf-8") as f:
        doc = json.load(f)
    result = {}

    if "inherits" in doc:  # Recursive inheritance.
        result.update(getInheritedSettings(doc["inherits"]))
    if "settings" in doc:
        result.update(flattenSettings(doc["settings"]))
    if "overrides" in doc:
        result = merge_dicts(result, doc["overrides"])

    return result

def flattenSettings(settings) -> Dict[str, Any]:
    result = {}
    for entry, contents in settings.items():
        if "children" in contents:
            result.update(flattenSettings(contents["children"]))
            del contents["children"]
        result[entry] = contents
    return result

def merge_dicts(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    result = {}
    result.update(base)
    for key, val in overrides.items():
        if key not in result:
            result[key] = val
            continue

        if isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = merge_dicts(result[key], val)
        else:
            result[key] = val
    return result