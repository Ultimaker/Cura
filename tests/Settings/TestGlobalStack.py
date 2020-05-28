# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import pytest #This module contains unit tests.
import unittest.mock #To monkeypatch some mocks in place of dependencies.

import cura.Settings.CuraContainerStack #To get the list of container types.
from cura.Settings.Exceptions import InvalidContainerError, InvalidOperationError #To test raising these errors.
from UM.Settings.DefinitionContainer import DefinitionContainer #To test against the class DefinitionContainer.
from UM.Settings.InstanceContainer import InstanceContainer #To test against the class InstanceContainer.
from UM.Settings.SettingInstance import InstanceState
import UM.Settings.ContainerRegistry
import UM.Settings.ContainerStack
import UM.Settings.SettingDefinition #To add settings to the definition.

from cura.Settings.cura_empty_instance_containers import empty_container


def getInstanceContainer(container_type) -> InstanceContainer:
    """Gets an instance container with a specified container type.
    
    :param container_type: The type metadata for the instance container.
    :return: An instance container instance.
    """

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


############################START OF TEST CASES################################


def test_addContainer(global_stack):
    """Tests whether adding a container is properly forbidden."""

    with pytest.raises(InvalidOperationError):
        global_stack.addContainer(unittest.mock.MagicMock())


def test_addExtruder(global_stack):
    """Tests adding extruders to the global stack."""

    mock_definition = unittest.mock.MagicMock()
    mock_definition.getProperty = lambda key, property, context = None: 2 if key == "machine_extruder_count" and property == "value" else None

    with unittest.mock.patch("cura.Settings.CuraContainerStack.DefinitionContainer", unittest.mock.MagicMock):
        global_stack.definition = mock_definition

    assert len(global_stack.extruders) == 0
    first_extruder = unittest.mock.MagicMock()
    first_extruder.getMetaDataEntry = lambda key: 0 if key == "position" else None
    with unittest.mock.patch("cura.Settings.CuraContainerStack.DefinitionContainer", unittest.mock.MagicMock):
        global_stack.addExtruder(first_extruder)
    assert len(global_stack.extruders) == 1
    assert global_stack.extruders[0] == first_extruder
    second_extruder = unittest.mock.MagicMock()
    second_extruder.getMetaDataEntry = lambda key: 1 if key == "position" else None
    with unittest.mock.patch("cura.Settings.CuraContainerStack.DefinitionContainer", unittest.mock.MagicMock):
        global_stack.addExtruder(second_extruder)
    assert len(global_stack.extruders) == 2
    assert global_stack.extruders[1] == second_extruder
    # Disabled for now for Custom FDM Printer
    # with unittest.mock.patch("cura.Settings.CuraContainerStack.DefinitionContainer", unittest.mock.MagicMock):
    #     with pytest.raises(TooManyExtrudersError): #Should be limited to 2 extruders because of machine_extruder_count.
    #         global_stack.addExtruder(unittest.mock.MagicMock())
    assert len(global_stack.extruders) == 2 #Didn't add the faulty extruder.


#Tests setting user changes profiles to invalid containers.
@pytest.mark.parametrize("container", [
    getInstanceContainer(container_type = "wrong container type"),
    getInstanceContainer(container_type = "material"), #Existing, but still wrong type.
    DefinitionContainer(container_id = "wrong class")
])
def test_constrainUserChangesInvalid(container, global_stack):
    with pytest.raises(InvalidContainerError): #Invalid container, should raise an error.
        global_stack.userChanges = container


#Tests setting user changes profiles.
@pytest.mark.parametrize("container", [
    getInstanceContainer(container_type = "user"),
    InstanceContainerSubClass(container_type = "user")
])
def test_constrainUserChangesValid(container, global_stack):
    global_stack.userChanges = container #Should not give an error.


#Tests setting quality changes profiles to invalid containers.
@pytest.mark.parametrize("container", [
    getInstanceContainer(container_type = "wrong container type"),
    getInstanceContainer(container_type = "material"), #Existing, but still wrong type.
    DefinitionContainer(container_id = "wrong class")
])
def test_constrainQualityChangesInvalid(container, global_stack):
    with pytest.raises(InvalidContainerError): #Invalid container, should raise an error.
        global_stack.qualityChanges = container


#Test setting quality changes profiles.
@pytest.mark.parametrize("container", [
    getInstanceContainer(container_type = "quality_changes"),
    InstanceContainerSubClass(container_type = "quality_changes")
])
def test_constrainQualityChangesValid(container, global_stack):
    global_stack.qualityChanges = container #Should not give an error.


