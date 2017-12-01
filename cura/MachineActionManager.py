# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from UM.Logger import Logger
from UM.PluginRegistry import PluginRegistry  # So MachineAction can be added as plugin type

from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.DefinitionContainer import DefinitionContainer

from PyQt5.QtCore import QObject
from UM.FlameProfiler import pyqtSlot

##  Raised when trying to add an unknown machine action as a required action
class UnknownMachineActionError(Exception):
    pass


##  Raised when trying to add a machine action that does not have an unique key.
class NotUniqueMachineActionError(Exception):
    pass


class MachineActionManager(QObject):
    def __init__(self, parent = None):
        super().__init__(parent)

        self._machine_actions = {}  # Dict of all known machine actions
        self._required_actions = {}  # Dict of all required actions by definition ID
        self._supported_actions = {}  # Dict of all supported actions by definition ID
        self._first_start_actions = {}  # Dict of all actions that need to be done when first added by definition ID

        # Add machine_action as plugin type
        PluginRegistry.addType("machine_action", self.addMachineAction)

        # Ensure that all containers that were registered before creation of this registry are also handled.
        # This should not have any effect, but it makes it safer if we ever refactor the order of things.
        for container in ContainerRegistry.getInstance().findDefinitionContainers():
            self._onContainerAdded(container)

        ContainerRegistry.getInstance().containerAdded.connect(self._onContainerAdded)

    def _onContainerAdded(self, container):
        ## Ensure that the actions are added to this manager
        if isinstance(container, DefinitionContainer):
            supported_actions = container.getMetaDataEntry("supported_actions", [])
            for action in supported_actions:
                self.addSupportedAction(container.getId(), action)

            required_actions = container.getMetaDataEntry("required_actions", [])
            for action in required_actions:
                self.addRequiredAction(container.getId(), action)

            first_start_actions = container.getMetaDataEntry("first_start_actions", [])
            for action in first_start_actions:
                self.addFirstStartAction(container.getId(), action)

    ##  Add a required action to a machine
    #   Raises an exception when the action is not recognised.
    def addRequiredAction(self, definition_id, action_key):
        if action_key in self._machine_actions:
            if definition_id in self._required_actions:
                if self._machine_actions[action_key] not in self._required_actions[definition_id]:
                    self._required_actions[definition_id].append(self._machine_actions[action_key])
            else:
                self._required_actions[definition_id] = [self._machine_actions[action_key]]
        else:
            raise UnknownMachineActionError("Action %s, which is required for %s is not known." % (action_key, definition_id))

    ##  Add a supported action to a machine.
    def addSupportedAction(self, definition_id, action_key):
        if action_key in self._machine_actions:
            if definition_id in self._supported_actions:
                if self._machine_actions[action_key] not in self._supported_actions[definition_id]:
                    self._supported_actions[definition_id].append(self._machine_actions[action_key])
            else:
                self._supported_actions[definition_id] = [self._machine_actions[action_key]]
        else:
            Logger.log("w", "Unable to add %s to %s, as the action is not recognised", action_key, definition_id)

    ##  Add an action to the first start list of a machine.
    def addFirstStartAction(self, definition_id, action_key, index = None):
        if action_key in self._machine_actions:
            if definition_id in self._first_start_actions:
                if index is not None:
                    self._first_start_actions[definition_id].insert(index, self._machine_actions[action_key])
                else:
                    self._first_start_actions[definition_id].append(self._machine_actions[action_key])
            else:
                self._first_start_actions[definition_id] = [self._machine_actions[action_key]]
        else:
            Logger.log("w", "Unable to add %s to %s, as the action is not recognised", action_key, definition_id)

    ##  Add a (unique) MachineAction
    #   if the Key of the action is not unique, an exception is raised.
    def addMachineAction(self, action):
        if action.getKey() not in self._machine_actions:
            self._machine_actions[action.getKey()] = action
        else:
            raise NotUniqueMachineActionError("MachineAction with key %s was already added. Actions must have unique keys.", action.getKey())

    ##  Get all actions supported by given machine
    #   \param definition_id The ID of the definition you want the supported actions of
    #   \returns set of supported actions.
    @pyqtSlot(str, result = "QVariantList")
    def getSupportedActions(self, definition_id):
        if definition_id in self._supported_actions:
            return list(self._supported_actions[definition_id])
        else:
            return list()

    ##  Get all actions required by given machine
    #   \param definition_id The ID of the definition you want the required actions of
    #   \returns set of required actions.
    def getRequiredActions(self, definition_id):
        if definition_id in self._required_actions:
            return self._required_actions[definition_id]
        else:
            return set()

    ##  Get all actions that need to be performed upon first start of a given machine.
    #   Note that contrary to required / supported actions a list is returned (as it could be required to run the same
    #   action multiple times).
    #   \param definition_id The ID of the definition that you want to get the "on added" actions for.
    #   \returns List of actions.
    @pyqtSlot(str, result="QVariantList")
    def getFirstStartActions(self, definition_id):
        if definition_id in self._first_start_actions:
            return self._first_start_actions[definition_id]
        else:
            return []

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
