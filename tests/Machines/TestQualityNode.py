from unittest.mock import patch, MagicMock
import pytest

from cura.Machines.MaterialNode import MaterialNode
from cura.Machines.QualityNode import QualityNode


instance_container_metadata_dict = {"fdmprinter": {"variant_1": {"material_1": [{"id": "intent_1"}, {"id": "intent_2"}]}},
                                    "machine_1": {"variant_2": {"material_2": [{"id": "intent_3"}, {"id": "intent_4"}]}}}


intent_metadata_intent_added_data = [({"type": "Not an intent"}, ["intent_3", "intent_4"]),  # Wrong type
                                    ({"type": "intent", "definition": "machine_9000"}, ["intent_3", "intent_4"]),  # wrong definition
                                    ({"type": "intent", "definition": "machine_1", "variant": "variant_299101"}, ["intent_3", "intent_4"]),  # wrong variant
                                    ({"type": "intent", "definition": "machine_1", "variant": "variant_2", "material": "super cool material!"}, ["intent_3", "intent_4"]),  # Wrong material
                                    ({"type": "intent", "definition": "machine_1", "variant": "variant_2", "material": "material_2"}, ["intent_3", "intent_4", "intent_9001"]),  # Yay, all good.
]

metadata_dict = {}


def getMetadataEntrySideEffect(*args, **kwargs):
    return metadata_dict.get(args[0])


def createMockedInstanceContainer(container_id):
    result = MagicMock()
    result.getId = MagicMock(return_value=container_id)
    result.getMetaDataEntry = MagicMock(side_effect=getMetadataEntrySideEffect)
    return result


def getInstanceContainerSideEffect(*args, **kwargs):

    definition_dict = instance_container_metadata_dict.get(kwargs["definition"])
    variant_dict = definition_dict.get(kwargs["variant"])
    return variant_dict.get(kwargs["material"])

@pytest.fixture
def container_registry():
    result = MagicMock()
    result.findInstanceContainersMetadata = MagicMock(side_effect=getInstanceContainerSideEffect)
    return result


def test_qualityNode_machine_1(container_registry):
    material_node = MagicMock()
    material_node.variant.machine.quality_definition = "machine_1"
    material_node.variant.variant_name = "variant_2"
    material_node.base_file = "material_2"

    with patch("cura.Machines.QualityNode.IntentNode"):
        with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
            node = QualityNode("quality_1", material_node)

    assert len(node.intents) == 2
    assert "intent_3" in node.intents
    assert "intent_4" in node.intents

@pytest.mark.parametrize("metadata,intent_result_list", intent_metadata_intent_added_data)
def test_intentNodeAdded(container_registry, metadata, intent_result_list):
    material_node = MagicMock()
    material_node.variant.machine.quality_definition = "machine_1"
    material_node.variant.variant_name = "variant_2"
    material_node.base_file = "material_2"

    intent_container = createMockedInstanceContainer("intent_9001")

    with patch("cura.Machines.QualityNode.IntentNode"):
        with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
            node = QualityNode("quality_1", material_node)
            with patch.dict(metadata_dict, metadata):
                node._intentAdded(intent_container)

    assert len(intent_result_list) == len(node.intents)
    for identifier in intent_result_list:
        assert identifier in node.intents

