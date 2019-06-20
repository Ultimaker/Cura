from unittest.mock import MagicMock, patch

import pytest

from UM.Settings.ContainerRegistry import ContainerRegistry
from cura.Settings.ExtruderManager import ExtruderManager
from cura.Settings.MachineManager import MachineManager
from cura.Settings.IntentManager import IntentManager

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
