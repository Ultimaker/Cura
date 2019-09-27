# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from unittest.mock import MagicMock, patch

import pytest
from typing import Any, Dict, List

from cura.Settings.IntentManager import IntentManager
from cura.Machines.QualityGroup import QualityGroup

from tests.Settings.MockContainer import MockContainer

mocked_intent_metadata = [
    {"id": "um3_aa4_pla_smooth_normal", "GUID": "abcxyz", "definition": "ultimaker3", "variant": "AA 0.4",
     "material_id": "generic_pla", "intent_category": "smooth", "quality_type": "normal"},
    {"id": "um3_aa4_pla_strong_abnorm", "GUID": "defqrs", "definition": "ultimaker3", "variant": "AA 0.4",
     "material_id": "generic_pla", "intent_category": "strong", "quality_type": "abnorm"}]  # type:List[Dict[str, str]]

mocked_qualitygroup_metadata = {
    "normal": QualityGroup("um3_aa4_pla_normal", "normal"),
    "abnorm": QualityGroup("um3_aa4_pla_abnorm", "abnorm")}  # type: Dict[str, QualityGroup]

@pytest.fixture
def mock_container_tree() -> MagicMock:
    container_tree = MagicMock()
    container_tree.getCurrentQualityGroups = MagicMock(return_value = mocked_qualitygroup_metadata)
    container_tree.machines = {
        "ultimaker3": MagicMock(
            variants = {
                "AA 0.4": MagicMock(
                    materials = {
                        "generic_pla": MagicMock(
                            qualities = {
                                "um3_aa4_pla_normal": MagicMock(
                                    quality_type = "normal",
                                    intents = {
                                        "smooth": MagicMock(
                                            intent_category = "smooth",
                                            getMetadata = MagicMock(return_value = mocked_intent_metadata[0])
                                        )
                                    }
                                ),
                                "um3_aa4_pla_abnorm": MagicMock(
                                    quality_type = "abnorm",
                                    intents = {
                                        "strong": MagicMock(
                                            intent_category = "strong",
                                            getMetadata = MagicMock(return_value = mocked_intent_metadata[1])
                                        )
                                    }
                                )
                            }
                        )
                    }
                )
            }
        )
    }
    return container_tree

@pytest.fixture
def intent_manager(application, extruder_manager, machine_manager, container_registry, global_stack) -> IntentManager:
    application.getExtruderManager = MagicMock(return_value = extruder_manager)
    application.getGlobalContainerStack = MagicMock(return_value = global_stack)
    application.getMachineManager = MagicMock(return_value = machine_manager)
    machine_manager.setIntentByCategory = MagicMock()
    with patch("cura.CuraApplication.CuraApplication.getInstance", MagicMock(return_value = application)):
        with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value = container_registry)):
            manager = IntentManager()
    return manager

def mockFindMetadata(**kwargs) -> List[Dict[str, Any]]:
    if "id" in kwargs:
        return [x for x in mocked_intent_metadata if x["id"] == kwargs["id"]]
    else:
        result = []
        for data in mocked_intent_metadata:
            should_add = True
            for key, value in kwargs.items():
                if key in data.keys():
                    should_add &= (data[key] == value)
            if should_add:
                result.append(data)
        return result


def mockFindContainers(**kwargs) -> List[MockContainer]:
    result = []
    metadatas = mockFindMetadata(**kwargs)
    for metadata in metadatas:
        result.append(MockContainer(metadata))
    return result


