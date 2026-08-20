# Copyright (c) 2026 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Settings.Models.SettingPreferenceVisibilityHandler import SettingPreferenceVisibilityHandler

from PyQt6.QtCore import pyqtSlot


class ExtendedSettingPreferenceVisibilityHandler(SettingPreferenceVisibilityHandler):
    """Extends SettingPreferenceVisibilityHandler with individual get/set methods for QML use."""

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent=parent, *args, **kwargs)

    @pyqtSlot(str, result=bool)
    def getSettingVisible(self, key: str) -> bool:
        return key in self.getVisible()

    @pyqtSlot(str, bool)
    def setSettingVisible(self, key: str, visible: bool) -> None:
        visible_settings = self.getVisible()
        if key in visible_settings and visible:
            return
        if key not in visible_settings and not visible:
            return

        if visible:
            visible_settings.add(key)
        else:
            visible_settings.remove(key)
        self.setVisible(visible_settings)
