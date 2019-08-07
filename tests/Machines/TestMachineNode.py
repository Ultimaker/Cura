from unittest.mock import patch, MagicMock
import pytest

from UM.Settings.Interfaces import ContainerInterface
from cura.Machines.MachineNode import MachineNode


machine_node_variant_added_test_data = [({"type": "Not a variant!"}, ["Variant One", "Variant Two"]),  # Wrong type
                                        ({"type": "variant", "name": "Variant One"}, ["Variant One", "Variant Two"]),  # Name already added
                                        ({"type": "variant", "name": "Variant Three", "hardware_type": "Not a nozzle"}, ["Variant One", "Variant Two"]),  # Wrong hardware type
                                        ({"type": "variant", "name": "Variant Three", "hardware_type": "nozzle", "definition": "machine_3"}, ["Variant One", "Variant Two"]),  # Wrong definition ID
                                        ({"type": "variant", "name": "Variant Three", "hardware_type": "nozzle", "definition": "machine_1"}, ["Variant One", "Variant Two", "Variant Three"])] # Yay! It's finally added


metadata_dict = {}


@pytest.fixture
def container_registry():
    result = MagicMock()
    result.findInstanceContainersMetadata = MagicMock(return_value = [{"id": "variant_1", "name": "Variant One"}, {"id": "variant_2", "name": "Variant Two"}])
    return result


def getMetadataEntrySideEffect(*args, **kwargs):
    return metadata_dict.get(args[0])


def createMockedInstanceContainer():
    result = MagicMock(spec = ContainerInterface)
    result.getMetaDataEntry = MagicMock(side_effect=getMetadataEntrySideEffect)
    return result


def createMachineNode(container_id, container_registry):
    with patch("cura.Machines.MachineNode.VariantNode"):  # We're not testing the variant node here, so patch it out.
        with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
            return MachineNode(container_id)


def test_machineNodeInit(container_registry):
    machine_node = createMachineNode("machine_1", container_registry)

    # As variants get stored by name, we want to check if those get added.
    assert "Variant One" in machine_node.variants
    assert "Variant Two" in machine_node.variants
    assert len(machine_node.variants) == 2  # And ensure that *only* those two got added.


@pytest.mark.parametrize("metadata,variant_result_list", machine_node_variant_added_test_data)
def test_machineNodeVariantAdded(container_registry, metadata, variant_result_list):
    machine_node = createMachineNode("machine_1", container_registry)

    with patch("cura.Machines.MachineNode.VariantNode"):  # We're not testing the variant node here, so patch it out.
        with patch.dict(metadata_dict, metadata):
            mocked_container = createMockedInstanceContainer()
            machine_node._variantAdded(mocked_container)

    assert len(variant_result_list) == len(machine_node.variants)
    for name in variant_result_list:
        assert name in machine_node.variants