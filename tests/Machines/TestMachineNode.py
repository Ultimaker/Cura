from unittest.mock import patch, MagicMock
import pytest

from UM.Settings.Interfaces import ContainerInterface
from cura.Machines.MachineNode import MachineNode

metadata_dict = {
    "has_materials": "false",
    "has_variants": "true",
    "has_machine_quality": "true",
    "quality_definition": "test_quality_definition",
    "exclude_materials": ["excluded_material_1", "excluded_material_2"],
    "preferred_variant_name": "beautiful_nozzle",
    "preferred_material": "beautiful_material",
    "preferred_quality_type": "beautiful_quality_type"
}


@pytest.fixture
def container_registry():
    result = MagicMock()
    result.findInstanceContainersMetadata = MagicMock(return_value = [{"id": "variant_1", "name": "Variant One", "quality_type": "normal"}, {"id": "variant_2", "name": "Variant Two", "quality_type": "great"}])
    result.findContainersMetadata = MagicMock(return_value = [metadata_dict])
    return result


def getMetadataEntrySideEffect(*args, **kwargs):
    return metadata_dict.get(args[0])


def createMockedInstanceContainer():
    result = MagicMock(spec = ContainerInterface)
    result.getMetaDataEntry = MagicMock(side_effect = getMetadataEntrySideEffect)
    return result


def createMachineNode(container_id, container_registry):
    with patch("cura.Machines.MachineNode.VariantNode"):  # We're not testing the variant node here, so patch it out.
        with patch("cura.Machines.MachineNode.QualityNode"):
            with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value = container_registry)):
                return MachineNode(container_id)


def test_machineNodeInit(container_registry):
    machine_node = createMachineNode("machine_1", container_registry)

    # As variants get stored by name, we want to check if those get added.
    assert "Variant One" in machine_node.variants
    assert "Variant Two" in machine_node.variants
    assert len(machine_node.variants) == 2  # And ensure that *only* those two got added.

def test_metadataProperties(container_registry):
    node = createMachineNode("machine_1", container_registry)

    # Check if each of the metadata entries got stored properly.
    assert not node.has_materials
    assert node.has_variants
    assert node.has_machine_quality
    assert node.quality_definition == metadata_dict["quality_definition"]
    assert node.exclude_materials == metadata_dict["exclude_materials"]
    assert node.preferred_variant_name == metadata_dict["preferred_variant_name"]
    assert node.preferred_material == metadata_dict["preferred_material"]
    assert node.preferred_quality_type == metadata_dict["preferred_quality_type"]