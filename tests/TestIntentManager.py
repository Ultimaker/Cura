from unittest.mock import MagicMock, patch

import pytest
from typing import Any, Dict, List

from cura.Settings.IntentManager import IntentManager
from cura.Machines.QualityGroup import QualityGroup
from cura.Machines.QualityManager import QualityManager

from tests.Settings.MockContainer import MockContainer

@pytest.fixture()
def quality_manager(application, container_registry, global_stack) -> QualityManager:
    application.getGlobalContainerStack = MagicMock(return_value = global_stack)
    with patch("cura.CuraApplication.CuraApplication.getInstance", MagicMock(return_value=application)):
        with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
            manager = QualityManager(application)
    return manager


@pytest.fixture()
def intent_manager(application, extruder_manager, machine_manager, quality_manager, container_registry, global_stack) -> IntentManager:
    application.getExtruderManager = MagicMock(return_value = extruder_manager)
    application.getGlobalContainerStack = MagicMock(return_value = global_stack)
    application.getMachineManager = MagicMock(return_value = machine_manager)
    application.getQualityManager = MagicMock(return_value = quality_manager)
    with patch("cura.CuraApplication.CuraApplication.getInstance", MagicMock(return_value=application)):
        with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
            manager = IntentManager()
    return manager


mocked_intent_metadata = [
    {"id": "um3_aa4_pla_smooth_normal", "GUID": "abcxyz", "definition": "ultimaker3", "variant": "AA 0.4",
     "material_id": "generic_pla", "intent_category": "smooth", "quality_type": "normal"},
    {"id": "um3_aa4_pla_strong_abnorm", "GUID": "defqrs", "definition": "ultimaker3", "variant": "AA 0.4",
     "material_id": "generic_pla", "intent_category": "strong", "quality_type": "abnorm"}]  # type:List[Dict[str, str]]


def test_intentCategories(application, intent_manager, container_registry):
    # Mock .findContainersMetadata so we also test .intentMetadatas (the latter is mostly a wrapper around the former).
    container_registry.findContainersMetadata = MagicMock(return_value=mocked_intent_metadata)

    with patch("cura.CuraApplication.CuraApplication.getInstance", MagicMock(return_value=application)):
        with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
            categories = intent_manager.intentCategories("ultimaker3", "AA 0.4", "generic_pla")  # type:List[str]
            assert "default" in categories, "default should always be in categories"
            assert "strong" in categories, "strong should be in categories"
            assert "smooth" in categories, "smooth should be in categories"


def test_currentAvailableIntents(application, extruder_manager, quality_manager, intent_manager, container_registry):
    mocked_qualitygroup_metadata = {
        "normal": QualityGroup("um3_aa4_pla_normal", "normal"),
        "abnorm": QualityGroup("um3_aa4_pla_abnorm", "abnorm")}  # type:Dict[str, QualityGroup]

    def mockIntentMetadatas(**kwargs) -> List[Dict[str, Any]]:
        if "id" in kwargs:
            return [x for x in mocked_intent_metadata if x["id"] == kwargs["id"]]
        else:
            # TODO? switch on 'kwargs["definition_id"]', "nozzle_name", "material_id" -> ... or go 1 deeper
            return mocked_intent_metadata
    container_registry.findContainersMetadata = MagicMock(side_effect=mockIntentMetadatas)

    quality_manager.getQualityGroups = MagicMock(return_value=mocked_qualitygroup_metadata)
    for _, qualitygroup in mocked_qualitygroup_metadata.items():
        qualitygroup.node_for_global = MagicMock(name="Node for global")
    application.getQualityManager = MagicMock(return_value=quality_manager)

    extruder_stack_a = MockContainer({"id": "A"})
    extruder_stack_a.variant = MockContainer({"id": "A_variant"})
    extruder_stack_a.material = MockContainer({"id": "A_material"})
    extruder_stack_b = MockContainer({"id": "B"})
    extruder_stack_b.variant = MockContainer({"id": "B_variant"})
    extruder_stack_b.material = MockContainer({"id": "B_material"})
    # See previous TODO, the above doesn't really matter if intentmetadatas is mocked out the way it is, but it should.

    extruder_manager.getUsedExtruderStacks = MagicMock(return_value=[extruder_stack_a, extruder_stack_b])

    with patch("cura.CuraApplication.CuraApplication.getInstance", MagicMock(return_value=application)):
        with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
            with patch("cura.Settings.ExtruderManager.ExtruderManager.getInstance", MagicMock(return_value=extruder_manager)):
                intents = intent_manager.currentAvailableIntents()
                assert ("smooth", "normal") in intents
                assert ("strong", "abnorm") in intents
                assert len(intents) == 2


def test_currentAvailableIntentCategories(application, quality_manager, intent_manager, container_registry):
    # def currentAvailableIntentCategories(self) -> List[str]:
    pass


def test_selectIntent(application, intent_manager, container_registry):
    # def selectIntent(self, intent_category, quality_type) -> None:
    pass
