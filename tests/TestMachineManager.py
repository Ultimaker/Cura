from unittest.mock import MagicMock, patch

import pytest

from UM.Settings.ContainerRegistry import ContainerRegistry
from cura.Settings.ExtruderManager import ExtruderManager
from cura.Settings.MachineManager import MachineManager


@pytest.fixture()
def container_registry() -> ContainerRegistry:
    return MagicMock()

@pytest.fixture()
def extruder_manager(application, container_registry) -> ExtruderManager:
    with patch("cura.CuraApplication.CuraApplication.getInstance", MagicMock(return_value=application)):
        with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
                manager = ExtruderManager()
    return manager

@pytest.fixture()
def machine_manager(application, extruder_manager, container_registry) -> MachineManager:
    application.getExtruderManager = MagicMock(return_value = extruder_manager)
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