def doSetup(application, extruder_manager, container_registry, global_stack) -> None:
    container_registry.findContainersMetadata = MagicMock(side_effect = mockFindMetadata)
    container_registry.findContainers = MagicMock(side_effect = mockFindContainers)

    for qualitygroup in mocked_qualitygroup_metadata.values():
        qualitygroup.node_for_global = MagicMock(name = "Node for global")

    global_stack.definition = MockContainer({"id": "ultimaker3"})

    extruder_stack_a = MockContainer({"id": "Extruder The First"})
    extruder_stack_a.variant = MockContainer({"name": "AA 0.4"})
    extruder_stack_a.quality = MockContainer({"id": "um3_aa4_pla_normal"})
    extruder_stack_a.material = MockContainer({"base_file": "generic_pla"})
    extruder_stack_a.intent = MockContainer({"id": "empty_intent", "intent_category": "default"})
    extruder_stack_b = MockContainer({"id": "Extruder II: Plastic Boogaloo"})
    extruder_stack_b.variant = MockContainer({"name": "AA 0.4"})
    extruder_stack_b.quality = MockContainer({"id": "um3_aa4_pla_normal"})
    extruder_stack_b.material = MockContainer({"base_file": "generic_pla"})
    extruder_stack_b.intent = MockContainer({"id": "empty_intent", "intent_category": "default"})
    global_stack.extruderList = [extruder_stack_a, extruder_stack_b]

    application.getGlobalContainerStack = MagicMock(return_value = global_stack)
    extruder_manager.getUsedExtruderStacks = MagicMock(return_value = [extruder_stack_a, extruder_stack_b])


def test_intentCategories(intent_manager, mock_container_tree):
    with patch("cura.Machines.ContainerTree.ContainerTree.getInstance", MagicMock(return_value = mock_container_tree)):
        categories = intent_manager.intentCategories("ultimaker3", "AA 0.4", "generic_pla")  # type:List[str]
        assert "default" in categories, "default should always be in categories"
        assert "strong" in categories, "strong should be in categories"
        assert "smooth" in categories, "smooth should be in categories"


def test_getCurrentAvailableIntents(application, extruder_manager, intent_manager, container_registry, global_stack, mock_container_tree):
    doSetup(application, extruder_manager, container_registry, global_stack)

    with patch("cura.Machines.ContainerTree.ContainerTree.getInstance", MagicMock(return_value = mock_container_tree)):
        with patch("cura.CuraApplication.CuraApplication.getInstance", MagicMock(return_value = application)):
            with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value = container_registry)):
                intents = intent_manager.getCurrentAvailableIntents()
                assert ("smooth", "normal") in intents
                assert ("strong", "abnorm") in intents
                #assert ("default", "normal") in intents  # Pending to-do in 'IntentManager'.
                #assert ("default", "abnorm") in intents  # Pending to-do in 'IntentManager'.
                assert len(intents) == 2  # Or 4? pending to-do in 'IntentManager'.


def test_currentAvailableIntentCategories(application, extruder_manager, intent_manager, container_registry, global_stack, mock_container_tree):
    doSetup(application, extruder_manager, container_registry, global_stack)

    with patch("cura.Machines.ContainerTree.ContainerTree.getInstance", MagicMock(return_value = mock_container_tree)):
        with patch("cura.CuraApplication.CuraApplication.getInstance", MagicMock(return_value = application)):
            with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value = container_registry)):
                with patch("cura.Settings.ExtruderManager.ExtruderManager.getInstance", MagicMock(return_value = extruder_manager)):
                    categories = intent_manager.currentAvailableIntentCategories()
                    assert "default" in categories  # Currently inconsistent with 'currentAvailableIntents'!
                    assert "smooth" in categories
                    assert "strong" in categories
                    assert len(categories) == 3


def test_selectIntent(application, extruder_manager, intent_manager, container_registry, global_stack, mock_container_tree):
    doSetup(application, extruder_manager, container_registry, global_stack)

    with patch("cura.Machines.ContainerTree.ContainerTree.getInstance", MagicMock(return_value = mock_container_tree)):
        with patch("cura.CuraApplication.CuraApplication.getInstance", MagicMock(return_value = application)):
            with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value = container_registry)):
                with patch("cura.Settings.ExtruderManager.ExtruderManager.getInstance", MagicMock(return_value = extruder_manager)):
                    intents = intent_manager.getCurrentAvailableIntents()
                    for intent, quality in intents:
                        intent_manager.selectIntent(intent, quality)
                        extruder_stacks = extruder_manager.getUsedExtruderStacks()
                        assert len(extruder_stacks) == 2
                        assert extruder_stacks[0].intent.getMetaDataEntry("intent_category") == intent
                        assert extruder_stacks[1].intent.getMetaDataEntry("intent_category") == intent
