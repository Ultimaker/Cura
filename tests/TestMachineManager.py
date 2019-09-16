from unittest.mock import MagicMock, patch

import pytest

from cura.Settings.MachineManager import MachineManager


@pytest.fixture()
def global_stack():
    stack = MagicMock(name="Global Stack")
    stack.getId = MagicMock(return_value ="GlobalStack")
    return stack


@pytest.fixture()
def machine_manager(application, extruder_manager, container_registry, global_stack) -> MachineManager:
    application.getExtruderManager = MagicMock(return_value = extruder_manager)
    application.getGlobalContainerStack = MagicMock(return_value = global_stack)
    with patch("cura.Settings.CuraContainerRegistry.CuraContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
        manager = MachineManager(application)

    return manager


def test_setActiveMachine(machine_manager):
    registry = MagicMock()

    mocked_global_stack = MagicMock()

    mocked_global_stack.getId = MagicMock(return_value = "test_machine")
    registry.findContainerStacks = MagicMock(return_value = [mocked_global_stack])
    with patch("cura.Settings.CuraContainerRegistry.CuraContainerRegistry.getInstance", MagicMock(return_value=registry)):
        with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=registry)):
            machine_manager.setActiveMachine("test_machine")

            # Although we mocked the application away, we still want to know if it was notified about the attempted change.
            machine_manager._application.setGlobalContainerStack.assert_called_with(mocked_global_stack)


def test_getMachine():
    registry = MagicMock()
    mocked_global_stack = MagicMock()
    mocked_global_stack.getId = MagicMock(return_value="test_machine")
    mocked_global_stack.definition.getId = MagicMock(return_value = "test")
    registry.findContainerStacks = MagicMock(return_value=[mocked_global_stack])
    with patch("cura.Settings.CuraContainerRegistry.CuraContainerRegistry.getInstance", MagicMock(return_value=registry)):
        assert MachineManager.getMachine("test") == mocked_global_stack


def test_addMachine(machine_manager):
    registry = MagicMock()

    mocked_stack = MagicMock()
    mocked_stack.getId = MagicMock(return_value="newlyCreatedStack")
    mocked_create_machine = MagicMock(name="createMachine", return_value = mocked_stack)
    machine_manager.setActiveMachine = MagicMock()
    with patch("cura.Settings.CuraStackBuilder.CuraStackBuilder.createMachine", mocked_create_machine):
        with patch("cura.Settings.CuraContainerRegistry.CuraContainerRegistry.getInstance", MagicMock(return_value=registry)):
            machine_manager.addMachine("derp")
    machine_manager.setActiveMachine.assert_called_with("newlyCreatedStack")


def test_hasUserSettings(machine_manager, application):
    mocked_stack = application.getGlobalContainerStack()

    mocked_instance_container = MagicMock(name="UserSettingContainer")
    mocked_instance_container.getNumInstances = MagicMock(return_value = 12)
    mocked_stack.getTop = MagicMock(return_value = mocked_instance_container)

    assert machine_manager.numUserSettings == 12
    assert machine_manager.hasUserSettings


def test_totalNumberOfSettings(machine_manager):
    registry = MagicMock()
    mocked_definition = MagicMock()
    mocked_definition.getAllKeys = MagicMock(return_value = ["omg", "zomg", "foo"])
    registry.findDefinitionContainers = MagicMock(return_value = [mocked_definition])
    with patch("cura.Settings.CuraContainerRegistry.CuraContainerRegistry.getInstance", MagicMock(return_value=registry)):
        assert machine_manager.totalNumberOfSettings == 3


def createMockedExtruder(extruder_id):
    extruder = MagicMock()
    extruder.getId = MagicMock(return_value = extruder_id)
    return extruder


def createMockedInstanceContainer(instance_id, name = ""):
    instance = MagicMock()
    instance.getName = MagicMock(return_value = name)
    instance.getId = MagicMock(return_value=instance_id)
    return instance


def test_allActiveMaterialIds(machine_manager, extruder_manager):
    extruder_1 = createMockedExtruder("extruder_1")
    extruder_2 = createMockedExtruder("extruder_2")
    extruder_1.material = createMockedInstanceContainer("material_1")
    extruder_2.material = createMockedInstanceContainer("material_2")
    extruder_manager.getActiveExtruderStacks = MagicMock(return_value = [extruder_1, extruder_2])
    assert machine_manager.allActiveMaterialIds == {"extruder_1": "material_1", "extruder_2": "material_2"}


def test_activeVariantNames(machine_manager, extruder_manager):
    extruder_1 = createMockedExtruder("extruder_1")
    extruder_2 = createMockedExtruder("extruder_2")
    extruder_1.getMetaDataEntry = MagicMock(return_value = "0")
    extruder_2.getMetaDataEntry = MagicMock(return_value= "2")
    extruder_1.variant = createMockedInstanceContainer("variant_1", "variant_name_1")
    extruder_2.variant = createMockedInstanceContainer("variant_2", "variant_name_2")
    extruder_manager.getActiveExtruderStacks = MagicMock(return_value=[extruder_1, extruder_2])

    assert machine_manager.activeVariantNames == {"0": "variant_name_1", "2": "variant_name_2"}


def test_globalVariantName(machine_manager, application):
    global_stack = application.getGlobalContainerStack()
    global_stack.variant = createMockedInstanceContainer("beep", "zomg")
    assert machine_manager.globalVariantName == "zomg"


def test_activeMachineDefinitionName(machine_manager):
    global_stack = machine_manager.activeMachine
    global_stack.definition = createMockedInstanceContainer("beep", "zomg")
    assert machine_manager.activeMachineDefinitionName == "zomg"


def test_activeMachineId(machine_manager):
    assert machine_manager.activeMachineId == "GlobalStack"


def test_activeVariantBuildplateName(machine_manager):
    global_stack = machine_manager.activeMachine
    global_stack.variant = createMockedInstanceContainer("beep", "zomg")
    assert machine_manager.activeVariantBuildplateName == "zomg"


def test_resetSettingForAllExtruders(machine_manager):
    global_stack = machine_manager.activeMachine
    extruder_1 = createMockedExtruder("extruder_1")
    extruder_2 = createMockedExtruder("extruder_2")
    extruder_1.userChanges = createMockedInstanceContainer("settings_1")
    extruder_2.userChanges = createMockedInstanceContainer("settings_2")
    global_stack.extruderList = [extruder_1, extruder_2]

    machine_manager.resetSettingForAllExtruders("whatever")

    extruder_1.userChanges.removeInstance.assert_called_once_with("whatever")
    extruder_2.userChanges.removeInstance.assert_called_once_with("whatever")