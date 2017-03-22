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

##  Helper function to read the contents of a container stack in the test
#   stack folder.
#
#   \param filename The name of the file in the "stacks" folder to read from.
#   \return The contents of that file.
def readStack(filename):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "stacks", filename)) as file_handle:
        serialized = file_handle.read()
    return serialized

##  Tests whether the user changes are being read properly from a global stack.
@pytest.mark.parametrize("filename,                 user_changes_id", [
                        ("Global.global.cfg",       "empty"),
                        ("Global.stack.cfg",        "empty"),
                        ("MachineLegacy.stack.cfg", "empty"),
                        ("OnlyUser.global.cfg",     "some_instance"), #This one does have a user profile.
                        ("Complete.global.cfg",     "some_user_changes")
])
def test_deserializeUserChanges(filename, user_changes_id, container_registry):
    serialized = readStack(filename)
    stack = cura.Settings.GlobalStack.GlobalStack("TestStack")

    #Mock the loading of the instance containers.
    stack.findContainer = findSomeContainers
    UM.Settings.ContainerStack._containerRegistry = container_registry #Always has all profiles you ask of.

    stack.deserialize(serialized)

    assert stack.userChanges.getId() == user_changes_id

##  Tests whether the quality changes are being read properly from a global
#   stack.
@pytest.mark.parametrize("filename,                       quality_changes_id", [
                        ("Global.global.cfg",             "empty"),
                        ("Global.stack.cfg",              "empty"),
                        ("MachineLegacy.stack.cfg",       "empty"),
                        ("OnlyQualityChanges.global.cfg", "some_instance"),
                        ("Complete.global.cfg",           "some_quality_changes")
])
def test_deserializeQualityChanges(filename, quality_changes_id, container_registry):
    serialized = readStack(filename)
    stack = cura.Settings.GlobalStack.GlobalStack("TestStack")

    #Mock the loading of the instance containers.
    stack.findContainer = findSomeContainers
    UM.Settings.ContainerStack._containerRegistry = container_registry #Always has all the profiles you ask of.

    stack.deserialize(serialized)

    assert stack.qualityChanges.getId() == quality_changes_id

##  Tests whether the quality profile is being read properly from a global
#   stack.
@pytest.mark.parametrize("filename,                 quality_id", [
                        ("Global.global.cfg",       "empty"),
                        ("Global.stack.cfg",        "empty"),
                        ("MachineLegacy.stack.cfg", "empty"),
                        ("OnlyQuality.global.cfg",  "some_instance"),
                        ("Complete.global.cfg",     "some_quality")
])
def test_deserializeQuality(filename, quality_id, container_registry):
    serialized = readStack(filename)
    stack = cura.Settings.GlobalStack.GlobalStack("TestStack")

    #Mock the loading of the instance containers.
    stack.findContainer = findSomeContainers
    UM.Settings.ContainerStack._containerRegistry = container_registry #Always has all the profiles you ask of.

    stack.deserialize(serialized)

    assert stack.quality.getId() == quality_id

##  Tests whether the material profile is being read properly from a global
#   stack.
@pytest.mark.parametrize("filename,                   material_id", [
                        ("Global.global.cfg",         "some_instance"),
                        ("Global.stack.cfg",          "some_instance"),
                        ("MachineLegacy.stack.cfg",   "some_instance"),
                        ("OnlyDefinition.global.cfg", "empty"),
                        ("OnlyMaterial.global.cfg",   "some_instance"),
                        ("Complete.global.cfg",       "some_material")
])
def test_deserializeMaterial(filename, material_id, container_registry):
    serialized = readStack(filename)
    stack = cura.Settings.GlobalStack.GlobalStack("TestStack")

    #Mock the loading of the instance containers.
    stack.findContainer = findSomeContainers
    UM.Settings.ContainerStack._containerRegistry = container_registry #Always has all the profiles you ask of.

    stack.deserialize(serialized)

    assert stack.material.getId() == material_id