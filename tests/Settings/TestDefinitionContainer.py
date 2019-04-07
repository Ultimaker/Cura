# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import pytest #This module contains automated tests.

import UM.Settings.ContainerRegistry #To create empty instance containers.
import UM.Settings.ContainerStack #To set the container registry the container stacks use.
from UM.Settings.DefinitionContainer import DefinitionContainer #To check against the class of DefinitionContainer.



import os
import os.path
import uuid

from UM.Resources import Resources
Resources.addSearchPath(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources")))


machine_filepaths = os.listdir(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "definitions"))
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
    assert isDefinitionValid(definition_container, definition_path, file_name)


def isDefinitionValid(definition_container, path, file_name):
    with open(os.path.join(path, file_name), encoding = "utf-8") as data:
        json = data.read()
        parser, is_valid = definition_container.readAndValidateSerialized(json)
        if not is_valid:
            print("The definition '{0}', has invalid data.".format(file_name))
        metadata = DefinitionContainer.deserializeMetadata(json, "whatever")

        # If the definition defines a platform file, it should be in /resources/meshes/
        if "platform" in metadata[0]:
            assert metadata[0]["platform"] in all_meshes

        if "platform_texture" in metadata[0]:
            assert metadata[0]["platform_texture"] in all_images

        return is_valid
