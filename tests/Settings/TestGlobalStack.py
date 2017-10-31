# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import pytest #This module contains unit tests.
import unittest.mock #To monkeypatch some mocks in place of dependencies.

import cura.Settings.GlobalStack #The module we're testing.
import cura.Settings.CuraContainerStack #To get the list of container types.
from cura.Settings.Exceptions import TooManyExtrudersError, InvalidContainerError, InvalidOperationError #To test raising these errors.
from UM.Settings.DefinitionContainer import DefinitionContainer #To test against the class DefinitionContainer.
from UM.Settings.InstanceContainer import InstanceContainer #To test against the class InstanceContainer.
from UM.Settings.SettingInstance import InstanceState
import UM.Settings.ContainerRegistry
import UM.Settings.ContainerStack
import UM.Settings.SettingDefinition #To add settings to the definition.

##  Fake container registry that always provides all containers you ask of.
@pytest.yield_fixture()
def container_registry():
    registry = unittest.mock.MagicMock()
    registry.return_value = unittest.mock.NonCallableMagicMock()
    registry.findInstanceContainers = lambda *args, registry = registry, **kwargs: [registry.return_value]
    registry.findDefinitionContainers = lambda *args, registry = registry, **kwargs: [registry.return_value]

    UM.Settings.ContainerRegistry.ContainerRegistry._ContainerRegistry__instance = registry
    UM.Settings.ContainerStack._containerRegistry = registry

    yield registry

    UM.Settings.ContainerRegistry.ContainerRegistry._ContainerRegistry__instance = None
    UM.Settings.ContainerStack._containerRegistry = None

#An empty global stack to test with.
@pytest.fixture()
def global_stack() -> cura.Settings.GlobalStack.GlobalStack:
    return cura.Settings.GlobalStack.GlobalStack("TestStack")

##  Gets an instance container with a specified container type.
#
#   \param container_type The type metadata for the instance container.
#   \return An instance container instance.
def getInstanceContainer(container_type) -> InstanceContainer:
    container = InstanceContainer(container_id = "InstanceContainer")
    container.addMetaDataEntry("type", container_type)
    return container

class DefinitionContainerSubClass(DefinitionContainer):
    def __init__(self):
        super().__init__(container_id = "SubDefinitionContainer")

class InstanceContainerSubClass(InstanceContainer):
    def __init__(self, container_type):
        super().__init__(container_id = "SubInstanceContainer")
        self.addMetaDataEntry("type", container_type)

#############################START OF TEST CASES################################

##  Tests whether adding a container is properly forbidden.
def test_addContainer(global_stack):
    with pytest.raises(InvalidOperationError):
        global_stack.addContainer(unittest.mock.MagicMock())

##  Tests adding extruders to the global stack.
def test_addExtruder(global_stack):
    mock_definition = unittest.mock.MagicMock()
    mock_definition.getProperty = lambda key, property: 2 if key == "machine_extruder_count" and property == "value" else None

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

##  Tests getting the approximate material diameter.
@pytest.mark.parametrize("diameter, approximate_diameter", [
    #Some real-life cases that are common in printers.
    (2.85, 3),
    (1.75, 2),
    (3.0, 3),
    (2.0, 2),
    #Exceptional cases.
    (0, 0),
    (-10.1, -10),
    (-1, -1),
    (9000.1, 9000)
])
def test_approximateMaterialDiameter(diameter, approximate_diameter, global_stack):
    global_stack.definition = DefinitionContainer(container_id = "TestDefinition")
    material_diameter = UM.Settings.SettingDefinition.SettingDefinition(key = "material_diameter", container = global_stack.definition)
    material_diameter.addSupportedProperty("value", UM.Settings.SettingDefinition.DefinitionPropertyType.Any, default = diameter)
    global_stack.definition.definitions.append(material_diameter)
    assert float(global_stack.approximateMaterialDiameter) == approximate_diameter

##  Tests getting the material diameter when there is no material diameter.
def test_approximateMaterialDiameterNoDiameter(global_stack):
    global_stack.definition = DefinitionContainer(container_id = "TestDefinition")
    assert global_stack.approximateMaterialDiameter == "-1"

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
def test_constrainVariantInvalid(container, global_stack):
    with pytest.raises(InvalidContainerError): #Invalid container, should raise an error.
        global_stack.definition = container