#Tests setting quality profiles to invalid containers.
@pytest.mark.parametrize("container", [
    getInstanceContainer(container_type = "wrong container type"),
    getInstanceContainer(container_type = "material"), #Existing, but still wrong type.
    DefinitionContainer(container_id = "wrong class")
])
def test_constrainQualityInvalid(container, global_stack):
    with pytest.raises(InvalidContainerError): #Invalid container, should raise an error.
        global_stack.quality = container


#Test setting quality profiles.
@pytest.mark.parametrize("container", [
    getInstanceContainer(container_type = "quality"),
    InstanceContainerSubClass(container_type = "quality")
])
def test_constrainQualityValid(container, global_stack):
    global_stack.quality = container #Should not give an error.


#Tests setting materials to invalid containers.
@pytest.mark.parametrize("container", [
    getInstanceContainer(container_type = "wrong container type"),
    getInstanceContainer(container_type = "quality"), #Existing, but still wrong type.
    DefinitionContainer(container_id = "wrong class")
])
def test_constrainMaterialInvalid(container, global_stack):
    with pytest.raises(InvalidContainerError): #Invalid container, should raise an error.
        global_stack.material = container


#Test setting materials.
@pytest.mark.parametrize("container", [
    getInstanceContainer(container_type = "material"),
    InstanceContainerSubClass(container_type = "material")
])
def test_constrainMaterialValid(container, global_stack):
    global_stack.material = container #Should not give an error.


#Tests setting variants to invalid containers.
@pytest.mark.parametrize("container", [
    getInstanceContainer(container_type = "wrong container type"),
    getInstanceContainer(container_type = "material"), #Existing, but still wrong type.
    DefinitionContainer(container_id = "wrong class")
])
def test_constrainVariantInvalid(container, global_stack):
    with pytest.raises(InvalidContainerError): #Invalid container, should raise an error.
        global_stack.variant = container


#Test setting variants.
@pytest.mark.parametrize("container", [
    getInstanceContainer(container_type = "variant"),
    InstanceContainerSubClass(container_type = "variant")
])
def test_constrainVariantValid(container, global_stack):
    global_stack.variant = container #Should not give an error.


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
def test_constrainDefinitionInvalid(container, global_stack):
    with pytest.raises(InvalidContainerError): #Invalid container, should raise an error.
        global_stack.definition = container


#Test setting definitions.
@pytest.mark.parametrize("container", [
    DefinitionContainer(container_id = "DefinitionContainer"),
    DefinitionContainerSubClass()
])
def test_constrainDefinitionValid(container, global_stack):
    global_stack.definition = container #Should not give an error.


def test_deserializeCompletesEmptyContainers(global_stack):
    """Tests whether deserialising completes the missing containers with empty ones. The initial containers are just the
    
    definition and the definition_changes (that cannot be empty after CURA-5281)
    """

    global_stack._containers = [DefinitionContainer(container_id = "definition"), global_stack.definitionChanges] #Set the internal state of this stack manually.

    with unittest.mock.patch("UM.Settings.ContainerStack.ContainerStack.deserialize", unittest.mock.MagicMock()): #Prevent calling super().deserialize.
        global_stack.deserialize("")

    assert len(global_stack.getContainers()) == len(cura.Settings.CuraContainerStack._ContainerIndexes.IndexTypeMap) #Needs a slot for every type.
    for container_type_index in cura.Settings.CuraContainerStack._ContainerIndexes.IndexTypeMap:
        if container_type_index in \
                (cura.Settings.CuraContainerStack._ContainerIndexes.Definition, cura.Settings.CuraContainerStack._ContainerIndexes.DefinitionChanges): #We're not checking the definition or definition_changes
            continue
        assert global_stack.getContainer(container_type_index) == empty_container #All others need to be empty.


def test_deserializeRemovesWrongInstanceContainer(global_stack):
    """Tests whether an instance container with the wrong type gets removed when deserialising."""

    global_stack._containers[cura.Settings.CuraContainerStack._ContainerIndexes.Quality] = getInstanceContainer(container_type = "wrong type")
    global_stack._containers[cura.Settings.CuraContainerStack._ContainerIndexes.Definition] = DefinitionContainer(container_id = "some definition")

    with unittest.mock.patch("UM.Settings.ContainerStack.ContainerStack.deserialize", unittest.mock.MagicMock()): #Prevent calling super().deserialize.
        global_stack.deserialize("")

    assert global_stack.quality == global_stack._empty_instance_container #Replaced with empty.


