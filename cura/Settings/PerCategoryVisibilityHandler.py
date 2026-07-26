# Copyright (c) 2026 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Settings.Models.SettingVisibilityHandler import SettingVisibilityHandler
from UM.Logger import Logger

from PyQt6.QtCore import pyqtProperty, pyqtSignal


class PerCategoryVisibilityHandler(SettingVisibilityHandler):
    """Visibility handler that shows all settings belonging to a single category."""

    def __init__(self, machine_manager, parent=None, *args, **kwargs):
        super().__init__(parent=parent, *args, **kwargs)
        self._machine_manager = machine_manager
        self._root_key = ""

    def setRootKey(self, root_key: str) -> None:
        if root_key == self._root_key:
            return

        self._root_key = root_key

        global_container_stack = self._machine_manager.activeMachine
        if not global_container_stack:
            Logger.error("Tried to set root of PerCategoryVisibilityHandler but there is no global stack")
            return

        definitions = global_container_stack.getBottom().findDefinitions(key=root_key)
        if not definitions:
            Logger.warning(f"Tried to set root of PerCategoryVisibilityHandler to an unknown definition: {root_key}")
            return

        visible_settings = set([d.key for d in definitions[0].findDefinitions()])

        self.setVisible(visible_settings)

    rootKeyChanged = pyqtSignal()

    @pyqtProperty(str, notify=rootKeyChanged, fset=setRootKey)
    def rootKey(self) -> str:
        return self._root_key
