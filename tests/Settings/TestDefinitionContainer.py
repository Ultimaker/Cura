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


#############################START OF TEST CASES################################

@pytest.fixture
def definition_container():
    uid = str(uuid.uuid4())
    result = UM.Settings.DefinitionContainer.DefinitionContainer(uid)
    assert result.getId() == uid
    return result

##  Tests all definition containers
def test_validateDefintionContainer(definition_container):

    definition_path = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "definitions")
    all_definition_files = os.listdir(definition_path)

    for file_name in all_definition_files:

        if file_name == "fdmprinter.def.json" or file_name == "fdmextruder.def.json":
            continue

        with open(os.path.join(definition_path, file_name), encoding = "utf-8") as data:

            json = data.read()
            parser, is_valid = definition_container.readAndValidateSerialized(json)
            if(not is_valid):
                print("The File Name: '{0}', has invalid data ".format(file_name))
            # To see the detailed data from log, comment the assert check and execute the test again. It will print invalid data
            assert is_valid == True