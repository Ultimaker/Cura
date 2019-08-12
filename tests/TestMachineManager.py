from unittest.mock import MagicMock, patch

import pytest

@pytest.mark.skip(reason = "Outdated test")
def test_setActiveMachine(machine_manager):
    registry = MagicMock()

    mocked_global_stack = MagicMock()

    mocked_global_stack.getId = MagicMock(return_value = "test_machine")
    registry.findContainerStacks = MagicMock(return_value = [mocked_global_stack])
    with patch("cura.Settings.CuraContainerRegistry.CuraContainerRegistry.getInstance", MagicMock(return_value=registry)):
        with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=registry)):
            machine_manager.setActiveMachine("test_machine")

            # Although we mocked the application away, we still want to know if it was notified about the attempted change.
            machine_manager._application.setGlobalContainerStack.assert_called_with(mocked_global_stack)


def test_hasUserSettings(machine_manager, application):
    mocked_stack = application.getGlobalContainerStack()

    mocked_instance_container = MagicMock(name="UserSettingContainer")
    mocked_instance_container.getNumInstances = MagicMock(return_value = 12)
    mocked_stack.getTop = MagicMock(return_value = mocked_instance_container)

    assert machine_manager.numUserSettings == 12
    assert machine_manager.hasUserSettings


def test_totalNumberOfSettings(machine_manager):
    registry = MagicMock()
    mocked_definition = MagicMock()
    mocked_definition.getAllKeys = MagicMock(return_value = ["omg", "zomg", "foo"])
    registry.findDefinitionContainers = MagicMock(return_value = [mocked_definition])
    with patch("cura.Settings.CuraContainerRegistry.CuraContainerRegistry.getInstance", MagicMock(return_value=registry)):
        assert machine_manager.totalNumberOfSettings == 3
