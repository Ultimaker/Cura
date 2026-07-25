# Copyright (c) 2026 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional

from PyQt6.QtCore import QObject, pyqtSlot

from UM.Logger import Logger

from cura.Settings.PerCategoryVisibilityHandler import PerCategoryVisibilityHandler
from cura.Settings.InstanceContainerVisibilityHandler import InstanceContainerVisibilityHandler
from cura.Settings.ExtendedSettingPreferenceVisibilityHandler import ExtendedSettingPreferenceVisibilityHandler


class TabbedSettingsManager(QObject):
    """Provides lazily-created visibility handler singletons to the tabbed settings QML view."""

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._visibility_handlers: dict = {}

    @pyqtSlot(str, result=QObject)
    def getVisibilityHandler(self, handler_type: str) -> Optional[QObject]:
        """Return a shared visibility handler instance for the given type.

        Supported types: "ExtendedSettingPreference", "PerCategory", "InstanceContainer"
        """
        if handler_type not in self._visibility_handlers:
            handler: Optional[QObject] = None
            if handler_type == "PerCategory":
                handler = PerCategoryVisibilityHandler()
            elif handler_type == "InstanceContainer":
                handler = InstanceContainerVisibilityHandler()
            elif handler_type == "ExtendedSettingPreference":
                handler = ExtendedSettingPreferenceVisibilityHandler()
            else:
                Logger.log("w", "TabbedSettingsManager: unknown handler type '%s'", handler_type)
                return None  # type: ignore[return-value]
            self._visibility_handlers[handler_type] = handler

        return self._visibility_handlers[handler_type]
