# Copyright (c) 2026 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from enum import IntEnum
from typing import Dict, TYPE_CHECKING, Optional

from PyQt6.QtCore import QObject, pyqtProperty, pyqtSlot

from UM.Logger import Logger
from UM.Settings.Models.SettingPreferenceVisibilityHandler import SettingPreferenceVisibilityHandler

from cura.Settings.PerCategoryVisibilityHandler import PerCategoryVisibilityHandler
from cura.Settings.InstanceContainerVisibilityHandler import InstanceContainerVisibilityHandler

if TYPE_CHECKING:
    from cura.Settings.MachineManager import MachineManager


class TabbedSettingsManager(QObject):
    """Provides lazily-created visibility handler singletons to the tabbed settings QML view."""

    class HandlerType(IntEnum):
        SettingPreference = 0
        PerCategory = 1
        InstanceContainer = 2

    def __init__(self, machine_manager: "MachineManager", parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._machine_manager = machine_manager
        self._visibility_handlers: Dict["TabbedSettingsManager.HandlerType", QObject] = {}

    @pyqtProperty(int, constant=True)
    def SettingPreference(self) -> int:
        return int(TabbedSettingsManager.HandlerType.SettingPreference)

    @pyqtProperty(int, constant=True)
    def PerCategory(self) -> int:
        return int(TabbedSettingsManager.HandlerType.PerCategory)

    @pyqtProperty(int, constant=True)
    def InstanceContainer(self) -> int:
        return int(TabbedSettingsManager.HandlerType.InstanceContainer)

    @pyqtSlot(int, result=QObject)
    def getVisibilityHandler(self, handler_type: int) -> Optional[QObject]:
        """Return a shared visibility handler instance for the given type.

        :param handler_type: One of the TabbedSettingsManager.HandlerType values, exposed to QML as the
        SettingPreference, PerCategory and InstanceContainer properties.
        """
        try:
            handler_type_enum = TabbedSettingsManager.HandlerType(handler_type)
        except ValueError:
            Logger.warning(f"TabbedSettingsManager: unknown handler type '{handler_type}'")
            return None

        if handler_type_enum not in self._visibility_handlers:
            handler: QObject
            if handler_type_enum == TabbedSettingsManager.HandlerType.PerCategory:
                handler = PerCategoryVisibilityHandler(machine_manager=self._machine_manager)
            elif handler_type_enum == TabbedSettingsManager.HandlerType.InstanceContainer:
                handler = InstanceContainerVisibilityHandler(machine_manager=self._machine_manager)
            else:
                handler = SettingPreferenceVisibilityHandler()
            self._visibility_handlers[handler_type_enum] = handler

        return self._visibility_handlers[handler_type_enum]
