# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import os.path #To find the test stack files.
import pytest #This module contains automated tests.
import unittest.mock #For the mocking and monkeypatching functionality.

import UM.Settings.ContainerRegistry #To create empty instance containers.
import UM.Settings.ContainerStack #To set the container registry the container stacks use.
from UM.Settings.DefinitionContainer import DefinitionContainer #To check against the class of DefinitionContainer.
import cura.Settings.ExtruderStack #The module we're testing.
from cura.Settings.Exceptions import InvalidOperationError #To check whether the correct exceptions are raised.

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

##  An empty extruder stack to test with.
@pytest.fixture()
def extruder_stack() -> cura.Settings.ExtruderStack.ExtruderStack:
    return cura.Settings.ExtruderStack.ExtruderStack("TestStack")

##  Place-in function for findContainer that finds only containers that start
#   with "some_".
def findSomeContainers(container_id = "*", container_type = None, type = None, category = "*"):
    if container_id.startswith("some_"):
        return UM.Settings.ContainerRegistry._EmptyInstanceContainer(container_id)
    if container_type == DefinitionContainer:
        definition_mock = unittest.mock.MagicMock()
        definition_mock.getId = unittest.mock.MagicMock(return_value = "some_definition") #getId returns some_definition.
        return definition_mock

##  Helper function to read the contents of a container stack in the test
#   stack folder.
#
#   \param filename The name of the file in the "stacks" folder to read from.
#   \return The contents of that file.
def readStack(filename):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "stacks", filename)) as file_handle:
        serialized = file_handle.read()
    return serialized

#############################START OF TEST CASES################################

##  Tests whether adding a container is properly forbidden.
def test_addContainer(extruder_stack):
    with pytest.raises(InvalidOperationError):
        extruder_stack.addContainer(unittest.mock.MagicMock())

@pytest.mark.parametrize("filename,                     definition_id", [
                        ("Left.extruder.cfg",           "empty"),
                        ("ExtruderLegacy.stack.cfg",    "empty"),
                        ("OnlyDefinition.extruder.cfg", "empty"),
                        ("Complete.extruder.cfg",       "some_definition")
])
def test_deserializeDefinition(filename, definition_id, container_registry, extruder_stack):
    serialized = readStack(filename)

    #Mock the loading of the instance containers.
    extruder_stack.findContainer = findSomeContainers
    original_container_registry = UM.Settings.ContainerStack._containerRegistry
    UM.Settings.ContainerStack._containerRegistry = container_registry #Always has all profiles you ask of.

    extruder_stack.deserialize(serialized)
    assert extruder_stack.definition.getId() == definition_id

    #Restore.
    UM.Settings.ContainerStack._containerRegistry = original_container_registry

@pytest.mark.parametrize("filename,                   material_id", [
                        ("Left.extruder.cfg",         "some_instance"),
                        ("ExtruderLegacy.stack.cfg",  "some_instance"),
                        ("OnlyMaterial.extruder.cfg", "some_instance"),
                        ("OnlyDefinition.extruder.cfg", "empty"),
                        ("Complete.extruder.cfg",     "some_material")
])
def test_deserializeMaterial(filename, material_id, container_registry, extruder_stack):
    serialized = readStack(filename)

    #Mock the loading of the instance containers.
    extruder_stack.findContainer = findSomeContainers
    original_container_registry = UM.Settings.ContainerStack._containerRegistry
    UM.Settings.ContainerStack._containerRegistry = container_registry #Always has all profiles you ask of.

    extruder_stack.deserialize(serialized)
    assert extruder_stack.material.getId() == material_id

    #Restore.
    UM.Settings.ContainerStack._containerRegistry = original_container_registry

