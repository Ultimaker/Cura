from unittest.mock import MagicMock, patch

import pytest

from UM.Settings.ContainerRegistry import ContainerRegistry
from cura.Settings.ExtruderManager import ExtruderManager
from cura.Settings.MachineManager import MachineManager


@pytest.fixture()
def global_stack():
    return MagicMock(name="Global Stack")

@pytest.fixture()
def container_registry() -> ContainerRegistry:
    return MagicMock(name = "ContainerRegistry")


@pytest.fixture()
def extruder_manager(application, container_registry) -> ExtruderManager:
    if ExtruderManager.getInstance() is not None:
        # Reset the data
        ExtruderManager._ExtruderManager__instance = None

    with patch("cura.CuraApplication.CuraApplication.getInstance", MagicMock(return_value=application)):
        with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
            manager = ExtruderManager()
    return manager


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