def test_deserializeRemovesWrongContainerClass(global_stack):
    """Tests whether a container with the wrong class gets removed when deserialising."""

    global_stack._containers[cura.Settings.CuraContainerStack._ContainerIndexes.Quality] = DefinitionContainer(container_id = "wrong class")
    global_stack._containers[cura.Settings.CuraContainerStack._ContainerIndexes.Definition] = DefinitionContainer(container_id = "some definition")

    with unittest.mock.patch("UM.Settings.ContainerStack.ContainerStack.deserialize", unittest.mock.MagicMock()): #Prevent calling super().deserialize.
        global_stack.deserialize("")

    assert global_stack.quality == global_stack._empty_instance_container #Replaced with empty.


def test_deserializeWrongDefinitionClass(global_stack):
    """Tests whether an instance container in the definition spot results in an error."""

    global_stack._containers[cura.Settings.CuraContainerStack._ContainerIndexes.Definition] = getInstanceContainer(container_type = "definition") #Correct type but wrong class.

    with unittest.mock.patch("UM.Settings.ContainerStack.ContainerStack.deserialize", unittest.mock.MagicMock()): #Prevent calling super().deserialize.
        with pytest.raises(UM.Settings.ContainerStack.InvalidContainerStackError): #Must raise an error that there is no definition container.
            global_stack.deserialize("")


def test_deserializeMoveInstanceContainer(global_stack):
    """Tests whether an instance container with the wrong type is moved into the correct slot by deserialising."""

    global_stack._containers[cura.Settings.CuraContainerStack._ContainerIndexes.Quality] = getInstanceContainer(container_type = "material") #Not in the correct spot.
    global_stack._containers[cura.Settings.CuraContainerStack._ContainerIndexes.Definition] = DefinitionContainer(container_id = "some definition")

    with unittest.mock.patch("UM.Settings.ContainerStack.ContainerStack.deserialize", unittest.mock.MagicMock()): #Prevent calling super().deserialize.
        global_stack.deserialize("")

    assert global_stack.quality == empty_container
    assert global_stack.material != empty_container


def test_deserializeMoveDefinitionContainer(global_stack):
    """Tests whether a definition container in the wrong spot is moved into the correct spot by deserialising."""

    global_stack._containers[cura.Settings.CuraContainerStack._ContainerIndexes.Material] = DefinitionContainer(container_id = "some definition") #Not in the correct spot.

    with unittest.mock.patch("UM.Settings.ContainerStack.ContainerStack.deserialize", unittest.mock.MagicMock()): #Prevent calling super().deserialize.
        global_stack.deserialize("")

    assert global_stack.material == empty_container
    assert global_stack.definition != empty_container


def test_getPropertyFallThrough(global_stack):
    """Tests whether getProperty properly applies the stack-like behaviour on its containers."""

    #A few instance container mocks to put in the stack.
    mock_layer_heights = {} #For each container type, a mock container that defines layer height to something unique.
    mock_no_settings = {} #For each container type, a mock container that has no settings at all.
    container_indexes = cura.Settings.CuraContainerStack._ContainerIndexes #Cache.
    for type_id, type_name in container_indexes.IndexTypeMap.items():
        container = unittest.mock.MagicMock()
        container.getProperty = lambda key, property, context = None, type_id = type_id: type_id if (key == "layer_height" and property == "value") else None #Returns the container type ID as layer height, in order to identify it.
        container.hasProperty = lambda key, property: key == "layer_height"
        container.getMetaDataEntry = unittest.mock.MagicMock(return_value = type_name)
        mock_layer_heights[type_id] = container

        container = unittest.mock.MagicMock()
        container.getProperty = unittest.mock.MagicMock(return_value = None) #Has no settings at all.
        container.hasProperty = unittest.mock.MagicMock(return_value = False)
        container.getMetaDataEntry = unittest.mock.MagicMock(return_value = type_name)
        mock_no_settings[type_id] = container

    global_stack.userChanges = mock_no_settings[container_indexes.UserChanges]
    global_stack.qualityChanges = mock_no_settings[container_indexes.QualityChanges]
    global_stack.quality = mock_no_settings[container_indexes.Quality]
    global_stack.material = mock_no_settings[container_indexes.Material]
    global_stack.variant = mock_no_settings[container_indexes.Variant]
    global_stack.definitionChanges = mock_no_settings[container_indexes.DefinitionChanges]
    with unittest.mock.patch("cura.Settings.CuraContainerStack.DefinitionContainer", unittest.mock.MagicMock): #To guard against the type checking.
        global_stack.definition = mock_layer_heights[container_indexes.Definition] #There's a layer height in here!

    assert global_stack.getProperty("layer_height", "value") == container_indexes.Definition
    global_stack.definitionChanges = mock_layer_heights[container_indexes.DefinitionChanges]
    assert global_stack.getProperty("layer_height", "value") == container_indexes.DefinitionChanges
    global_stack.variant = mock_layer_heights[container_indexes.Variant]
    assert global_stack.getProperty("layer_height", "value") == container_indexes.Variant
    global_stack.material = mock_layer_heights[container_indexes.Material]
    assert global_stack.getProperty("layer_height", "value") == container_indexes.Material
    global_stack.quality = mock_layer_heights[container_indexes.Quality]
    assert global_stack.getProperty("layer_height", "value") == container_indexes.Quality
    global_stack.qualityChanges = mock_layer_heights[container_indexes.QualityChanges]
    assert global_stack.getProperty("layer_height", "value") == container_indexes.QualityChanges
    global_stack.userChanges = mock_layer_heights[container_indexes.UserChanges]
    assert global_stack.getProperty("layer_height", "value") == container_indexes.UserChanges


