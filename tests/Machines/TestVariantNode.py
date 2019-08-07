from unittest.mock import patch, MagicMock
import pytest

from cura.Machines.VariantNode import VariantNode


metadata_dict = {"fdmprinter": {"no_variant": [{"base_file": "material_1", "id": "material_1"}, {"base_file": "material_2", "id": "material_2"}]},
                 "machine_1": {"no_variant": [{"base_file": "material_1", "id": "material_1"}, {"base_file": "material_2", "id": "material_2"}],
                               "Variant One": [{"base_file": "material_1", "id": "material_1"}, {"base_file": "material_2", "id": "material_2"}]}}


def getMetadataEntrySideEffect(*args, **kwargs):
    variant = kwargs.get("variant")
    definition = kwargs.get("definition")

    if variant is not None:
        return metadata_dict.get(definition).get(variant)
    return metadata_dict.get(definition).get("no_variant")


@pytest.fixture
def machine_node():
    mocked_machine_node = MagicMock()
    mocked_machine_node.container_id = "machine_1"
    return mocked_machine_node


@pytest.fixture
def container_registry():
    result = MagicMock()
    result.findInstanceContainersMetadata = MagicMock(side_effect = getMetadataEntrySideEffect)
    result.findContainersMetadata = MagicMock(return_value = [{"name": "Variant One"}])
    return result


def test_variantNodeInit(container_registry, machine_node):
    with patch("cura.Machines.VariantNode.MaterialNode"):  # We're not testing the material node here, so patch it out.
        with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
            node = VariantNode("variant_1", machine_node)

    assert "material_1" in node.materials
    assert "material_2" in node.materials
    assert len(node.materials) == 2


def test_variantNodeInit_excludedMaterial(container_registry, machine_node):
    machine_node.exclude_materials = ["material_1"]
    with patch("cura.Machines.VariantNode.MaterialNode"):  # We're not testing the material node here, so patch it out.
        with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
            node = VariantNode("variant_1", machine_node)

    assert "material_1" not in node.materials
    assert "material_2" in node.materials
    assert len(node.materials) == 1
