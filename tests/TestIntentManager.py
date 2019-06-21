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
def container_registry(application, global_stack) -> ContainerRegistry:
  result = MagicMock()
  mocked_metadata = [{"id": "um3_aa4_pla_smooth", "GUID": "abcxyz", "definition": "ultimaker3", "variant": "AA 0.4", "material_id": "generic_pla", "intent_category": "smooth"},
                     {"id": "um3_aa4_pla_strong", "GUID": "defqrs", "definition": "ultimaker3", "variant": "AA 0.4", "material_id": "generic_pla", "intent_category": "strong"}]
  result.findContainersMetadata = MagicMock(return_value = mocked_metadata)
  result.findContainerStacks = MagicMock(return_value = [global_stack])

  application.getContainerRegistry = MagicMock(return_value = result)

  return result

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
    with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
        manager = MachineManager(application)

    return manager

# TODO: maybe put some definitions above in common file because they copy the ones in TestMachineManager (also there).

@pytest.fixture()
def intent_manager(application, extruder_manager, machine_manager, container_registry, global_stack) -> IntentManager:
    application.getExtruderManager = MagicMock(return_value = extruder_manager)
    application.getGlobalContainerStack = MagicMock(return_value = global_stack)
    application.getMachineManager = MagicMock(return_value = machine_manager)
    with patch("cura.CuraApplication.CuraApplication.getInstance", MagicMock(return_value=application)):
        with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
            manager = IntentManager()

    return manager

def test_intentCategories(application, intent_manager, container_registry):
    with patch("cura.CuraApplication.CuraApplication.getInstance", MagicMock(return_value=application)):
        with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
            categories = intent_manager.intentCategories("ultimaker3", "AA 0.4", "generic_pla")  # type:List[str]
            assert "default" in categories, "default should always be in categories"
            assert "strong" in categories, "strong should be in categories"
            assert "smooth" in categories, "smooth should be in categories"