def test_getPropertyNoResolveInDefinition(global_stack):
    """In definitions, test whether having no resolve allows us to find the value."""

    value = unittest.mock.MagicMock() #Just sets the value for bed temperature.
    value.getProperty = lambda key, property, context = None: 10 if (key == "material_bed_temperature" and property == "value") else None

    with unittest.mock.patch("cura.Settings.CuraContainerStack.DefinitionContainer", unittest.mock.MagicMock): #To guard against the type checking.
        global_stack.definition = value
    assert global_stack.getProperty("material_bed_temperature", "value") == 10 #No resolve, so fall through to value.


def test_getPropertyResolveInDefinition(global_stack):
    """In definitions, when the value is asked and there is a resolve function, it must get the resolve first."""

    resolve_and_value = unittest.mock.MagicMock() #Sets the resolve and value for bed temperature.
    resolve_and_value.getProperty = lambda key, property, context = None: (7.5 if property == "resolve" else 5) if (key == "material_bed_temperature" and property in ("resolve", "value")) else None #7.5 resolve, 5 value.

    with unittest.mock.patch("cura.Settings.CuraContainerStack.DefinitionContainer", unittest.mock.MagicMock): #To guard against the type checking.
        global_stack.definition = resolve_and_value
    assert global_stack.getProperty("material_bed_temperature", "value") == 7.5 #Resolve wins in the definition.


def test_getPropertyResolveInInstance(global_stack):
    """In instance containers, when the value is asked and there is a resolve function, it must get the value first."""

    container_indices = cura.Settings.CuraContainerStack._ContainerIndexes
    instance_containers = {}
    for container_type in container_indices.IndexTypeMap:
        instance_containers[container_type] = unittest.mock.MagicMock() #Sets the resolve and value for bed temperature.
        instance_containers[container_type].getProperty = lambda key, property, context = None: (7.5 if property == "resolve" else (InstanceState.User if property == "state" else (5 if property != "limit_to_extruder" else "-1"))) if (key == "material_bed_temperature") else None #7.5 resolve, 5 value.
        instance_containers[container_type].getMetaDataEntry = unittest.mock.MagicMock(return_value = container_indices.IndexTypeMap[container_type]) #Make queries for the type return the desired type.
    instance_containers[container_indices.Definition].getProperty = lambda key, property, context = None: 10 if (key == "material_bed_temperature" and property == "value") else None #Definition only has value.
    with unittest.mock.patch("cura.Settings.CuraContainerStack.DefinitionContainer", unittest.mock.MagicMock): #To guard against the type checking.
        global_stack.definition = instance_containers[container_indices.Definition] #Stack must have a definition.

    #For all instance container slots, the value reigns over resolve.
    global_stack.definitionChanges = instance_containers[container_indices.DefinitionChanges]
    assert global_stack.getProperty("material_bed_temperature", "value") == 5
    global_stack.variant = instance_containers[container_indices.Variant]
    assert global_stack.getProperty("material_bed_temperature", "value") == 5
    global_stack.material = instance_containers[container_indices.Material]
    assert global_stack.getProperty("material_bed_temperature", "value") == 5
    global_stack.quality = instance_containers[container_indices.Quality]
    assert global_stack.getProperty("material_bed_temperature", "value") == 5
    global_stack.qualityChanges = instance_containers[container_indices.QualityChanges]
    assert global_stack.getProperty("material_bed_temperature", "value") == 5
    global_stack.userChanges = instance_containers[container_indices.UserChanges]
    assert global_stack.getProperty("material_bed_temperature", "value") == 5


