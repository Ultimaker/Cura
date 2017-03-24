# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import os.path #To find the test stack files.
import pytest #This module contains automated tests.
import unittest.mock #For the mocking and monkeypatching functionality.

import UM.Settings.ContainerRegistry #To create empty instance containers.
import UM.Settings.ContainerStack #To set the container registry the container stacks use.
from UM.Settings.DefinitionContainer import DefinitionContainer #To check against the class of DefinitionContainer.
from UM.Settings.InstanceContainer import InstanceContainer #To check against the class of InstanceContainer.
import cura.Settings.ExtruderStack #The module we're testing.
from cura.Settings.Exceptions import InvalidContainerError, InvalidOperationError #To check whether the correct exceptions are raised.

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

class DefinitionContainerSubClass(DefinitionContainer):
    def __init__(self):
        super().__init__(container_id = "SubDefinitionContainer")

class InstanceContainerSubClass(InstanceContainer):
    def __init__(self):
        super().__init__(container_id = "SubInstanceContainer")

#############################START OF TEST CASES################################

##  Tests whether adding a container is properly forbidden.
def test_addContainer(extruder_stack):
    with pytest.raises(InvalidOperationError):
        extruder_stack.addContainer(unittest.mock.MagicMock())

##  Tests whether the container types are properly enforced on the stack.
#
#   When setting a field to have a different type of stack than intended, we
#   should get an exception.
@pytest.mark.parametrize("definition_container, instance_container", [
    (DefinitionContainer(container_id = "TestDefinitionContainer"), InstanceContainer(container_id = "TestInstanceContainer")),
    (DefinitionContainerSubClass(), InstanceContainerSubClass())
])
def test_constrainContainerTypes(definition_container, instance_container, extruder_stack):
    with pytest.raises(InvalidContainerError): #Putting a definition container in the user changes is not allowed.
        extruder_stack.userChanges = definition_container
    extruder_stack.userChanges = instance_container #Putting an instance container in the user changes is allowed.
    with pytest.raises(InvalidContainerError):
        extruder_stack.qualityChanges = definition_container
    extruder_stack.qualityChanges = instance_container
    with pytest.raises(InvalidContainerError):
        extruder_stack.quality = definition_container
    extruder_stack.quality = instance_container
    with pytest.raises(InvalidContainerError):
        extruder_stack.material = definition_container
    extruder_stack.material = instance_container
    with pytest.raises(InvalidContainerError):
        extruder_stack.variant = definition_container
    extruder_stack.variant = instance_container
    with pytest.raises(InvalidContainerError): #Putting an instance container in the definition is not allowed.
        extruder_stack.definition = instance_container
    extruder_stack.definition = definition_container #Putting a definition container in the definition is allowed.

##  Tests whether definitions are being read properly from an extruder stack.
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

