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

##  Test getting quality groups when there are quality profiles available for
#   the requested configurations on two extruders.
def test_getQualityGroupsBothExtrudersAvailable():
    # Create a machine node without constructing the tree beneath it. We don't want to depend on that for this test.
    empty_container_registry = MagicMock()
    empty_container_registry.findContainersMetadata = MagicMock(return_value = [metadata_dict])  # Still contain the MachineNode's own metadata for the constructor.
    empty_container_registry.findInstanceContainersMetadata = MagicMock(return_value = [])
    with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value = empty_container_registry)):
        with patch("cura.Machines.MachineNode.MachineNode._loadAll", MagicMock()):
            machine_node = MachineNode("machine_1")

    # Prepare a tree inside the machine node.
    extruder_0_node = MagicMock(quality_type = "quality_type_1")
    extruder_1_node = MagicMock(quality_type = "quality_type_1")  # Same quality type, so this is the one that can be returned.
    machine_node.variants = {
        "variant_1": MagicMock(
            materials = {
                "material_1": MagicMock(
                    qualities = {
                        "quality_1": extruder_0_node
                    }
                )
            }
        ),
        "variant_2": MagicMock(
            materials = {
                "material_2": MagicMock(
                    qualities = {
                        "quality_2": extruder_1_node
                    }
                )
            }
        )
    }
    global_node = MagicMock(
        container = MagicMock(id = "global_quality_container"),  # Needs to exist, otherwise it won't add this quality type.
        getMetaDataEntry = lambda _, __: "Global Quality Profile Name"
    )
    machine_node.global_qualities = {
        "quality_type_1": global_node
    }

    # Request the quality groups for the variants in the machine tree.
    result = machine_node.getQualityGroups(["variant_1", "variant_2"], ["material_1", "material_2"], [True, True])

    assert "quality_type_1" in result, "This quality type was available for both extruders."
    assert result["quality_type_1"].node_for_global == global_node
    assert result["quality_type_1"].nodes_for_extruders[0] == extruder_0_node
    assert result["quality_type_1"].nodes_for_extruders[1] == extruder_1_node
    assert result["quality_type_1"].name == global_node.getMetaDataEntry("name", "Unnamed Profile")
    assert result["quality_type_1"].quality_type == "quality_type_1"