#Test setting definitions.
@pytest.mark.parametrize("container", [
    DefinitionContainer(container_id = "DefinitionContainer"),
    DefinitionContainerSubClass()
])
def test_constrainDefinitionValid(container, global_stack):
    global_stack.definition = container #Should not give an error.

##  Tests whether deserialising completes the missing containers with empty
#   ones.
@pytest.mark.skip #The test currently fails because the definition container doesn't have a category, which is wrong but we don't have time to refactor that right now.
def test_deserializeCompletesEmptyContainers(global_stack: cura.Settings.GlobalStack):
    global_stack._containers = [DefinitionContainer(container_id = "definition")] #Set the internal state of this stack manually.

    with unittest.mock.patch("UM.Settings.ContainerStack.ContainerStack.deserialize", unittest.mock.MagicMock()): #Prevent calling super().deserialize.
        global_stack.deserialize("")

    assert len(global_stack.getContainers()) == len(cura.Settings.CuraContainerStack._ContainerIndexes.IndexTypeMap) #Needs a slot for every type.
    for container_type_index in cura.Settings.CuraContainerStack._ContainerIndexes.IndexTypeMap:
        if container_type_index == cura.Settings.CuraContainerStack._ContainerIndexes.Definition: #We're not checking the definition.
            continue
        assert global_stack.getContainer(container_type_index).getId() == "empty" #All others need to be empty.

##  Tests whether an instance container with the wrong type gets removed when
#   deserialising.
def test_deserializeRemovesWrongInstanceContainer(global_stack):
    global_stack._containers[cura.Settings.CuraContainerStack._ContainerIndexes.Quality] = getInstanceContainer(container_type = "wrong type")
    global_stack._containers[cura.Settings.CuraContainerStack._ContainerIndexes.Definition] = DefinitionContainer(container_id = "some definition")

    with unittest.mock.patch("UM.Settings.ContainerStack.ContainerStack.deserialize", unittest.mock.MagicMock()): #Prevent calling super().deserialize.
        global_stack.deserialize("")

    assert global_stack.quality == global_stack._empty_instance_container #Replaced with empty.

##  Tests whether a container with the wrong class gets removed when
#   deserialising.
def test_deserializeRemovesWrongContainerClass(global_stack):
    global_stack._containers[cura.Settings.CuraContainerStack._ContainerIndexes.Quality] = DefinitionContainer(container_id = "wrong class")
    global_stack._containers[cura.Settings.CuraContainerStack._ContainerIndexes.Definition] = DefinitionContainer(container_id = "some definition")

    with unittest.mock.patch("UM.Settings.ContainerStack.ContainerStack.deserialize", unittest.mock.MagicMock()): #Prevent calling super().deserialize.
        global_stack.deserialize("")

    assert global_stack.quality == global_stack._empty_instance_container #Replaced with empty.

##  Tests whether an instance container in the definition spot results in an
#   error.
def test_deserializeWrongDefinitionClass(global_stack):
    global_stack._containers[cura.Settings.CuraContainerStack._ContainerIndexes.Definition] = getInstanceContainer(container_type = "definition") #Correct type but wrong class.

    with unittest.mock.patch("UM.Settings.ContainerStack.ContainerStack.deserialize", unittest.mock.MagicMock()): #Prevent calling super().deserialize.
        with pytest.raises(UM.Settings.ContainerStack.InvalidContainerStackError): #Must raise an error that there is no definition container.
            global_stack.deserialize("")

##  Tests whether an instance container with the wrong type is moved into the
#   correct slot by deserialising.
def test_deserializeMoveInstanceContainer(global_stack):
    global_stack._containers[cura.Settings.CuraContainerStack._ContainerIndexes.Quality] = getInstanceContainer(container_type = "material") #Not in the correct spot.
    global_stack._containers[cura.Settings.CuraContainerStack._ContainerIndexes.Definition] = DefinitionContainer(container_id = "some definition")

    with unittest.mock.patch("UM.Settings.ContainerStack.ContainerStack.deserialize", unittest.mock.MagicMock()): #Prevent calling super().deserialize.
        global_stack.deserialize("")

    assert global_stack.quality.getId() == "empty"
    assert global_stack.material.getId() != "empty"

