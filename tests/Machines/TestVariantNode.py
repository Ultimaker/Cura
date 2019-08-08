from unittest.mock import patch, MagicMock
import pytest

from cura.Machines.VariantNode import VariantNode
import copy

instance_container_metadata_dict = {"fdmprinter": {"no_variant": [{"base_file": "material_1", "id": "material_1"}, {"base_file": "material_2", "id": "material_2"}]},
                 "machine_1": {"no_variant": [{"base_file": "material_1", "id": "material_1"}, {"base_file": "material_2", "id": "material_2"}],
                               "Variant One": [{"base_file": "material_1", "id": "material_1"}, {"base_file": "material_2", "id": "material_2"}]}}


material_node_added_test_data = [({"type": "Not a material"}, ["material_1", "material_2"]), # Wrong type
                                 ({"type": "material", "base_file": "material_3"}, ["material_1", "material_2"]),  # material_3 is on the "NOPE" list.
                                 ({"type": "material", "base_file": "material_4", "definition": "machine_3"}, ["material_1", "material_2"]),  # Wrong machine
                                 ({"type": "material", "base_file": "material_4", "definition": "machine_1"}, ["material_1", "material_2"]), # No variant
                                 ({"type": "material", "base_file": "material_4", "definition": "machine_1", "variant": "Variant Three"}, ["material_1", "material_2"]), # Wrong variant
                                 ({"type": "material", "base_file": "material_4", "definition": "machine_1", "variant": "Variant One"}, ["material_1", "material_2", "material_4"])
                                 ]

material_node_update_test_data = [({"type": "material", "base_file": "material_1", "definition": "machine_1", "variant": "Variant One"}, ["material_1"], ["material_2"]),
                                  ({"type": "material", "base_file": "material_1", "definition": "fdmprinter", "variant": "Variant One"}, [], ["material_2", "material_1"]),  # Too generic
                                  ({"type": "material", "base_file": "material_1", "definition": "machine_2", "variant": "Variant One"}, [], ["material_2", "material_1"])   # Wrong definition
                                  ]

metadata_dict = {}


def getMetadataEntrySideEffect(*args, **kwargs):
    return metadata_dict.get(args[0])


def getInstanceContainerSideEffect(*args, **kwargs):
    variant = kwargs.get("variant")
    definition = kwargs.get("definition")

    if variant is not None:
        return instance_container_metadata_dict.get(definition).get(variant)
    return instance_container_metadata_dict.get(definition).get("no_variant")


@pytest.fixture
def machine_node():
    mocked_machine_node = MagicMock()
    mocked_machine_node.container_id = "machine_1"
    return mocked_machine_node


@pytest.fixture
def container_registry():
    result = MagicMock()
    result.findInstanceContainersMetadata = MagicMock(side_effect = getInstanceContainerSideEffect)
    result.findContainersMetadata = MagicMock(return_value = [{"name": "Variant One"}])
    return result


def createMockedInstanceContainer():
    result = MagicMock()
    result.getMetaDataEntry = MagicMock(side_effect=getMetadataEntrySideEffect)
    return result


def createVariantNode(container_id, machine_node, container_registry):
    with patch("cura.Machines.VariantNode.MaterialNode"):  # We're not testing the material node here, so patch it out.
        with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
            return VariantNode(container_id, machine_node)


def test_variantNodeInit(container_registry, machine_node):
    node = createVariantNode("variant_1", machine_node, container_registry)

    assert "material_1" in node.materials
    assert "material_2" in node.materials
    assert len(node.materials) == 2


def test_variantNodeInit_excludedMaterial(container_registry, machine_node):
    machine_node.exclude_materials = ["material_1"]
    node = createVariantNode("variant_1", machine_node, container_registry)

    assert "material_1" not in node.materials
    assert "material_2" in node.materials
    assert len(node.materials) == 1


@pytest.mark.parametrize("metadata,material_result_list", material_node_added_test_data)
def test_materialAdded(container_registry, machine_node, metadata, material_result_list):
    variant_node = createVariantNode("machine_1", machine_node, container_registry)
    machine_node.exclude_materials = ["material_3"]
    with patch("cura.Machines.VariantNode.MaterialNode"):  # We're not testing the material node here, so patch it out.
        with patch.dict(metadata_dict, metadata):
            mocked_container = createMockedInstanceContainer()
            variant_node._materialAdded(mocked_container)

    assert len(material_result_list) == len(variant_node.materials)
    for name in material_result_list:
        assert name in variant_node.materials

@pytest.mark.parametrize("metadata,changed_material_list,unchanged_material_list", material_node_update_test_data)
def test_materialAdded_update(container_registry, machine_node, metadata,changed_material_list, unchanged_material_list):
    variant_node = createVariantNode("machine_1", machine_node, container_registry)
    original_material_nodes = copy.copy(variant_node.materials)

    with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
        with patch("cura.Machines.VariantNode.MaterialNode"):  # We're not testing the material node here, so patch it out.
            with patch.dict(metadata_dict, metadata):
                mocked_container = createMockedInstanceContainer()
                variant_node._materialAdded(mocked_container)

    for key in unchanged_material_list:
        assert original_material_nodes[key] == variant_node.materials[key]

    for key in changed_material_list:
        assert original_material_nodes[key] != variant_node.materials[key]

