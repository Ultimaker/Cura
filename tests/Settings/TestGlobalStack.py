# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import os.path #To find the test files.
import pytest #This module contains unit tests.
import unittest.mock #To monkeypatch some mocks in place of dependencies.

import cura.Settings.GlobalStack #The module we're testing.
from UM.Settings.DefinitionContainer import DefinitionContainer #To test against the class DefinitionContainer.
import UM.Settings.ContainerRegistry
import UM.Settings.ContainerStack

##  Fake container registry that always provides all containers you ask of.
@pytest.fixture()
def container_registry():
    registry = unittest.mock.MagicMock()
    def findContainers(id = None):
        if not id:
            return [UM.Settings.ContainerRegistry._EmptyInstanceContainer("test_container")]
        else:
            return [UM.Settings.ContainerRegistry._EmptyInstanceContainer(id)]
    registry.findContainers = findContainers
    return registry

##  Place-in function for findContainer that finds only containers that start
#   with "some_".
def findSomeContainers(container_id = "*", container_type = None, type = None, category = "*"):
    if container_id.startswith("some_"):
        return UM.Settings.ContainerRegistry._EmptyInstanceContainer(container_id)
    if container_type == DefinitionContainer:
        return unittest.mock.MagicMock()

##  Tests whether the user changes are being read properly from a global stack.
@pytest.mark.parametrize("filename, user_changes_id", [
                        ("Global.global.cfg", "empty"),
                        ("Global.stack.cfg", "empty"),
                        ("MachineLegacy.stack.cfg", "empty"),
                        ("OnlyUser.global.cfg", "some_instance"), #This one does have a user profile.
                        ("Complete.global.cfg", "some_user_changes")
])
def test_deserializeUserChanges(filename, user_changes_id, container_registry):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "stacks", filename)) as file_handle:
        serialized = file_handle.read()
    stack = cura.Settings.GlobalStack.GlobalStack("TestStack")

    #Mock the loading of the instances.
    stack.findContainer = findSomeContainers
    UM.Settings.ContainerStack._containerRegistry = container_registry #Always has all profiles you ask of.

    stack.deserialize(serialized)

    assert stack.userChanges.getId() == user_changes_id