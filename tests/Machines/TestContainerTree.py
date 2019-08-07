from unittest.mock import patch, MagicMock
import pytest
from UM.Settings.DefinitionContainer import DefinitionContainer
from cura.Machines.ContainerTree import ContainerTree


def createMockedStack(definition_id: str):
    result = MagicMock()
    result.definition.getId = MagicMock(return_value = definition_id)
    return result


@pytest.fixture
def container_registry():
    result = MagicMock()
    result.findContainerStacks = MagicMock(return_value=[createMockedStack("machine_1"), createMockedStack("machine_2")])
    return result


def test_containerTreeInit(container_registry):
    with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
        container_tree = ContainerTree()

    assert "machine_1" in container_tree.machines
    assert "machine_2" in container_tree.machines


def test_newMachineAdded(container_registry):
    mocked_definition_container = MagicMock(spec=DefinitionContainer)
    mocked_definition_container.getId = MagicMock(return_value = "machine_3")

    with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
        container_tree = ContainerTree()
        # machine_3 shouldn't be there, as on init it wasn't in the registry
        assert "machine_3" not in container_tree.machines

        # But when it does get added (by manually triggering the _machineAdded), it should be there.
        container_tree._machineAdded(mocked_definition_container)
        assert "machine_3" in container_tree.machines


def test_alreadyKnownMachineAdded(container_registry):
    mocked_definition_container = MagicMock(spec=DefinitionContainer)
    mocked_definition_container.getId = MagicMock(return_value="machine_2")

    with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
        container_tree = ContainerTree()
        assert len(container_tree.machines) == 2

        # The ID is already there, so no machine should be added.
        container_tree._machineAdded(mocked_definition_container)
        assert len(container_tree.machines) == 2