def test_getPropertyInstancesBeforeResolve(global_stack):
    """Tests whether the value in instances gets evaluated before the resolve in definitions."""

    def getValueProperty(key, property, context = None):
        if key != "material_bed_temperature":
            return None
        if property == "value":
            return 10
        if property == "limit_to_extruder":
            return -1
        return InstanceState.User

    def getResolveProperty(key, property, context = None):
        if key != "material_bed_temperature":
            return None
        if property == "resolve":
            return 7.5
        return None

    value = unittest.mock.MagicMock() #Sets just the value.
    value.getProperty = unittest.mock.MagicMock(side_effect = getValueProperty)
    value.getMetaDataEntry = unittest.mock.MagicMock(return_value = "quality")
    resolve = unittest.mock.MagicMock() #Sets just the resolve.
    resolve.getProperty = unittest.mock.MagicMock(side_effect = getResolveProperty)

    with unittest.mock.patch("cura.Settings.CuraContainerStack.DefinitionContainer", unittest.mock.MagicMock): #To guard against the type checking.
        global_stack.definition = resolve
    global_stack.quality = value

    assert global_stack.getProperty("material_bed_temperature", "value") == 10


def test_hasUserValueUserChanges(global_stack):
    """Tests whether the hasUserValue returns true for settings that are changed in the user-changes container."""

    container = unittest.mock.MagicMock()
    container.getMetaDataEntry = unittest.mock.MagicMock(return_value = "user")
    container.hasProperty = lambda key, property: key == "layer_height" #Only have the layer_height property set.
    global_stack.userChanges = container

    assert global_stack.hasUserValue("layer_height")
    assert not global_stack.hasUserValue("infill_sparse_density")
    assert not global_stack.hasUserValue("")


def test_hasUserValueQualityChanges(global_stack):
    """Tests whether the hasUserValue returns true for settings that are changed in the quality-changes container."""

    container = unittest.mock.MagicMock()
    container.getMetaDataEntry = unittest.mock.MagicMock(return_value = "quality_changes")
    container.hasProperty = lambda key, property: key == "layer_height" #Only have the layer_height property set.
    global_stack.qualityChanges = container

    assert global_stack.hasUserValue("layer_height")
    assert not global_stack.hasUserValue("infill_sparse_density")
    assert not global_stack.hasUserValue("")


def test_hasNoUserValue(global_stack):
    """Tests whether a container in some other place on the stack is correctly not recognised as user value."""

    container = unittest.mock.MagicMock()
    container.getMetaDataEntry = unittest.mock.MagicMock(return_value = "quality")
    container.hasProperty = lambda key, property: key == "layer_height" #Only have the layer_height property set.
    global_stack.quality = container

    assert not global_stack.hasUserValue("layer_height") #However this container is quality, so it's not a user value.


def test_insertContainer(global_stack):
    """Tests whether inserting a container is properly forbidden."""

    with pytest.raises(InvalidOperationError):
        global_stack.insertContainer(0, unittest.mock.MagicMock())


def test_removeContainer(global_stack):
    """Tests whether removing a container is properly forbidden."""

    with pytest.raises(InvalidOperationError):
        global_stack.removeContainer(unittest.mock.MagicMock())


def test_setNextStack(global_stack):
    """Tests whether changing the next stack is properly forbidden."""

    with pytest.raises(InvalidOperationError):
        global_stack.setNextStack(unittest.mock.MagicMock())


##  Tests setting properties directly on the global stack.
@pytest.mark.parametrize("key,              property,         value", [
                        ("layer_height",    "value",          0.1337),
                        ("foo",             "value",          100),
                        ("support_enabled", "value",          True),
                        ("layer_height",    "default_value",  0.1337),
                        ("layer_height",    "is_bright_pink", "of course")
])
def test_setPropertyUser(key, property, value, global_stack):
    user_changes = unittest.mock.MagicMock()
    user_changes.getMetaDataEntry = unittest.mock.MagicMock(return_value = "user")
    global_stack.userChanges = user_changes

    global_stack.setProperty(key, property, value)  # The actual test.

    # Make sure that the user container gets a setProperty call.
    global_stack.userChanges.setProperty.assert_called_once_with(key, property, value, None, False)