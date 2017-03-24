# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import os.path #To find the test files.
import pytest #This module contains unit tests.
import unittest.mock #To monkeypatch some mocks in place of dependencies.

import cura.Settings.GlobalStack #The module we're testing.
from cura.Settings.Exceptions import TooManyExtrudersError #To test raising this error.
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

#An empty global stack to test with.
@pytest.fixture()
def global_stack() -> cura.Settings.GlobalStack.GlobalStack:
    return cura.Settings.GlobalStack.GlobalStack("TestStack")

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

##  Tests adding extruders to the global stack.
def test_addExtruder(global_stack):
    mock_definition = unittest.mock.MagicMock()
    mock_definition.getProperty = lambda key, property: 2 if key == "machine_extruder_count" and property == "value" else None

    global_stack.definition = mock_definition

    global_stack.addExtruder(unittest.mock.MagicMock())
    global_stack.addExtruder(unittest.mock.MagicMock())
    with pytest.raises(TooManyExtrudersError): #Should be limited to 2 extruders because of machine_extruder_count.
        global_stack.addExtruder(unittest.mock.MagicMock())

##  Tests whether the user changes are being read properly from a global stack.
@pytest.mark.parametrize("filename,                 user_changes_id", [
                        ("Global.global.cfg",       "empty"),
                        ("Global.stack.cfg",        "empty"),
                        ("MachineLegacy.stack.cfg", "empty"),
                        ("OnlyUser.global.cfg",     "some_instance"), #This one does have a user profile.
                        ("Complete.global.cfg",     "some_user_changes")
])
def test_deserializeUserChanges(filename, user_changes_id, container_registry, global_stack):
    serialized = readStack(filename)

    #Mock the loading of the instance containers.
    global_stack.findContainer = findSomeContainers
    original_container_registry = UM.Settings.ContainerStack._containerRegistry
    UM.Settings.ContainerStack._containerRegistry = container_registry #Always has all profiles you ask of.

    global_stack.deserialize(serialized)

    assert global_stack.userChanges.getId() == user_changes_id

    #Restore.
    UM.Settings.ContainerStack._containerRegistry = original_container_registry

##  Tests whether the quality changes are being read properly from a global
#   stack.
@pytest.mark.parametrize("filename,                       quality_changes_id", [
                        ("Global.global.cfg",             "empty"),
                        ("Global.stack.cfg",              "empty"),
                        ("MachineLegacy.stack.cfg",       "empty"),
                        ("OnlyQualityChanges.global.cfg", "some_instance"),
                        ("Complete.global.cfg",           "some_quality_changes")
])
def test_deserializeQualityChanges(filename, quality_changes_id, container_registry, global_stack):
    serialized = readStack(filename)

    #Mock the loading of the instance containers.
    global_stack.findContainer = findSomeContainers
    original_container_registry = UM.Settings.ContainerStack._containerRegistry
    UM.Settings.ContainerStack._containerRegistry = container_registry #Always has all the profiles you ask of.

    global_stack.deserialize(serialized)

    assert global_stack.qualityChanges.getId() == quality_changes_id

    #Restore.
    UM.Settings.ContainerStack._containerRegistry = original_container_registry

##  Tests whether the quality profile is being read properly from a global
#   stack.
@pytest.mark.parametrize("filename,                 quality_id", [
                        ("Global.global.cfg",       "empty"),
                        ("Global.stack.cfg",        "empty"),
                        ("MachineLegacy.stack.cfg", "empty"),
                        ("OnlyQuality.global.cfg",  "some_instance"),
                        ("Complete.global.cfg",     "some_quality")
])
def test_deserializeQuality(filename, quality_id, container_registry, global_stack):
    serialized = readStack(filename)

    #Mock the loading of the instance containers.
    global_stack.findContainer = findSomeContainers
    original_container_registry = UM.Settings.ContainerStack._containerRegistry
    UM.Settings.ContainerStack._containerRegistry = container_registry #Always has all the profiles you ask of.

    global_stack.deserialize(serialized)

    assert global_stack.quality.getId() == quality_id

    #Restore.
    UM.Settings.ContainerStack._containerRegistry = original_container_registry

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
def test_deserializeMaterial(filename, material_id, container_registry, global_stack):
    serialized = readStack(filename)

    #Mock the loading of the instance containers.
    global_stack.findContainer = findSomeContainers
    original_container_registry = UM.Settings.ContainerStack._containerRegistry
    UM.Settings.ContainerStack._containerRegistry = container_registry #Always has all the profiles you ask of.

    global_stack.deserialize(serialized)

    assert global_stack.material.getId() == material_id

    #Restore.
    UM.Settings.ContainerStack._containerRegistry = original_container_registry

##  Tests whether the variant profile is being read properly from a global
#   stack.
@pytest.mark.parametrize("filename,                 variant_id", [
                        ("Global.global.cfg",       "empty"),
                        ("Global.stack.cfg",        "empty"),
                        ("MachineLegacy.stack.cfg", "empty"),
                        ("OnlyVariant.global.cfg",  "some_instance"),
                        ("Complete.global.cfg",     "some_variant")
])
def test_deserializeVariant(filename, variant_id, container_registry, global_stack):
    serialized = readStack(filename)

    #Mock the loading of the instance containers.
    global_stack.findContainer = findSomeContainers
    original_container_registry = UM.Settings.ContainerStack._containerRegistry
    UM.Settings.ContainerStack._containerRegistry = container_registry #Always has all the profiles you ask of.

    global_stack.deserialize(serialized)

    assert global_stack.variant.getId() == variant_id

    #Restore.
    UM.Settings.ContainerStack._containerRegistry = original_container_registry

