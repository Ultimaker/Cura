from UM.Logger import Logger


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
                self._required_actions[machine].append(self._machine_actions[action_key])
            else:
                self._required_actions[machine] = set(self._machine_actions[action_key])
        else:
            # Todo: define specific Exception types (instead of general type)
            raise Exception("Action %s, which is required for %s is not known." % (action_key, machine.getKey()))

    ##  Add a (unique) MachineAction
    #   if the Key of the action is not unique, an exception is raised.
    def addMachineAction(self, action):
        if action.getKey() not in self._machine_action:
            self._machine_action[action.getKey()] = action
        else:
            # Todo: define specific Exception types (instead of general type)
            raise Exception("MachineAction with key %s was already added. Actions must have unique keys.", action.getKey())

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