# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import TYPE_CHECKING, Optional, List, Set, Dict

from PyQt5.QtCore import QObject

from UM.FlameProfiler import pyqtSlot
from UM.Logger import Logger
from UM.PluginRegistry import PluginRegistry  # So MachineAction can be added as plugin type

if TYPE_CHECKING:
    from cura.CuraApplication import CuraApplication
    from cura.Settings.GlobalStack import GlobalStack
    from cura.MachineAction import MachineAction


class UnknownMachineActionError(Exception):
    """Raised when trying to add an unknown machine action as a required action"""

    pass


class NotUniqueMachineActionError(Exception):
    """Raised when trying to add a machine action that does not have an unique key."""

    pass


class MachineActionManager(QObject):
    def __init__(self, application: "CuraApplication", parent: Optional["QObject"] = None) -> None:
        super().__init__(parent = parent)
        self._application = application
        self._container_registry = self._application.getContainerRegistry()

        # Keeps track of which machines have already been processed so we don't do that again.
        self._definition_ids_with_default_actions_added = set()  # type: Set[str]

        # Dict of all known machine actions
        self._machine_actions = {}  # type: Dict[str, MachineAction]
        # Dict of all required actions by definition ID
        self._required_actions = {}  # type: Dict[str, List[MachineAction]]
        # Dict of all supported actions by definition ID
        self._supported_actions = {}  # type: Dict[str, List[MachineAction]]
        # Dict of all actions that need to be done when first added by definition ID
        self._first_start_actions = {}  # type: Dict[str, List[MachineAction]]

    def initialize(self) -> None:
        # Add machine_action as plugin type
        PluginRegistry.addType("machine_action", self.addMachineAction)

    # Adds all default machine actions that are defined in the machine definition for the given machine.
    def addDefaultMachineActions(self, global_stack: "GlobalStack") -> None:
        definition_id = global_stack.definition.getId()

        if definition_id in self._definition_ids_with_default_actions_added:
            Logger.log("i", "Default machine actions have been added for machine definition [%s], do nothing.",
                       definition_id)
            return

        supported_actions = global_stack.getMetaDataEntry("supported_actions", [])
        for action_key in supported_actions:
            self.addSupportedAction(definition_id, action_key)

        required_actions = global_stack.getMetaDataEntry("required_actions", [])
        for action_key in required_actions:
            self.addRequiredAction(definition_id, action_key)

        first_start_actions = global_stack.getMetaDataEntry("first_start_actions", [])
        for action_key in first_start_actions:
            self.addFirstStartAction(definition_id, action_key)

        self._definition_ids_with_default_actions_added.add(definition_id)
        Logger.log("i", "Default machine actions added for machine definition [%s]", definition_id)

    def addRequiredAction(self, definition_id: str, action_key: str) -> None:
        """Add a required action to a machine

        Raises an exception when the action is not recognised.
        """
        if action_key in self._machine_actions:
            if definition_id in self._required_actions:
                if self._machine_actions[action_key] not in self._required_actions[definition_id]:
                    self._required_actions[definition_id].append(self._machine_actions[action_key])
            else:
                self._required_actions[definition_id] = [self._machine_actions[action_key]]
        else:
            raise UnknownMachineActionError("Action %s, which is required for %s is not known." % (action_key, definition_id))

    def addSupportedAction(self, definition_id: str, action_key: str) -> None:
        """Add a supported action to a machine."""

        if action_key in self._machine_actions:
            if definition_id in self._supported_actions:
                if self._machine_actions[action_key] not in self._supported_actions[definition_id]:
                    self._supported_actions[definition_id].append(self._machine_actions[action_key])
            else:
                self._supported_actions[definition_id] = [self._machine_actions[action_key]]
        else:
            Logger.log("w", "Unable to add %s to %s, as the action is not recognised", action_key, definition_id)

    def addFirstStartAction(self, definition_id: str, action_key: str) -> None:
        """Add an action to the first start list of a machine."""

        if action_key in self._machine_actions:
            if definition_id in self._first_start_actions:
                self._first_start_actions[definition_id].append(self._machine_actions[action_key])
            else:
                self._first_start_actions[definition_id] = [self._machine_actions[action_key]]
        else:
            Logger.log("w", "Unable to add %s to %s, as the action is not recognised", action_key, definition_id)

    def addMachineAction(self, action: "MachineAction") -> None:
        """Add a (unique) MachineAction

        if the Key of the action is not unique, an exception is raised.
        """
        if action.getKey() not in self._machine_actions:
            self._machine_actions[action.getKey()] = action
        else:
            raise NotUniqueMachineActionError("MachineAction with key %s was already added. Actions must have unique keys.", action.getKey())

    @pyqtSlot(str, result = "QVariantList")
    def getSupportedActions(self, definition_id: str) -> List["MachineAction"]:
        """Get all actions supported by given machine

        :param definition_id: The ID of the definition you want the supported actions of
        :returns: set of supported actions.
        """
        if definition_id in self._supported_actions:
            return list(self._supported_actions[definition_id])
        else:
            return list()

    def getRequiredActions(self, definition_id: str) -> List["MachineAction"]:
        """Get all actions required by given machine

        :param definition_id: The ID of the definition you want the required actions of
        :returns: set of required actions.
        """
        if definition_id in self._required_actions:
            return self._required_actions[definition_id]
        else:
            return list()

    @pyqtSlot(str, result = "QVariantList")
    def getFirstStartActions(self, definition_id: str) -> List["MachineAction"]:
        """Get all actions that need to be performed upon first start of a given machine.

        Note that contrary to required / supported actions a list is returned (as it could be required to run the same
        action multiple times).
        :param definition_id: The ID of the definition that you want to get the "on added" actions for.
        :returns: List of actions.
        """
        if definition_id in self._first_start_actions:
            return self._first_start_actions[definition_id]
        else:
            return []

    def removeMachineAction(self, action: "MachineAction") -> None:
        """Remove Machine action from manager

        :param action: to remove
        """
        try:
            del self._machine_actions[action.getKey()]
        except KeyError:
            Logger.log("w", "Trying to remove MachineAction (%s) that was already removed", action.getKey())

    def getMachineAction(self, key: str) -> Optional["MachineAction"]:
        """Get MachineAction by key

        :param key: String of key to select
        :return: Machine action if found, None otherwise
        """
        if key in self._machine_actions:
            return self._machine_actions[key]
        else:
            return None
