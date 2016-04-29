# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.
from UM.Logger import Logger


##  Raised when trying to add an unknown machine action as a required action
class UnknownMachineAction(Exception):
    pass


##  Raised when trying to add a machine action that does not have an unique key.
class NotUniqueMachineAction(Exception):
    pass


class MachineActionManager:
    def __init__(self):
        ##  Dict of all known machine actions
        self._machine_actions = {}

        ##  Dict of all required actions by machine reference.
        self._required_actions = {}

        ##  Dict of all supported actions by machine reference
        self._supported_actions = {}

        ##  Dict of all actions that need to be done when first added by machine reference.
        self._first_start_actions = {}

    ##  Add a required action to a machine
    #   Raises an exception when the action is not recognised.
    def addRequiredAction(self, machine, action_key):
        if action_key in self._machine_actions:
            if machine in self._required_actions:
                self._required_actions[machine] |= {self._machine_actions[action_key]}
            else:
                self._required_actions[machine] = {self._machine_actions[action_key]}
        else:
            raise UnknownMachineAction("Action %s, which is required for %s is not known." % (action_key, machine.getKey()))

    ##  Add a supported action to a machine.
    def addSupportedAction(self, machine, action_key):
        if action_key in self._machine_actions:
            if machine in self._supported_actions:
                self._supported_actions[machine] |= {self._machine_actions[action_key]}
            else:
                self._supported_actions[machine] = {self._machine_actions[action_key]}
        else:
            Logger.log("W", "Unable to add %s to %s, as the action is not recognised", action_key, machine.getKey())

    ##  Add an action to the first start list of a machine.
    def addFirstStartAction(self, machine, action_key, index = None):
        if action_key in self._machine_actions:
            if machine in self._supported_actions and index is not None:
                self._first_start_actions[machine].insert(index, self._machine_actions[action_key])
            else:
                self._first_start_actions[machine] = [self._machine_actions[action_key]]
        else:
            Logger.log("W", "Unable to add %s to %s, as the action is not recognised", action_key, machine.getKey())

    ##  Add a (unique) MachineAction
    #   if the Key of the action is not unique, an exception is raised.
    def addMachineAction(self, action):
        if action.getKey() not in self._machine_actions:
            self._machine_actions[action.getKey()] = action
        else:
            raise NotUniqueMachineAction("MachineAction with key %s was already added. Actions must have unique keys.", action.getKey())

    ##  Get all actions supported by given machine
    #   \param machine The machine you want the supported actions of
    #   \returns set of supported actions.
    def getSupportedActions(self, machine):
        if machine in self._supported_actions:
            return self._supported_actions[machine]
        else:
            return set()

    ##  Get all actions required by given machine
    #   \param machine The machine you want the required actions of
    #   \returns set of required actions.
    def getRequiredActions(self, machine):
        if machine in self._required_actions:
            return self._required_actions[machine]
        else:
            return set()

    ##  Remove Machine action from manager
    #   \param action to remove
    def removeMachineAction(self, action):
        try:
            del self._machine_actions[action.getKey()]
        except KeyError:
            Logger.log("w", "Trying to remove MachineAction (%s) that was already removed", action.getKey())

    ##  Get MachineAction by key
    #   \param key String of key to select
    #   \return Machine action if found, None otherwise
    def getMachineAction(self, key):
        if key in self._machine_actions:
            return self._machine_actions[key]
        else:
            return None