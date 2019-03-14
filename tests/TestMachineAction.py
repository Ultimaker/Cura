# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import pytest

from cura.MachineAction import MachineAction
from cura.MachineActionManager import NotUniqueMachineActionError, UnknownMachineActionError
from cura.Settings.GlobalStack import GlobalStack


@pytest.fixture()
def global_stack():
    gs = GlobalStack("test_global_stack")
    gs._metadata = {
        "supported_actions": ["supported_action_1", "supported_action_2"],
        "required_actions": ["required_action_1", "required_action_2"],
        "first_start_actions": ["first_start_actions_1", "first_start_actions_2"]
    }
    return gs


class Machine:
    def __init__(self, key = ""):
        self._key = key

    def getKey(self):
        return self._key


def test_addDefaultMachineActions(machine_action_manager, global_stack):
    # The actions need to be registered first as "available actions" in the manager,
    # same as the "machine_action" type does when registering a plugin.
    all_actions = []
    for action_key_list in global_stack._metadata.values():
        for key in action_key_list:
            all_actions.append(MachineAction(key = key))
    for action in all_actions:
        machine_action_manager.addMachineAction(action)

    # Only the actions in the definition that were registered first will be added to the machine.
    # For the sake of this test, all the actions were previouly added.
    machine_action_manager.addDefaultMachineActions(global_stack)
    definition_id = global_stack.getDefinition().getId()

    support_action_keys = [a.getKey() for a in machine_action_manager.getSupportedActions(definition_id)]
    assert support_action_keys == global_stack.getMetaDataEntry("supported_actions")

    required_action_keys = [a.getKey() for a in machine_action_manager.getRequiredActions(definition_id)]
    assert required_action_keys == global_stack.getMetaDataEntry("required_actions")

    first_start_action_keys = [a.getKey() for a in machine_action_manager.getFirstStartActions(definition_id)]
    assert first_start_action_keys == global_stack.getMetaDataEntry("first_start_actions")


def test_addMachineAction(machine_action_manager):

    test_action = MachineAction(key = "test_action")
    test_action_2 = MachineAction(key = "test_action_2")
    test_machine = Machine("test_machine")
    machine_action_manager.addMachineAction(test_action)
    machine_action_manager.addMachineAction(test_action_2)

    assert machine_action_manager.getMachineAction("test_action") == test_action
    assert machine_action_manager.getMachineAction("key_that_doesnt_exist") is None

    # Adding the same machine action is not allowed.
    with pytest.raises(NotUniqueMachineActionError):
        machine_action_manager.addMachineAction(test_action)

    # Check that the machine has no supported actions yet.
    assert machine_action_manager.getSupportedActions(test_machine) == list()

    # Check if adding a supported action works.
    machine_action_manager.addSupportedAction(test_machine, "test_action")
    assert machine_action_manager.getSupportedActions(test_machine) == [test_action, ]

    # Check that adding a unknown action doesn't change anything.
    machine_action_manager.addSupportedAction(test_machine, "key_that_doesnt_exist")
    assert machine_action_manager.getSupportedActions(test_machine) == [test_action, ]

    # Check if adding multiple supported actions works.
    machine_action_manager.addSupportedAction(test_machine, "test_action_2")
    assert machine_action_manager.getSupportedActions(test_machine) == [test_action, test_action_2]

    # Check that the machine has no required actions yet.
    assert machine_action_manager.getRequiredActions(test_machine) == list()

    ## Ensure that only known actions can be added.
    with pytest.raises(UnknownMachineActionError):
        machine_action_manager.addRequiredAction(test_machine, "key_that_doesnt_exist")

    ## Check if adding single required action works
    machine_action_manager.addRequiredAction(test_machine, "test_action")
    assert machine_action_manager.getRequiredActions(test_machine) == [test_action, ]

    # Check if adding multiple required actions works.
    machine_action_manager.addRequiredAction(test_machine, "test_action_2")
    assert machine_action_manager.getRequiredActions(test_machine) == [test_action, test_action_2]

    # Ensure that firstStart actions are empty by default.
    assert machine_action_manager.getFirstStartActions(test_machine) == []

    # Check if adding multiple (the same) actions to first start actions work.
    machine_action_manager.addFirstStartAction(test_machine, "test_action")
    machine_action_manager.addFirstStartAction(test_machine, "test_action")
    assert machine_action_manager.getFirstStartActions(test_machine) == [test_action, test_action]

    # Adding unknown action should not crash.
    machine_action_manager.addFirstStartAction(test_machine, "key_that_doesnt_exists")

def test_removeMachineAction(machine_action_manager):
    test_action = MachineAction(key="test_action")
    test_machine = Machine("test_machine")
    machine_action_manager.addMachineAction(test_action)

    # Remove the machine action
    machine_action_manager.removeMachineAction(test_action)
    assert machine_action_manager.getMachineAction("test_action") is None

    # Attempting to remove it again should not crash.
    machine_action_manager.removeMachineAction(test_action)
