# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import pytest

from cura.MachineAction import MachineAction
from cura.MachineActionManager import NotUniqueMachineActionError, UnknownMachineActionError

class Machine:
    def __init__(self, key = ""):
        self._key = key

    def getKey(self):
        return self._key

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
    assert machine_action_manager.getRequiredActions(test_machine) == set()

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

    # Check if inserting an action works
    machine_action_manager.addFirstStartAction(test_machine, "test_action_2", index = 1)
    assert machine_action_manager.getFirstStartActions(test_machine) == [test_action, test_action_2, test_action]

    # Check that adding a unknown action doesn't change anything.
    machine_action_manager.addFirstStartAction(test_machine, "key_that_doesnt_exist", index = 1)
    assert machine_action_manager.getFirstStartActions(test_machine) == [test_action, test_action_2, test_action]

