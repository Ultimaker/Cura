# Copyright (c) 2026 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional, Set, TYPE_CHECKING

from UM.Settings.Models.SettingVisibilityHandler import SettingVisibilityHandler
from UM.Logger import Logger

from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal

if TYPE_CHECKING:
    from cura.Settings.MachineManager import MachineManager


class InstanceContainerVisibilityHandler(SettingVisibilityHandler):
    """Visibility handler that shows settings that have been modified in a given container stack index (e.g. user changes)."""

    def __init__(self, machine_manager: "MachineManager", parent: Optional[QObject] = None, *args, **kwargs) -> None:
        super().__init__(parent=parent, *args, **kwargs)
        self._active = False  # inactive until explicitly enabled via the "Changed settings" tab
        self._container_index: Optional[int] = None
        self._visible_settings: Set[str] = set()

        self._machine_manager = machine_manager
        self._machine_manager.activeStackChanged.connect(self._update)
        self._machine_manager.activeStackValueChanged.connect(self._update)

    def setContainerIndex(self, container_index: int) -> None:
        if container_index == self._container_index:
            return
        self._container_index = container_index
        self.containerIndexChanged.emit()
        self._update()

    containerIndexChanged = pyqtSignal()

    @pyqtProperty(int, notify=containerIndexChanged, fset=setContainerIndex)
    def containerIndex(self) -> int:
        return self._container_index if self._container_index is not None else -1

    def setActive(self, active: bool) -> None:
        if active == self._active:
            return
        self._active = active
        self.activeChanged.emit()
        self._update()

    activeChanged = pyqtSignal()

    @pyqtProperty(bool, notify=activeChanged, fset=setActive)
    def active(self) -> bool:
        return self._active

    def _update(self) -> None:
        if not self._active:
            return

        if self._container_index is None:
            Logger.warning("Tried to update InstanceContainerVisibilityHandler, but there is no container index")
            return

        global_container_stack = self._machine_manager.activeMachine
        if not global_container_stack:
            Logger.warning("Tried to update InstanceContainerVisibilityHandler, but there is no global stack")
            return

        extruder_stack = self._machine_manager.activeStack
        if not extruder_stack:
            Logger.warning("Tried to update InstanceContainerVisibilityHandler, but there is no extruder stack")
            return

        visible_settings: Set[str] = set()
        visible_categories: Set[str] = set()

        for stack in [global_container_stack, extruder_stack]:
            container = stack.getContainer(self._container_index)
            stack_settings = container.getAllKeys()
            visible_settings.update(stack_settings)

            for setting_key in stack_settings:
                category = container.getInstance(setting_key).definition
                while category is not None and category.type != "category":
                    category = category.parent
                if category is not None:
                    visible_categories.add(category.key)

        visible_settings.update(visible_categories)

        if self._visible_settings != visible_settings:
            self._visible_settings = visible_settings
            self.setVisible(visible_settings)
