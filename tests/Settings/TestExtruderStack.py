# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import pytest #This module contains automated tests.
import unittest.mock #For the mocking and monkeypatching functionality.

import cura.Settings.CuraContainerStack #To get the list of container types.
import UM.Settings.ContainerRegistry #To create empty instance containers.
import UM.Settings.ContainerStack #To set the container registry the container stacks use.
from UM.Settings.DefinitionContainer import DefinitionContainer #To check against the class of DefinitionContainer.
from UM.Settings.InstanceContainer import InstanceContainer #To check against the class of InstanceContainer.
from cura.Settings.Exceptions import InvalidContainerError, InvalidOperationError #To check whether the correct exceptions are raised.
from cura.Settings.ExtruderManager import ExtruderManager
from cura.Settings.cura_empty_instance_containers import empty_container

##  Gets an instance container with a specified container type.
#
#   \param container_type The type metadata for the instance container.
#   \return An instance container instance.
def getInstanceContainer(container_type) -> InstanceContainer:
    container = InstanceContainer(container_id = "InstanceContainer")
    container.setMetaDataEntry("type", container_type)
    return container

class DefinitionContainerSubClass(DefinitionContainer):
    def __init__(self):
        super().__init__(container_id = "SubDefinitionContainer")

class InstanceContainerSubClass(InstanceContainer):
    def __init__(self, container_type):
        super().__init__(container_id = "SubInstanceContainer")
        self.setMetaDataEntry("type", container_type)

#############################START OF TEST CASES################################

##  Tests whether adding a container is properly forbidden.
def test_addContainer(extruder_stack):
    with pytest.raises(InvalidOperationError):
        extruder_stack.addContainer(unittest.mock.MagicMock())

#Tests setting user changes profiles to invalid containers.
@pytest.mark.parametrize("container", [
    getInstanceContainer(container_type = "wrong container type"),
    getInstanceContainer(container_type = "material"), #Existing, but still wrong type.
    DefinitionContainer(container_id = "wrong class")
])
def test_constrainUserChangesInvalid(container, extruder_stack):
    with pytest.raises(InvalidContainerError): #Invalid container, should raise an error.
        extruder_stack.userChanges = container

#Tests setting user changes profiles.
@pytest.mark.parametrize("container", [
    getInstanceContainer(container_type = "user"),
    InstanceContainerSubClass(container_type = "user")
])
def test_constrainUserChangesValid(container, extruder_stack):
    extruder_stack.userChanges = container #Should not give an error.

#Tests setting quality changes profiles to invalid containers.
@pytest.mark.parametrize("container", [
    getInstanceContainer(container_type = "wrong container type"),
    getInstanceContainer(container_type = "material"), #Existing, but still wrong type.
    DefinitionContainer(container_id = "wrong class")
])
def test_constrainQualityChangesInvalid(container, extruder_stack):
    with pytest.raises(InvalidContainerError): #Invalid container, should raise an error.
        extruder_stack.qualityChanges = container

#Test setting quality changes profiles.
@pytest.mark.parametrize("container", [
    getInstanceContainer(container_type = "quality_changes"),
    InstanceContainerSubClass(container_type = "quality_changes")
])
def test_constrainQualityChangesValid(container, extruder_stack):
    extruder_stack.qualityChanges = container #Should not give an error.

#Tests setting quality profiles to invalid containers.
@pytest.mark.parametrize("container", [
    getInstanceContainer(container_type = "wrong container type"),
    getInstanceContainer(container_type = "material"), #Existing, but still wrong type.
    DefinitionContainer(container_id = "wrong class")
])
def test_constrainQualityInvalid(container, extruder_stack):
    with pytest.raises(InvalidContainerError): #Invalid container, should raise an error.
        extruder_stack.quality = container

#Test setting quality profiles.
@pytest.mark.parametrize("container", [
    getInstanceContainer(container_type = "quality"),
    InstanceContainerSubClass(container_type = "quality")
])
def test_constrainQualityValid(container, extruder_stack):
    extruder_stack.quality = container #Should not give an error.

