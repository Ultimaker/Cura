import ctypes
from ctypes import wintypes

import pytest

from cura.WindowsAccessibilityFilter import WindowsAccessibilityFilter


class Preferences:
    def __init__(self, value):
        self.value = value
        self.callback = None
        self.preferenceChanged = self

    def connect(self, callback):
        self.callback = callback

    def getValue(self, name):
        assert name == WindowsAccessibilityFilter.Preference
        return self.value

    def setValue(self, value):
        self.value = value
        self.callback(WindowsAccessibilityFilter.Preference)


@pytest.mark.parametrize("enabled", [True, "True", "true", 1])
def test_blocks_only_accessibility_queries(enabled):
    native_filter = WindowsAccessibilityFilter(Preferences(enabled))
    message = wintypes.MSG()
    for number in (0x0200, 0x0201, 0x0202, 0x0113, 0x000F, 0x0100):
        message.message = number
        assert native_filter.nativeEventFilter(b"windows_generic_MSG", ctypes.addressof(message)) == (False, 0)
    message.message = 0x003D
    assert native_filter.nativeEventFilter(b"windows_generic_MSG", ctypes.addressof(message)) == (True, 0)


def test_preference_changes_apply_without_restart():
    preferences = Preferences(True)
    native_filter = WindowsAccessibilityFilter(preferences)
    message = wintypes.MSG()
    message.message = 0x003D
    pointer = ctypes.addressof(message)
    preferences.setValue(False)
    assert native_filter.nativeEventFilter(b"windows_generic_MSG", pointer) == (False, 0)
    preferences.setValue(True)
    assert native_filter.nativeEventFilter(b"windows_generic_MSG", pointer) == (True, 0)


def test_other_platform_event_does_not_read_native_pointer():
    native_filter = WindowsAccessibilityFilter(Preferences(True))
    assert native_filter.nativeEventFilter(b"other_platform", 0) == (False, 0)
