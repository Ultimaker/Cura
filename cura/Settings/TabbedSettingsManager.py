# Copyright (c) 2026 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import TYPE_CHECKING, Optional

from PyQt6.QtCore import QObject, pyqtSlot

from UM.Logger import Logger

from cura.Settings.PerCategoryVisibilityHandler import PerCategoryVisibilityHandler
from cura.Settings.InstanceContainerVisibilityHandler import InstanceContainerVisibilityHandler
from cura.Settings.ExtendedSettingPreferenceVisibilityHandler import ExtendedSettingPreferenceVisibilityHandler

if TYPE_CHECKING:
    from cura.Settings.MachineManager import MachineManager


class TabbedSettingsManager(QObject):
    """Provides lazily-created visibility handler singletons to the tabbed settings QML view."""

    def __init__(self, machine_manager: "MachineManager", parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._machine_manager = machine_manager
        self._visibility_handlers: dict = {}

    @pyqtSlot(str, result=QObject)
    def getVisibilityHandler(self, handler_type: str) -> Optional[QObject]:
        """Return a shared visibility handler instance for the given type.

        Supported types: "ExtendedSettingPreference", "PerCategory", "InstanceContainer"
        """
        if handler_type not in self._visibility_handlers:
            handler: Optional[QObject] = None
            if handler_type == "PerCategory":
                handler = PerCategoryVisibilityHandler(machine_manager=self._machine_manager)
            elif handler_type == "InstanceContainer":
                handler = InstanceContainerVisibilityHandler(machine_manager=self._machine_manager)
            elif handler_type == "ExtendedSettingPreference":
                handler = ExtendedSettingPreferenceVisibilityHandler()
            else:
                Logger.warning(f"TabbedSettingsManager: unknown handler type '{handler_type}'")
                return None  # type: ignore[return-value]
            self._visibility_handlers[handler_type] = handler

        return self._visibility_handlers[handler_type]