##  Tests whether materials are being read properly from an extruder stack.
@pytest.mark.parametrize("filename,                     material_id", [
                        ("Left.extruder.cfg",           "some_instance"),
                        ("ExtruderLegacy.stack.cfg",    "some_instance"),
                        ("OnlyMaterial.extruder.cfg",   "some_instance"),
                        ("OnlyDefinition.extruder.cfg", "empty"),
                        ("Complete.extruder.cfg",       "some_material")
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

##  Tests that when an extruder is loaded with an unknown instance, it raises an
#   exception.
def test_deserializeMissingContainer(extruder_stack):
    serialized = readStack("Left.extruder.cfg")
    with pytest.raises(Exception):
        extruder_stack.deserialize(serialized)
    try:
        extruder_stack.deserialize(serialized)
    except Exception as e:
        #Must be exactly Exception, not one of its subclasses, since that is what gets raised when a stack has an unknown container.
        #That's why we can't use pytest.raises.
        assert type(e) == Exception

##  Tests whether qualities are being read properly from an extruder stack.
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

##  Tests whether quality changes are being read properly from an extruder
#   stack.
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

##  Tests whether user changes are being read properly from an extruder stack.
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

##  Tests whether variants are being read properly from an extruder stack.
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

##  Tests whether getProperty properly applies the stack-like behaviour on its
#   containers.
def test_getPropertyFallThrough(extruder_stack):
    #A few instance container mocks to put in the stack.
    layer_height_5 = unittest.mock.MagicMock() #Sets layer height to 5.
    layer_height_5.getProperty = lambda key, property: 5 if (key == "layer_height" and property == "value") else None
    layer_height_5.hasProperty = lambda key: key == "layer_height"
    layer_height_10 = unittest.mock.MagicMock() #Sets layer height to 10.
    layer_height_10.getProperty = lambda key, property: 10 if (key == "layer_height" and property == "value") else None
    layer_height_10.hasProperty = lambda key: key == "layer_height"
    no_layer_height = unittest.mock.MagicMock() #No settings at all.
    no_layer_height.getProperty = lambda key, property: None
    no_layer_height.hasProperty = lambda key: False

    extruder_stack.userChanges = no_layer_height
    extruder_stack.qualityChanges = no_layer_height
    extruder_stack.quality = no_layer_height
    extruder_stack.material = no_layer_height
    extruder_stack.variant = no_layer_height
    extruder_stack.definition = layer_height_5 #Here it is!

    assert extruder_stack.getProperty("layer_height", "value") == 5
    extruder_stack.variant = layer_height_10
    assert extruder_stack.getProperty("layer_height", "value") == 10
    extruder_stack.material = layer_height_5
    assert extruder_stack.getProperty("layer_height", "value") == 5
    extruder_stack.quality = layer_height_10
    assert extruder_stack.getProperty("layer_height", "value") == 10
    extruder_stack.qualityChanges = layer_height_5
    assert extruder_stack.getProperty("layer_height", "value") == 5
    extruder_stack.userChanges = layer_height_10
    assert extruder_stack.getProperty("layer_height", "value") == 10

##  Tests whether inserting a container is properly forbidden.
def test_insertContainer(extruder_stack):
    with pytest.raises(InvalidOperationError):
        extruder_stack.insertContainer(0, unittest.mock.MagicMock())

##  Tests whether removing a container is properly forbidden.
def test_removeContainer(extruder_stack):
    with pytest.raises(InvalidOperationError):
        extruder_stack.removeContainer(unittest.mock.MagicMock())

##  Tests setting definitions by specifying an ID of a definition that exists.
def test_setDefinitionByIdExists(extruder_stack, container_registry):
    original_container_registry = UM.Settings.ContainerStack._containerRegistry
    UM.Settings.ContainerStack._containerRegistry = container_registry #Always has all the profiles you ask of.

    extruder_stack.setDefinitionById("some_definition") #The container registry always has a container with the ID.

    #Restore.
    UM.Settings.ContainerStack._containerRegistry = original_container_registry

##  Tests setting definitions by specifying an ID of a definition that doesn't
#   exist.
def test_setDefinitionByIdDoesntExist(extruder_stack):
    with pytest.raises(KeyError):
        extruder_stack.setDefinitionById("some_definition") #Container registry is empty now.

##  Tests setting materials by specifying an ID of a material that exists.
def test_setMaterialByIdExists(extruder_stack, container_registry):
    original_container_registry = UM.Settings.ContainerStack._containerRegistry
    UM.Settings.ContainerStack._containerRegistry = container_registry #Always has all the profiles you ask of.

    extruder_stack.setMaterialById("some_material") #The container registry always has a container with the ID.

    #Restore.
    UM.Settings.ContainerStack._containerRegistry = original_container_registry

##  Tests setting materials by specifying an ID of a material that doesn't
#   exist.
def test_setMaterialByIdDoesntExist(extruder_stack):
    with pytest.raises(KeyError):
        extruder_stack.setMaterialById("some_material") #Container registry is empty now.

##  Tests setting qualities by specifying an ID of a quality that exists.
def test_setQualityByIdExists(extruder_stack, container_registry):
    original_container_registry = UM.Settings.ContainerStack._containerRegistry
    UM.Settings.ContainerStack._containerRegistry = container_registry #Always has all the profiles you ask of.

    extruder_stack.setQualityById("some_quality") #The container registry always has a container with the ID.

    #Restore.
    UM.Settings.ContainerStack._containerRegistry = original_container_registry

##  Tests setting qualities by specifying an ID of a quality that doesn't exist.
def test_setQualityByIdDoesntExist(extruder_stack):
    with pytest.raises(KeyError):
        extruder_stack.setQualityById("some_quality") #Container registry is empty now.