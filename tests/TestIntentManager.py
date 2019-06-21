from unittest.mock import MagicMock, patch

import pytest

from cura.Settings.IntentManager import IntentManager

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
    mocked_metadata = [{"id": "um3_aa4_pla_smooth", "GUID": "abcxyz", "definition": "ultimaker3", "variant": "AA 0.4", "material_id": "generic_pla", "intent_category": "smooth"},
                       {"id": "um3_aa4_pla_strong", "GUID": "defqrs", "definition": "ultimaker3", "variant": "AA 0.4", "material_id": "generic_pla", "intent_category": "strong"}]
    container_registry.findContainersMetadata = MagicMock(return_value=mocked_metadata)

    with patch("cura.CuraApplication.CuraApplication.getInstance", MagicMock(return_value=application)):
        with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
            categories = intent_manager.intentCategories("ultimaker3", "AA 0.4", "generic_pla")  # type:List[str]
            assert "default" in categories, "default should always be in categories"
            assert "strong" in categories, "strong should be in categories"
            assert "smooth" in categories, "smooth should be in categories"
