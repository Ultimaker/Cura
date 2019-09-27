# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from unittest.mock import patch, MagicMock
import pytest

from cura.Machines.QualityNode import QualityNode

##  Metadata for hypothetical containers that get put in the registry.
metadatas = [
    {
        "id": "matching_intent",  # Matches our query.
        "type": "intent",
        "definition": "correct_definition",
        "variant": "correct_variant",
        "material": "correct_material",
        "quality_type": "correct_quality_type"
    },
    {
        "id": "matching_intent_2",  # Matches our query as well.
        "type": "intent",
        "definition": "correct_definition",
        "variant": "correct_variant",
        "material": "correct_material",
        "quality_type": "correct_quality_type"
    },
    {
        "id": "bad_type",
        "type": "quality",  # Doesn't match because it's not an intent.
        "definition": "correct_definition",
        "variant": "correct_variant",
        "material": "correct_material",
        "quality_type": "correct_quality_type"
    },
    {
        "id": "bad_definition",
        "type": "intent",
        "definition": "wrong_definition",  # Doesn't match on the definition.
        "variant": "correct_variant",
        "material": "correct_material",
        "quality_type": "correct_quality_type"
    },
    {
        "id": "bad_variant",
        "type": "intent",
        "definition": "correct_definition",
        "variant": "wrong_variant",  # Doesn't match on the variant.
        "material": "correct_material",
        "quality_type": "correct_quality_type"
    },
    {
        "id": "bad_material",
        "type": "intent",
        "definition": "correct_definition",
        "variant": "correct_variant",
        "material": "wrong_material",  # Doesn't match on the material.
        "quality_type": "correct_quality_type"
    },
    {
        "id": "bad_quality",
        "type": "intent",
        "definition": "correct_definition",
        "variant": "correct_variant",
        "material": "correct_material",
        "quality_type": "wrong_quality_type"  # Doesn't match on the quality type.
    },
    {
        "id": "quality_1",
        "quality_type": "correct_quality_type",
        "material": "correct_material"
    }
]

@pytest.fixture
def container_registry():
    result = MagicMock()
    def findContainersMetadata(**kwargs):
        return [metadata for metadata in metadatas if kwargs.items() <= metadata.items()]
    result.findContainersMetadata = findContainersMetadata
    result.findInstanceContainersMetadata = findContainersMetadata
    return result

def test_qualityNode_machine_1(container_registry):
    material_node = MagicMock()
    material_node.variant.machine.quality_definition = "correct_definition"
    material_node.variant.variant_name = "correct_variant"

    with patch("cura.Machines.QualityNode.IntentNode"):
        with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value = container_registry)):
            node = QualityNode("quality_1", material_node)

    assert len(node.intents) == 3
    assert "matching_intent" in node.intents
    assert "matching_intent_2" in node.intents
    assert "empty_intent" in node.intents