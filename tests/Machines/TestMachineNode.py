# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

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

metadata_dict_list = {
    "has_materials": "false",
    "has_variants": "true",
    "has_machine_quality": "true",
    "quality_definition": "test_quality_definition",
    "exclude_materials": ["excluded_material_1", "excluded_material_2"],
    "preferred_variant_name": ["beautiful_nozzle_0", "beautiful_nozzle_1"],
    "preferred_material": ["beautiful_material_0", "beautiful_material_1"],
    "preferred_quality_type": "beautiful_quality_type"
}


@pytest.fixture
def container_registry():
    result = MagicMock()
    result.findInstanceContainersMetadata = MagicMock(return_value = [{"id": "variant_1", "name": "Variant One", "quality_type": "normal"}, {"id": "variant_2", "name": "Variant Two", "quality_type": "great"}])
    result.findContainersMetadata = MagicMock(return_value = [metadata_dict])
    return result

@pytest.fixture
def container_registry_list():
    result = MagicMock()
    result.findInstanceContainersMetadata = MagicMock(return_value = [{"id": "variant_1", "name": "Variant One", "quality_type": "normal"}, {"id": "variant_2", "name": "Variant Two", "quality_type": "great"}])
    result.findContainersMetadata = MagicMock(return_value = [metadata_dict_list])
    return result

@pytest.fixture
def empty_machine_node():
    """Creates a machine node without anything underneath it. No sub-nodes.

    For testing stuff with machine nodes without testing _loadAll(). You'll need
    to add subnodes manually in your test.
    """

    empty_container_registry = MagicMock()
    empty_container_registry.findContainersMetadata = MagicMock(return_value = [metadata_dict])  # Still contain the MachineNode's own metadata for the constructor.
    empty_container_registry.findInstanceContainersMetadata = MagicMock(return_value = [])
    with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value = empty_container_registry)):
        with patch("cura.Machines.MachineNode.MachineNode._loadAll", MagicMock()):
            return MachineNode("machine_1")

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


def test_metadataPropertiesListPreferredVariantName(container_registry_list):
    """Tests that preferred_variant_name accepts a list, with index mapping to extruder position."""
    node = createMachineNode("machine_1", container_registry_list)

    assert node.preferred_variant_name == "beautiful_nozzle_0", "The property should return the first list item for backwards compatibility."
    assert node.preferredVariantName(0) == "beautiful_nozzle_0"
    assert node.preferredVariantName(1) == "beautiful_nozzle_1"
    assert node.preferredVariantName(2) == "beautiful_nozzle_0", "Position beyond list length should fall back to index 0."


def test_metadataPropertiesListPreferredMaterial(container_registry_list):
    """Tests that preferred_material accepts a list, with index mapping to extruder position."""
    node = createMachineNode("machine_1", container_registry_list)

    assert node.preferred_material == "beautiful_material_0", "The property should return the first list item for backwards compatibility."
    assert node.preferredMaterialName(0) == "beautiful_material_0"
    assert node.preferredMaterialName(1) == "beautiful_material_1"
    assert node.preferredMaterialName(2) == "beautiful_material_0", "Position beyond list length should fall back to index 0."


def test_preferredVariantNameByPositionFallback(container_registry):
    """Tests that preferredVariantName falls back to extruder 0 when the list is shorter than the requested position.

    A single string value in the definition produces a 1-element list, so any position > 0 falls back to [0].
    """
    node = createMachineNode("machine_1", container_registry)

    assert node.preferredVariantName(0) == metadata_dict["preferred_variant_name"]
    assert node.preferredVariantName(1) == metadata_dict["preferred_variant_name"], "Single-item list should fall back to index 0 for any position."
    assert node.preferredVariantName(5) == metadata_dict["preferred_variant_name"], "Single-item list should fall back to index 0 for any position."


def test_preferredMaterialNameByPositionFallback(container_registry):
    """Tests that preferredMaterialName falls back to extruder 0 when the list is shorter than the requested position.

    A single string value in the definition produces a 1-element list, so any position > 0 falls back to [0].
    """
    node = createMachineNode("machine_1", container_registry)

    assert node.preferredMaterialName(0) == metadata_dict["preferred_material"]
    assert node.preferredMaterialName(1) == metadata_dict["preferred_material"], "Single-item list should fall back to index 0 for any position."
    assert node.preferredMaterialName(5) == metadata_dict["preferred_material"], "Single-item list should fall back to index 0 for any position."


