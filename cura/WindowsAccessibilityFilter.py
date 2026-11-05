# Cura is released under the terms of the LGPLv3 or higher.

import ctypes
from ctypes import wintypes
from typing import Tuple

from PyQt6.QtCore import QAbstractNativeEventFilter

from UM.Preferences import Preferences


class WindowsAccessibilityFilter(QAbstractNativeEventFilter):
    """Control external accessibility discovery for Cura's Windows interface."""

    Preference = "general/block_windows_accessibility_queries"
    _WM_GETOBJECT = 0x003D

    def __init__(self, preferences: Preferences) -> None:
        super().__init__()
        self._preferences = preferences
        self._blocked = False
        self._onPreferenceChanged(self.Preference)
        preferences.preferenceChanged.connect(self._onPreferenceChanged)

    def _onPreferenceChanged(self, name: str) -> None:
        if name == self.Preference:
            value = self._preferences.getValue(self.Preference)
            self._blocked = value is True or str(value).lower() in ("true", "1")

    def nativeEventFilter(self, event_type, message) -> Tuple[bool, int]:
        if not self._blocked or bytes(event_type) not in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            return False, 0

        # WM_GETOBJECT asks the application to expose an accessibility object.
        # Do not inspect message payloads or intercept input/painting messages.
        native_message = ctypes.cast(int(message), ctypes.POINTER(wintypes.MSG)).contents
        if native_message.message == self._WM_GETOBJECT:
            return True, 0
        return False, 0