##  Tests whether a definition container in the wrong spot is moved into the
#   correct spot by deserialising.
@pytest.mark.skip #The test currently fails because the definition container doesn't have a category, which is wrong but we don't have time to refactor that right now.
def test_deserializeMoveDefinitionContainer(global_stack):
    global_stack._containers[cura.Settings.CuraContainerStack._ContainerIndexes.Material] = DefinitionContainer(container_id = "some definition") #Not in the correct spot.

    with unittest.mock.patch("UM.Settings.ContainerStack.ContainerStack.deserialize", unittest.mock.MagicMock()): #Prevent calling super().deserialize.
        global_stack.deserialize("")

    assert global_stack.material.getId() == "empty"
    assert global_stack.definition.getId() != "empty"

    UM.Settings.ContainerStack._containerRegistry = None

##  Tests whether getProperty properly applies the stack-like behaviour on its
#   containers.
def test_getPropertyFallThrough(global_stack):
    #A few instance container mocks to put in the stack.
    mock_layer_heights = {} #For each container type, a mock container that defines layer height to something unique.
    mock_no_settings = {} #For each container type, a mock container that has no settings at all.
    container_indexes = cura.Settings.CuraContainerStack._ContainerIndexes #Cache.
    for type_id, type_name in container_indexes.IndexTypeMap.items():
        container = unittest.mock.MagicMock()
        container.getProperty = lambda key, property, type_id = type_id: type_id if (key == "layer_height" and property == "value") else None #Returns the container type ID as layer height, in order to identify it.
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

##  In definitions, test whether having no resolve allows us to find the value.
def test_getPropertyNoResolveInDefinition(global_stack):
    value = unittest.mock.MagicMock() #Just sets the value for bed temperature.
    value.getProperty = lambda key, property: 10 if (key == "material_bed_temperature" and property == "value") else None

    with unittest.mock.patch("cura.Settings.CuraContainerStack.DefinitionContainer", unittest.mock.MagicMock): #To guard against the type checking.
        global_stack.definition = value
    assert global_stack.getProperty("material_bed_temperature", "value") == 10 #No resolve, so fall through to value.

##  In definitions, when the value is asked and there is a resolve function, it
#   must get the resolve first.
def test_getPropertyResolveInDefinition(global_stack):
    resolve_and_value = unittest.mock.MagicMock() #Sets the resolve and value for bed temperature.
    resolve_and_value.getProperty = lambda key, property: (7.5 if property == "resolve" else 5) if (key == "material_bed_temperature" and property in ("resolve", "value")) else None #7.5 resolve, 5 value.

    with unittest.mock.patch("cura.Settings.CuraContainerStack.DefinitionContainer", unittest.mock.MagicMock): #To guard against the type checking.
        global_stack.definition = resolve_and_value
    assert global_stack.getProperty("material_bed_temperature", "value") == 7.5 #Resolve wins in the definition.

##  In instance containers, when the value is asked and there is a resolve
#   function, it must get the value first.
def test_getPropertyResolveInInstance(global_stack):
    container_indices = cura.Settings.CuraContainerStack._ContainerIndexes
    instance_containers = {}
    for container_type in container_indices.IndexTypeMap:
        instance_containers[container_type] = unittest.mock.MagicMock() #Sets the resolve and value for bed temperature.
        instance_containers[container_type].getProperty = lambda key, property: (7.5 if property == "resolve" else (InstanceState.User if property == "state" else (5 if property != "limit_to_extruder" else "-1"))) if (key == "material_bed_temperature") else None #7.5 resolve, 5 value.
        instance_containers[container_type].getMetaDataEntry = unittest.mock.MagicMock(return_value = container_indices.IndexTypeMap[container_type]) #Make queries for the type return the desired type.
    instance_containers[container_indices.Definition].getProperty = lambda key, property: 10 if (key == "material_bed_temperature" and property == "value") else None #Definition only has value.
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