#Tests setting materials to invalid containers.
@pytest.mark.parametrize("container", [
    getInstanceContainer(container_type = "wrong container type"),
    getInstanceContainer(container_type = "quality"), #Existing, but still wrong type.
    DefinitionContainer(container_id = "wrong class")
])
def test_constrainMaterialInvalid(container, extruder_stack):
    with pytest.raises(InvalidContainerError): #Invalid container, should raise an error.
        extruder_stack.material = container

#Test setting materials.
@pytest.mark.parametrize("container", [
    getInstanceContainer(container_type = "material"),
    InstanceContainerSubClass(container_type = "material")
])
def test_constrainMaterialValid(container, extruder_stack):
    extruder_stack.material = container #Should not give an error.

#Tests setting variants to invalid containers.
@pytest.mark.parametrize("container", [
    getInstanceContainer(container_type = "wrong container type"),
    getInstanceContainer(container_type = "material"), #Existing, but still wrong type.
    DefinitionContainer(container_id = "wrong class")
])
def test_constrainVariantInvalid(container, extruder_stack):
    with pytest.raises(InvalidContainerError): #Invalid container, should raise an error.
        extruder_stack.variant = container

#Test setting variants.
@pytest.mark.parametrize("container", [
    getInstanceContainer(container_type = "variant"),
    InstanceContainerSubClass(container_type = "variant")
])
def test_constrainVariantValid(container, extruder_stack):
    extruder_stack.variant = container #Should not give an error.

#Tests setting definition changes profiles to invalid containers.
@pytest.mark.parametrize("container", [
    getInstanceContainer(container_type = "wrong container type"),
    getInstanceContainer(container_type = "material"), #Existing, but still wrong type.
    DefinitionContainer(container_id = "wrong class")
])
def test_constrainDefinitionChangesInvalid(container, global_stack):
    with pytest.raises(InvalidContainerError): #Invalid container, should raise an error.
        global_stack.definitionChanges = container

#Test setting definition changes profiles.
@pytest.mark.parametrize("container", [
    getInstanceContainer(container_type = "definition_changes"),
    InstanceContainerSubClass(container_type = "definition_changes")
])
def test_constrainDefinitionChangesValid(container, global_stack):
    global_stack.definitionChanges = container #Should not give an error.

#Tests setting definitions to invalid containers.
@pytest.mark.parametrize("container", [
    getInstanceContainer(container_type = "wrong class"),
    getInstanceContainer(container_type = "material"), #Existing, but still wrong class.
])
def test_constrainDefinitionInvalid(container, extruder_stack):
    with pytest.raises(InvalidContainerError): #Invalid container, should raise an error.
        extruder_stack.definition = container

#Test setting definitions.
@pytest.mark.parametrize("container", [
    DefinitionContainer(container_id = "DefinitionContainer"),
    DefinitionContainerSubClass()
])
def test_constrainDefinitionValid(container, extruder_stack):
    extruder_stack.definition = container #Should not give an error.

##  Tests whether deserialising completes the missing containers with empty ones.
def test_deserializeCompletesEmptyContainers(extruder_stack):
    extruder_stack._containers = [DefinitionContainer(container_id = "definition"), extruder_stack.definitionChanges] #Set the internal state of this stack manually.

    with unittest.mock.patch("UM.Settings.ContainerStack.ContainerStack.deserialize", unittest.mock.MagicMock()): #Prevent calling super().deserialize.
        extruder_stack.deserialize("")

    assert len(extruder_stack.getContainers()) == len(cura.Settings.CuraContainerStack._ContainerIndexes.IndexTypeMap) #Needs a slot for every type.
    for container_type_index in cura.Settings.CuraContainerStack._ContainerIndexes.IndexTypeMap:
        if container_type_index in \
                (cura.Settings.CuraContainerStack._ContainerIndexes.Definition,
                 cura.Settings.CuraContainerStack._ContainerIndexes.DefinitionChanges):  # We're not checking the definition or definition_changes
            continue
        assert extruder_stack.getContainer(container_type_index) == empty_container #All others need to be empty.

