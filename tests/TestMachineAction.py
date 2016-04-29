#Todo: Write tests

import pytest

from cura.MachineAction import MachineAction
from cura.MachineActionManager import MachineActionManager, NotUniqueMachineAction

class Machine:
    def __init__(self, key = ""):
        self._key = key

    def getKey(self):
        return self._key


def test_addMachineAction():

    machine_manager = MachineActionManager()

    test_action = MachineAction(key = "test")
    test_machine = Machine("test_machine")
    machine_manager.addMachineAction(test_action)

    assert machine_manager.getMachineAction("test") == test_action

    # Adding the same machine action is not allowed.
    with pytest.raises(NotUniqueMachineAction):
        machine_manager.addMachineAction(test_action)

    # Check if adding a supported action works.
    machine_manager.addSupportedAction(test_machine, "test")
    assert machine_manager.getSupportedActions(test_machine) == {test_action}

    # Check that adding a unknown action doesn't change anything.
    machine_manager.addSupportedAction(test_machine, "key_that_doesnt_exist")
    assert machine_manager.getSupportedActions(test_machine) == {test_action}

