# Copyright (c) 2018 Ultimaker B.V.
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


filepaths = os.listdir(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "definitions"))

#############################START OF TEST CASES################################

@pytest.fixture
def definition_container():
    uid = str(uuid.uuid4())
    result = UM.Settings.DefinitionContainer.DefinitionContainer(uid)
    assert result.getId() == uid
    return result

##  Tests all definition containers

@pytest.mark.parametrize("file_name", filepaths)
def test_validateDefintionContainer(file_name, definition_container):

    definition_path = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "definitions")

    if file_name == "fdmprinter.def.json" or file_name == "fdmextruder.def.json":
        return  # Stop checking, these are root files.

    with open(os.path.join(definition_path, file_name), encoding = "utf-8") as data:

        json = data.read()
        parser, is_valid = definition_container.readAndValidateSerialized(json)
        if not is_valid:
            print("The definition '{0}', has invalid data.".format(file_name))

        assert is_valid