##  Tests whether an instance container with the wrong type gets removed when deserialising.
def test_deserializeRemovesWrongInstanceContainer(extruder_stack):
    extruder_stack._containers[cura.Settings.CuraContainerStack._ContainerIndexes.Quality] = getInstanceContainer(container_type = "wrong type")
    extruder_stack._containers[cura.Settings.CuraContainerStack._ContainerIndexes.Definition] = DefinitionContainer(container_id = "some definition")

    with unittest.mock.patch("UM.Settings.ContainerStack.ContainerStack.deserialize", unittest.mock.MagicMock()): #Prevent calling super().deserialize.
        extruder_stack.deserialize("")

    assert extruder_stack.quality == extruder_stack._empty_instance_container #Replaced with empty.

##  Tests whether a container with the wrong class gets removed when deserialising.
def test_deserializeRemovesWrongContainerClass(extruder_stack):
    extruder_stack._containers[cura.Settings.CuraContainerStack._ContainerIndexes.Quality] = DefinitionContainer(container_id = "wrong class")
    extruder_stack._containers[cura.Settings.CuraContainerStack._ContainerIndexes.Definition] = DefinitionContainer(container_id = "some definition")

    with unittest.mock.patch("UM.Settings.ContainerStack.ContainerStack.deserialize", unittest.mock.MagicMock()): #Prevent calling super().deserialize.
        extruder_stack.deserialize("")

    assert extruder_stack.quality == extruder_stack._empty_instance_container #Replaced with empty.

##  Tests whether an instance container in the definition spot results in an error.
def test_deserializeWrongDefinitionClass(extruder_stack):
    extruder_stack._containers[cura.Settings.CuraContainerStack._ContainerIndexes.Definition] = getInstanceContainer(container_type = "definition") #Correct type but wrong class.

    with unittest.mock.patch("UM.Settings.ContainerStack.ContainerStack.deserialize", unittest.mock.MagicMock()): #Prevent calling super().deserialize.
        with pytest.raises(UM.Settings.ContainerStack.InvalidContainerStackError): #Must raise an error that there is no definition container.
            extruder_stack.deserialize("")

##  Tests whether an instance container with the wrong type is moved into the correct slot by deserialising.
def test_deserializeMoveInstanceContainer(extruder_stack):
    extruder_stack._containers[cura.Settings.CuraContainerStack._ContainerIndexes.Quality] = getInstanceContainer(container_type = "material") #Not in the correct spot.
    extruder_stack._containers[cura.Settings.CuraContainerStack._ContainerIndexes.Definition] = DefinitionContainer(container_id = "some definition")

    with unittest.mock.patch("UM.Settings.ContainerStack.ContainerStack.deserialize", unittest.mock.MagicMock()): #Prevent calling super().deserialize.
        extruder_stack.deserialize("")

    assert extruder_stack.quality == empty_container
    assert extruder_stack.material != empty_container

##  Tests whether a definition container in the wrong spot is moved into the correct spot by deserialising.
def test_deserializeMoveDefinitionContainer(extruder_stack):
    extruder_stack._containers[cura.Settings.CuraContainerStack._ContainerIndexes.Material] = DefinitionContainer(container_id = "some definition") #Not in the correct spot.

    with unittest.mock.patch("UM.Settings.ContainerStack.ContainerStack.deserialize", unittest.mock.MagicMock()): #Prevent calling super().deserialize.
        extruder_stack.deserialize("")

    assert extruder_stack.material == empty_container
    assert extruder_stack.definition != empty_container