def test_getQualityGroupsBothExtrudersAvailable(empty_machine_node):
    """Test getting quality groups when there are quality profiles available for

    the requested configurations on two extruders.
    """

    # Prepare a tree inside the machine node.
    extruder_0_node = MagicMock(quality_type = "quality_type_1")
    extruder_1_node = MagicMock(quality_type = "quality_type_1")  # Same quality type, so this is the one that can be returned.
    empty_machine_node.variants = {
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
    empty_machine_node.global_qualities = {
        "quality_type_1": global_node
    }

    # Request the quality groups for the variants in the machine tree.
    result = empty_machine_node.getQualityGroups(["variant_1", "variant_2"], ["material_1", "material_2"], [True, True])

    assert "quality_type_1" in result, "This quality type was available for both extruders."
    assert result["quality_type_1"].node_for_global == global_node
    assert result["quality_type_1"].nodes_for_extruders[0] == extruder_0_node
    assert result["quality_type_1"].nodes_for_extruders[1] == extruder_1_node
    assert result["quality_type_1"].name == global_node.getMetaDataEntry("name", "Unnamed Profile")
    assert result["quality_type_1"].quality_type == "quality_type_1"


def test_getQualityGroupsAvailability(empty_machine_node):
    """Test the "is_available" flag on quality groups.

    If a profile is available for a quality type on an extruder but not on all
    extruders, there should be a quality group for it but it should not be made
    available.
    """

    # Prepare a tree inside the machine node.
    extruder_0_both = MagicMock(quality_type = "quality_type_both")  # This quality type is available for both extruders.
    extruder_1_both = MagicMock(quality_type = "quality_type_both")
    extruder_0_exclusive = MagicMock(quality_type = "quality_type_0")  # These quality types are only available on one of the extruders.
    extruder_1_exclusive = MagicMock(quality_type = "quality_type_1")
    empty_machine_node.variants = {
        "variant_1": MagicMock(
            materials = {
                "material_1": MagicMock(
                    qualities = {
                        "quality_0_both": extruder_0_both,
                        "quality_0_exclusive": extruder_0_exclusive
                    }
                )
            }
        ),
        "variant_2": MagicMock(
            materials = {
                "material_2": MagicMock(
                    qualities = {
                        "quality_1_both": extruder_1_both,
                        "quality_1_exclusive": extruder_1_exclusive
                    }
                )
            }
        )
    }
    global_both = MagicMock(container = MagicMock(id = "global_quality_both"), getMetaDataEntry = lambda _, __: "Global Quality Both")
    global_0 = MagicMock(container = MagicMock(id = "global_quality_0"), getMetaDataEntry = lambda _, __: "Global Quality 0 Exclusive")
    global_1 = MagicMock(container = MagicMock(id = "global_quality_1"), getMetaDataEntry = lambda _, __: "Global Quality 1 Exclusive")
    empty_machine_node.global_qualities = {
        "quality_type_both": global_both,
        "quality_type_0": global_0,
        "quality_type_1": global_1
    }

    # Request the quality groups for the variants in the machine tree.
    result = empty_machine_node.getQualityGroups(["variant_1", "variant_2"], ["material_1", "material_2"], [True, True])

    assert "quality_type_both" in result, "This quality type was available on both extruders."
    assert result["quality_type_both"].is_available, "This quality type was available on both extruders and thus should be made available."
    assert "quality_type_0" in result, "This quality type was available for one of the extruders, and so there must be a group for it (even though it's unavailable)."
    assert not result["quality_type_0"].is_available, "This quality type was only available for one of the extruders and thus can't be activated."
    assert "quality_type_1" in result, "This quality type was available for one of the extruders, and so there must be a group for it (even though it's unavailable)."
    assert not result["quality_type_1"].is_available, "This quality type was only available for one of the extruders and thus can't be activated."