##  Tests whether the value in instances gets evaluated before the resolve in
#   definitions.
def test_getPropertyInstancesBeforeResolve(global_stack):
    value = unittest.mock.MagicMock() #Sets just the value.
    value.getProperty = lambda key, property: (10 if property == "value" else (InstanceState.User if property != "limit_to_extruder" else "-1")) if key == "material_bed_temperature" else None
    value.getMetaDataEntry = unittest.mock.MagicMock(return_value = "quality")
    resolve = unittest.mock.MagicMock() #Sets just the resolve.
    resolve.getProperty = lambda key, property: 7.5 if (key == "material_bed_temperature" and property == "resolve") else None

    with unittest.mock.patch("cura.Settings.CuraContainerStack.DefinitionContainer", unittest.mock.MagicMock): #To guard against the type checking.
        global_stack.definition = resolve
    global_stack.quality = value

    assert global_stack.getProperty("material_bed_temperature", "value") == 10

##  Tests whether the hasUserValue returns true for settings that are changed in
#   the user-changes container.
def test_hasUserValueUserChanges(global_stack):
    container = unittest.mock.MagicMock()
    container.getMetaDataEntry = unittest.mock.MagicMock(return_value = "user")
    container.hasProperty = lambda key, property: key == "layer_height" #Only have the layer_height property set.
    global_stack.userChanges = container

    assert global_stack.hasUserValue("layer_height")
    assert not global_stack.hasUserValue("infill_sparse_density")
    assert not global_stack.hasUserValue("")

##  Tests whether the hasUserValue returns true for settings that are changed in
#   the quality-changes container.
def test_hasUserValueQualityChanges(global_stack):
    container = unittest.mock.MagicMock()
    container.getMetaDataEntry = unittest.mock.MagicMock(return_value = "quality_changes")
    container.hasProperty = lambda key, property: key == "layer_height" #Only have the layer_height property set.
    global_stack.qualityChanges = container

    assert global_stack.hasUserValue("layer_height")
    assert not global_stack.hasUserValue("infill_sparse_density")
    assert not global_stack.hasUserValue("")

##  Tests whether a container in some other place on the stack is correctly not
#   recognised as user value.
def test_hasNoUserValue(global_stack):
    container = unittest.mock.MagicMock()
    container.getMetaDataEntry = unittest.mock.MagicMock(return_value = "quality")
    container.hasProperty = lambda key, property: key == "layer_height" #Only have the layer_height property set.
    global_stack.quality = container

    assert not global_stack.hasUserValue("layer_height") #However this container is quality, so it's not a user value.

##  Tests whether inserting a container is properly forbidden.
def test_insertContainer(global_stack):
    with pytest.raises(InvalidOperationError):
        global_stack.insertContainer(0, unittest.mock.MagicMock())

##  Tests whether removing a container is properly forbidden.
def test_removeContainer(global_stack):
    with pytest.raises(InvalidOperationError):
        global_stack.removeContainer(unittest.mock.MagicMock())

##  Tests setting definitions by specifying an ID of a definition that exists.
def test_setDefinitionByIdExists(global_stack, container_registry):
    container_registry.return_value = DefinitionContainer(container_id = "some_definition")
    global_stack.setDefinitionById("some_definition")
    assert global_stack.definition.getId() == "some_definition"

##  Tests setting definitions by specifying an ID of a definition that doesn't
#   exist.
def test_setDefinitionByIdDoesntExist(global_stack):
    with pytest.raises(InvalidContainerError):
        global_stack.setDefinitionById("some_definition") #Container registry is empty now.

##  Tests setting definition changes by specifying an ID of a container that
#   exists.
def test_setDefinitionChangesByIdExists(global_stack, container_registry):
    container_registry.return_value = getInstanceContainer(container_type = "definition_changes")
    global_stack.setDefinitionChangesById("InstanceContainer")
    assert global_stack.definitionChanges.getId() == "InstanceContainer"

##  Tests setting definition changes by specifying an ID of a container that
#   doesn't exist.
def test_setDefinitionChangesByIdDoesntExist(global_stack):
    with pytest.raises(InvalidContainerError):
        global_stack.setDefinitionChangesById("some_definition_changes") #Container registry is empty now.