##  Tests whether getProperty properly applies the stack-like behaviour on its containers.
def test_getPropertyFallThrough(global_stack, extruder_stack):
    # ExtruderStack.setNextStack calls registerExtruder for backward compatibility, but we do not need a complete extruder manager
    ExtruderManager._ExtruderManager__instance = unittest.mock.MagicMock()

    #A few instance container mocks to put in the stack.
    mock_layer_heights = {} #For each container type, a mock container that defines layer height to something unique.
    mock_no_settings = {} #For each container type, a mock container that has no settings at all.
    container_indices = cura.Settings.CuraContainerStack._ContainerIndexes #Cache.
    for type_id, type_name in container_indices.IndexTypeMap.items():
        container = unittest.mock.MagicMock()
        # Return type_id when asking for value and -1 when asking for settable_per_extruder
        container.getProperty = lambda key, property, context = None, type_id = type_id: type_id if (key == "layer_height" and property == "value") else (None if property != "settable_per_extruder" else "-1") #Returns the container type ID as layer height, in order to identify it.
        container.hasProperty = lambda key, property: key == "layer_height"
        container.getMetaDataEntry = unittest.mock.MagicMock(return_value = type_name)
        mock_layer_heights[type_id] = container

        container = unittest.mock.MagicMock()
        container.getProperty = unittest.mock.MagicMock(return_value = None) #Has no settings at all.
        container.hasProperty = unittest.mock.MagicMock(return_value = False)
        container.getMetaDataEntry = unittest.mock.MagicMock(return_value = type_name)
        mock_no_settings[type_id] = container

    extruder_stack.userChanges = mock_no_settings[container_indices.UserChanges]
    extruder_stack.qualityChanges = mock_no_settings[container_indices.QualityChanges]
    extruder_stack.quality = mock_no_settings[container_indices.Quality]
    extruder_stack.material = mock_no_settings[container_indices.Material]
    extruder_stack.variant = mock_no_settings[container_indices.Variant]
    with unittest.mock.patch("cura.Settings.CuraContainerStack.DefinitionContainer", unittest.mock.MagicMock): #To guard against the type checking.
        extruder_stack.definition = mock_layer_heights[container_indices.Definition] #There's a layer height in here!

    extruder_stack.setNextStack(global_stack)

    assert extruder_stack.getProperty("layer_height", "value") == container_indices.Definition
    extruder_stack.variant = mock_layer_heights[container_indices.Variant]
    assert extruder_stack.getProperty("layer_height", "value") == container_indices.Variant
    extruder_stack.material = mock_layer_heights[container_indices.Material]
    assert extruder_stack.getProperty("layer_height", "value") == container_indices.Material
    extruder_stack.quality = mock_layer_heights[container_indices.Quality]
    assert extruder_stack.getProperty("layer_height", "value") == container_indices.Quality
    extruder_stack.qualityChanges = mock_layer_heights[container_indices.QualityChanges]
    assert extruder_stack.getProperty("layer_height", "value") == container_indices.QualityChanges
    extruder_stack.userChanges = mock_layer_heights[container_indices.UserChanges]
    assert extruder_stack.getProperty("layer_height", "value") == container_indices.UserChanges

##  Tests whether inserting a container is properly forbidden.
def test_insertContainer(extruder_stack):
    with pytest.raises(InvalidOperationError):
        extruder_stack.insertContainer(0, unittest.mock.MagicMock())

##  Tests whether removing a container is properly forbidden.
def test_removeContainer(extruder_stack):
    with pytest.raises(InvalidOperationError):
        extruder_stack.removeContainer(unittest.mock.MagicMock())

##  Tests setting properties directly on the extruder stack.
@pytest.mark.parametrize("key,              property,         value", [
                        ("layer_height",    "value",          0.1337),
                        ("foo",             "value",          100),
                        ("support_enabled", "value",          True),
                        ("layer_height",    "default_value",  0.1337),
                        ("layer_height",    "is_bright_pink", "of course")
])
def test_setPropertyUser(key, property, value, extruder_stack):
    user_changes = unittest.mock.MagicMock()
    user_changes.getMetaDataEntry = unittest.mock.MagicMock(return_value = "user")
    extruder_stack.userChanges = user_changes

    extruder_stack.setProperty(key, property, value) #The actual test.

    extruder_stack.userChanges.setProperty.assert_called_once_with(key, property, value, None, False) #Make sure that the user container gets a setProperty call.