@pytest.mark.parametrize("filename,                  quality_id", [
                        ("Left.extruder.cfg",        "empty"),
                        ("ExtruderLegacy.stack.cfg", "empty"),
                        ("OnlyQuality.extruder.cfg", "some_instance"),
                        ("Complete.extruder.cfg",    "some_quality")
])
def test_deserializeQuality(filename, quality_id, container_registry, extruder_stack):
    serialized = readStack(filename)

    #Mock the loading of the instance containers.
    extruder_stack.findContainer = findSomeContainers
    original_container_registry = UM.Settings.ContainerStack._containerRegistry
    UM.Settings.ContainerStack._containerRegistry = container_registry #Always has all profiles you ask of.

    extruder_stack.deserialize(serialized)
    assert extruder_stack.quality.getId() == quality_id

    #Restore.
    UM.Settings.ContainerStack._containerRegistry = original_container_registry

@pytest.mark.parametrize("filename,                         quality_changes_id", [
                        ("Left.extruder.cfg",               "empty"),
                        ("ExtruderLegacy.stack.cfg",        "empty"),
                        ("OnlyQualityChanges.extruder.cfg", "some_instance"),
                        ("Complete.extruder.cfg",           "some_quality_changes")
])
def test_deserializeQualityChanges(filename, quality_changes_id, container_registry, extruder_stack):
    serialized = readStack(filename)

    #Mock the loading of the instance containers.
    extruder_stack.findContainer = findSomeContainers
    original_container_registry = UM.Settings.ContainerStack._containerRegistry
    UM.Settings.ContainerStack._containerRegistry = container_registry #Always has all profiles you ask of.

    extruder_stack.deserialize(serialized)
    assert extruder_stack.qualityChanges.getId() == quality_changes_id

    #Restore.
    UM.Settings.ContainerStack._containerRegistry = original_container_registry

@pytest.mark.parametrize("filename,                  user_changes_id", [
                        ("Left.extruder.cfg",        "empty"),
                        ("ExtruderLegacy.stack.cfg", "empty"),
                        ("OnlyUser.extruder.cfg",    "some_instance"),
                        ("Complete.extruder.cfg",    "some_user_changes")
])
def test_deserializeUserChanges(filename, user_changes_id, container_registry, extruder_stack):
    serialized = readStack(filename)

    #Mock the loading of the instance containers.
    extruder_stack.findContainer = findSomeContainers
    original_container_registry = UM.Settings.ContainerStack._containerRegistry
    UM.Settings.ContainerStack._containerRegistry = container_registry #Always has all profiles you ask of.

    extruder_stack.deserialize(serialized)
    assert extruder_stack.userChanges.getId() == user_changes_id

    #Restore.
    UM.Settings.ContainerStack._containerRegistry = original_container_registry

@pytest.mark.parametrize("filename,                  variant_id", [
                        ("Left.extruder.cfg",        "empty"),
                        ("ExtruderLegacy.stack.cfg", "empty"),
                        ("OnlyVariant.extruder.cfg", "some_instance"),
                        ("Complete.extruder.cfg",    "some_variant")
])
def test_deserializeVariant(filename, variant_id, container_registry, extruder_stack):
    serialized = readStack(filename)

    #Mock the loading of the instance containers.
    extruder_stack.findContainer = findSomeContainers
    original_container_registry = UM.Settings.ContainerStack._containerRegistry
    UM.Settings.ContainerStack._containerRegistry = container_registry #Always has all profiles you ask of.

    extruder_stack.deserialize(serialized)
    assert extruder_stack.variant.getId() == variant_id

    #Restore.
    UM.Settings.ContainerStack._containerRegistry = original_container_registry

##  Tests whether inserting a container is properly forbidden.
def test_insertContainer(extruder_stack):
    with pytest.raises(InvalidOperationError):
        extruder_stack.insertContainer(0, unittest.mock.MagicMock())

##  Tests whether removing a container is properly forbidden.
def test_removeContainer(extruder_stack):
    with pytest.raises(InvalidOperationError):
        extruder_stack.removeContainer(unittest.mock.MagicMock())