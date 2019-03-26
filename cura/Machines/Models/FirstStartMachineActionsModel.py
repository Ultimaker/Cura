# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional

from PyQt5.QtCore import QObject, Qt

from UM.Qt.ListModel import ListModel


#
# This model holds all first-start machine actions for the currently active machine. It has 2 roles:
#   - title   : the title/name of the action
#   - content : the QObject of the QML content of the action
#   - action  : the MachineAction object itself
#
class FirstStartMachineActionsModel(ListModel):

    TitleRole = Qt.UserRole + 1
    ContentRole = Qt.UserRole + 2
    ActionRole = Qt.UserRole + 3

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

        self.addRoleName(self.TitleRole, "title")
        self.addRoleName(self.ContentRole, "content")
        self.addRoleName(self.ActionRole, "action")

        from cura.CuraApplication import CuraApplication
        self._application = CuraApplication.getInstance()

        self._application.initializationFinished.connect(self._initialize)

    def _initialize(self) -> None:
        self._application.getMachineManager().globalContainerChanged.connect(self._update)
        self._update()

    def _update(self) -> None:
        global_stack = self._application.getMachineManager().activeMachine
        if global_stack is None:
            self.setItems([])
            return

        definition_id = global_stack.definition.getId()
        first_start_actions = self._application.getMachineActionManager().getFirstStartActions(definition_id)

        item_list = []
        for item in first_start_actions:
            item_list.append({"title": item.label,
                              "content": item.displayItem,
                              "action": item,
                              })

        self.setItems(item_list)


__all__ = ["FirstStartMachineActionsModel"]
