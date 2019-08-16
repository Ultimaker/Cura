from unittest.mock import patch, MagicMock
import pytest

from UM.Settings.Interfaces import ContainerInterface
from cura.Machines.MachineNode import MachineNode

metadata_dict = {}


@pytest.fixture
def container_registry():
    result = MagicMock()
    result.findInstanceContainersMetadata = MagicMock(return_value = [{"id": "variant_1", "name": "Variant One", "quality_type": "normal"}, {"id": "variant_2", "name": "Variant Two", "quality_type": "great"}])
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