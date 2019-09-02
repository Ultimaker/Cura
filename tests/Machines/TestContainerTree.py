from unittest.mock import patch, MagicMock
import pytest
from UM.Settings.DefinitionContainer import DefinitionContainer
from cura.Machines.ContainerTree import ContainerTree
from cura.Settings.GlobalStack import GlobalStack

import cura.CuraApplication  # DEBUG!


def createMockedStack(definition_id: str):
    result = MagicMock(spec = GlobalStack)
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

        # It should only react when a globalStack is added.
        container_tree._machineAdded(mocked_definition_container)
        assert "machine_3" not in container_tree.machines

        container_tree._machineAdded(createMockedStack("machine_3"))
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

def test_getCurrentQualityGroupsNoGlobalStack(container_registry):
    with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value = container_registry)):
        with patch("cura.CuraApplication.CuraApplication.getInstance", MagicMock(return_value = MagicMock(getGlobalContainerStack = MagicMock(return_value = None)))):
            container_tree = ContainerTree()
            result = container_tree.getCurrentQualityGroups()

    assert len(result) == 0