##  Tests setting materials by specifying an ID of a material that exists.
def test_setMaterialByIdExists(global_stack, container_registry):
    container_registry.return_value = getInstanceContainer(container_type = "material")
    global_stack.setMaterialById("InstanceContainer")
    assert global_stack.material.getId() == "InstanceContainer"

##  Tests setting materials by specifying an ID of a material that doesn't
#   exist.
def test_setMaterialByIdDoesntExist(global_stack):
    with pytest.raises(InvalidContainerError):
        global_stack.setMaterialById("some_material") #Container registry is empty now.

##  Tests whether changing the next stack is properly forbidden.
def test_setNextStack(global_stack):
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

    global_stack.setProperty(key, property, value) #The actual test.

    global_stack.userChanges.setProperty.assert_called_once_with(key, property, value) #Make sure that the user container gets a setProperty call.

##  Tests setting properties on specific containers on the global stack.
@pytest.mark.parametrize("target_container,    stack_variable", [
                        ("user",               "userChanges"),
                        ("quality_changes",    "qualityChanges"),
                        ("quality",            "quality"),
                        ("material",           "material"),
                        ("variant",            "variant"),
                        ("definition_changes", "definitionChanges")
])
def test_setPropertyOtherContainers(target_container, stack_variable, global_stack):
    #Other parameters that don't need to be varied.
    key = "layer_height"
    property = "value"
    value = 0.1337
    #A mock container in the right spot.
    container = unittest.mock.MagicMock()
    container.getMetaDataEntry = unittest.mock.MagicMock(return_value = target_container)
    setattr(global_stack, stack_variable, container) #For instance, set global_stack.qualityChanges = container.

    global_stack.setProperty(key, property, value, target_container = target_container) #The actual test.

    getattr(global_stack, stack_variable).setProperty.assert_called_once_with(key, property, value) #Make sure that the proper container gets a setProperty call.

##  Tests setting qualities by specifying an ID of a quality that exists.
def test_setQualityByIdExists(global_stack, container_registry):
    container_registry.return_value = getInstanceContainer(container_type = "quality")
    global_stack.setQualityById("InstanceContainer")
    assert global_stack.quality.getId() == "InstanceContainer"

##  Tests setting qualities by specifying an ID of a quality that doesn't exist.
def test_setQualityByIdDoesntExist(global_stack):
    with pytest.raises(InvalidContainerError):
        global_stack.setQualityById("some_quality") #Container registry is empty now.

##  Tests setting quality changes by specifying an ID of a quality change that
#   exists.
def test_setQualityChangesByIdExists(global_stack, container_registry):
    container_registry.return_value = getInstanceContainer(container_type = "quality_changes")
    global_stack.setQualityChangesById("InstanceContainer")
    assert global_stack.qualityChanges.getId() == "InstanceContainer"

##  Tests setting quality changes by specifying an ID of a quality change that
#   doesn't exist.
def test_setQualityChangesByIdDoesntExist(global_stack):
    with pytest.raises(InvalidContainerError):
        global_stack.setQualityChangesById("some_quality_changes") #Container registry is empty now.

##  Tests setting variants by specifying an ID of a variant that exists.
def test_setVariantByIdExists(global_stack, container_registry):
    container_registry.return_value = getInstanceContainer(container_type = "variant")
    global_stack.setVariantById("InstanceContainer")
    assert global_stack.variant.getId() == "InstanceContainer"

##  Tests setting variants by specifying an ID of a variant that doesn't exist.
def test_setVariantByIdDoesntExist(global_stack):
    with pytest.raises(InvalidContainerError):
        global_stack.setVariantById("some_variant") #Container registry is empty now.

##  Smoke test for findDefaultVariant
def test_smoke_findDefaultVariant(global_stack):
    global_stack.findDefaultVariant()

##  Smoke test for findDefaultMaterial
def test_smoke_findDefaultMaterial(global_stack):
    global_stack.findDefaultMaterial()

##  Smoke test for findDefaultQuality
def test_smoke_findDefaultQuality(global_stack):
    global_stack.findDefaultQuality()