##  Tests whether the definition changes profile is being read properly from a
#   global stack.
@pytest.mark.parametrize("filename,                          definition_changes_id", [
                        ("Global.global.cfg",                "empty"),
                        ("Global.stack.cfg",                 "empty"),
                        ("MachineLegacy.stack.cfg",          "empty"),
                        ("OnlyDefinitionChanges.global.cfg", "some_instance"),
                        ("Complete.global.cfg",              "some_material")
])
def test_deserializeDefinitionChanges(filename, definition_changes_id, container_registry, global_stack):
    serialized = readStack(filename)
    global_stack = cura.Settings.GlobalStack.GlobalStack("TestStack")

    #Mock the loading of the instance containers.
    global_stack.findContainer = findSomeContainers
    original_container_registry = UM.Settings.ContainerStack._containerRegistry
    UM.Settings.ContainerStack._containerRegistry = container_registry #Always has all the profiles you ask of.

    global_stack.deserialize(serialized)

    assert global_stack.definitionChanges.getId() == definition_changes_id

    #Restore.
    UM.Settings.ContainerStack._containerRegistry = original_container_registry

##  Tests whether the definition is being read properly from a global stack.
@pytest.mark.parametrize("filename,                   definition_id", [
                        ("Global.global.cfg",         "some_definition"),
                        ("Global.stack.cfg",          "some_definition"),
                        ("MachineLegacy.stack.cfg",   "some_definition"),
                        ("OnlyDefinition.global.cfg", "some_definition"),
                        ("Complete.global.cfg",       "some_definition")
])
def test_deserializeDefinition(filename, definition_id, container_registry, global_stack):
    serialized = readStack(filename)

    #Mock the loading of the instance containers.
    global_stack.findContainer = findSomeContainers
    original_container_registry = UM.Settings.ContainerStack._containerRegistry
    UM.Settings.ContainerStack._containerRegistry = container_registry #Always has all the profiles you ask of.

    global_stack.deserialize(serialized)

    assert global_stack.definition.getId() == definition_id

    #Restore.
    UM.Settings.ContainerStack._containerRegistry = original_container_registry

def test_deserializeMissingContainer(container_registry, global_stack):
    serialized = readStack("Global.global.cfg")
    try:
        global_stack.deserialize(serialized)
    except Exception as e:
        #Must be exactly Exception, not one of its subclasses, since that is what gets raised when a stack has an unknown container.
        #That's why we can't use pytest.raises.
        assert type(e) == Exception

##  Tests whether getProperty properly applies the stack-like behaviour on its
#   containers.
def test_getPropertyFallThrough(global_stack):
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

    global_stack.userChanges = no_layer_height
    global_stack.qualityChanges = no_layer_height
    global_stack.quality = no_layer_height
    global_stack.material = no_layer_height
    global_stack.variant = no_layer_height
    global_stack.definitionChanges = no_layer_height
    global_stack.definition = layer_height_5 #Here it is!

    assert global_stack.getProperty("layer_height", "value") == 5
    global_stack.definitionChanges = layer_height_10
    assert global_stack.getProperty("layer_height", "value") == 10
    global_stack.variant = layer_height_5
    assert global_stack.getProperty("layer_height", "value") == 5
    global_stack.material = layer_height_10
    assert global_stack.getProperty("layer_height", "value") == 10
    global_stack.quality = layer_height_5
    assert global_stack.getProperty("layer_height", "value") == 5
    global_stack.qualityChanges = layer_height_10
    assert global_stack.getProperty("layer_height", "value") == 10
    global_stack.userChanges = layer_height_5
    assert global_stack.getProperty("layer_height", "value") == 5

##  Tests whether the hasUserValue returns true for settings that are changed in
#   the user-changes container.
def test_hasUserValueUserChanges(global_stack):
    user_changes = unittest.mock.MagicMock()
    def hasProperty(key, property):
        return key == "layer_height" and property == "value" #Only have the layer_height property set.
    user_changes.hasProperty = hasProperty

    global_stack.userChanges = user_changes

    assert not global_stack.hasUserValue("infill_sparse_density")
    assert global_stack.hasUserValue("layer_height")
    assert not global_stack.hasUserValue("")

##  Tests whether the hasUserValue returns true for settings that are changed in
#   the quality-changes container.
def test_hasUserValueQualityChanges(global_stack):
    quality_changes = unittest.mock.MagicMock()
    def hasProperty(key, property):
        return key == "layer_height" and property == "value" #Only have the layer_height property set.
    quality_changes.hasProperty = hasProperty

    global_stack.qualityChanges = quality_changes

    assert not global_stack.hasUserValue("infill_sparse_density")
    assert global_stack.hasUserValue("layer_height")
    assert not global_stack.hasUserValue("")