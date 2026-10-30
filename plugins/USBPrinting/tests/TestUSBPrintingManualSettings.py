# Copyright (c) 2026 UltiMaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

"""Unit tests for the manual COM port / baud rate settings of USBPrinting.

Follows the repo's testing model: plain pytest functions with unittest.mock
(see pytest.ini: Test*.py, and e.g. plugins/PostProcessingPlugin/tests/).
Run with: pytest plugins/USBPrinting/tests/ -v
"""

import pytest
from unittest.mock import MagicMock, patch

from ..USBPrinterOutputDeviceManager import (
    USBPrinterOutputDeviceManager,
    ALL_BAUD_RATES,
    USB_MANUAL_PORT_PREFERENCE_KEY,
    USB_MANUAL_BAUDRATE_PREFERENCE_KEY,
)
from ..USBPrintingExtension import USBPrintingExtension, AUTO_LABEL


# ---------------------------------------------------------------------------
# Helpers: build manager / extension without running their full __init__
# (which needs a real Qt application + singleton handling).
# ---------------------------------------------------------------------------

def _make_preferences(store=None):
    store = dict(store) if store is not None else {
        "usb_printing/enabled": True,
        USB_MANUAL_PORT_PREFERENCE_KEY: "",
        USB_MANUAL_BAUDRATE_PREFERENCE_KEY: "",
    }
    preferences = MagicMock()
    preferences.getValue.side_effect = lambda key: store.get(key)
    preferences.setValue.side_effect = lambda key, value: store.__setitem__(key, value)
    preferences.store = store
    return preferences


def _make_manager(preferences=None):
    preferences = preferences or _make_preferences()
    application = MagicMock()
    application.getPreferences.return_value = preferences
    manager = USBPrinterOutputDeviceManager.__new__(USBPrinterOutputDeviceManager)
    manager._application = application
    manager._serial_port_list = []
    manager._usb_output_devices = {}
    manager.addUSBOutputDeviceSignal = MagicMock()
    return manager


def _make_extension(preferences=None):
    preferences = preferences or _make_preferences()
    application = MagicMock()
    application.getPreferences.return_value = preferences
    extension = USBPrintingExtension.__new__(USBPrintingExtension)
    extension._dialog = None
    extension._cached_ports = []
    # Instances built without QObject.__init__ cannot emit real signals.
    extension.settingsChanged = MagicMock()
    extension.portsChanged = MagicMock()
    return extension, application


# ---------------------------------------------------------------------------
# Manager: preference parsing
# ---------------------------------------------------------------------------

def test_getManualPort_defaults_to_empty():
    assert _make_manager().getManualPort() == ""


def test_getManualPort_strips_whitespace():
    prefs = _make_preferences({USB_MANUAL_PORT_PREFERENCE_KEY: "  COM3  "})
    assert _make_manager(prefs).getManualPort() == "COM3"


@pytest.mark.parametrize("value", ["", None, "0", "Auto", "auto", "   "])
def test_getManualBaudRate_auto_variants_return_none(value):
    prefs = _make_preferences({USB_MANUAL_BAUDRATE_PREFERENCE_KEY: value})
    assert _make_manager(prefs).getManualBaudRate() is None


@pytest.mark.parametrize("baud_rate", ALL_BAUD_RATES)
def test_getManualBaudRate_valid_rates(baud_rate):
    prefs = _make_preferences({USB_MANUAL_BAUDRATE_PREFERENCE_KEY: str(baud_rate)})
    assert _make_manager(prefs).getManualBaudRate() == baud_rate


@pytest.mark.parametrize("value", ["999999", "abc", "115200.5", "-1"])
def test_getManualBaudRate_invalid_rates_return_none(value):
    prefs = _make_preferences({USB_MANUAL_BAUDRATE_PREFERENCE_KEY: value})
    assert _make_manager(prefs).getManualBaudRate() is None


# ---------------------------------------------------------------------------
# Manager: port list resolution (used by the 5s scan thread)
# ---------------------------------------------------------------------------

def test_resolvePortList_auto_keeps_scanned_ports():
    manager = _make_manager()
    assert manager.resolvePortList(["COM1", "COM2"]) == ["COM1", "COM2"]
    assert manager.resolvePortList([]) == []


def test_resolvePortList_manual_overrides_scan():
    prefs = _make_preferences({USB_MANUAL_PORT_PREFERENCE_KEY: "COM3"})
    manager = _make_manager(prefs)
    assert manager.resolvePortList(["COM1", "COM2", "COM3"]) == ["COM3"]
    # Even a port that disappeared from the scan is kept: the user chose it.
    assert manager.resolvePortList([]) == ["COM3"]


# ---------------------------------------------------------------------------
# Manager: device creation honors manual settings (skips auto-detection)
# ---------------------------------------------------------------------------

def test_addOutputDevice_auto_mode_passes_no_baud_rate():
    from .. import USBPrinterOutputDeviceManager as manager_module
    manager = _make_manager()
    device_cls = MagicMock()
    with patch.object(manager_module.USBPrinterOutputDevice, "USBPrinterOutputDevice", device_cls):
        manager.addOutputDevice("COM1")
    device_cls.assert_called_once_with("COM1", baud_rate=None)
    assert "COM1" in manager._usb_output_devices


def test_addOutputDevice_manual_baud_rate_is_passed_to_device():
    from .. import USBPrinterOutputDeviceManager as manager_module
    prefs = _make_preferences({
        USB_MANUAL_PORT_PREFERENCE_KEY: "COM3",
        USB_MANUAL_BAUDRATE_PREFERENCE_KEY: "250000",
    })
    manager = _make_manager(prefs)
    device_cls = MagicMock()
    with patch.object(manager_module.USBPrinterOutputDevice, "USBPrinterOutputDevice", device_cls):
        manager.addOutputDevice("COM3")
    device_cls.assert_called_once_with("COM3", baud_rate=250000)


def test_addOutputDevice_ignores_other_ports_when_manual_port_set():
    from .. import USBPrinterOutputDeviceManager as manager_module
    prefs = _make_preferences({USB_MANUAL_PORT_PREFERENCE_KEY: "COM3"})
    manager = _make_manager(prefs)
    device_cls = MagicMock()
    with patch.object(manager_module.USBPrinterOutputDevice, "USBPrinterOutputDevice", device_cls):
        manager.addOutputDevice("COM4")
    device_cls.assert_not_called()
    assert "COM4" not in manager._usb_output_devices


def test_addOutputDevice_closes_existing_device_for_same_port():
    from .. import USBPrinterOutputDeviceManager as manager_module
    manager = _make_manager()
    old_device = MagicMock()
    manager._usb_output_devices = {"COM1": old_device}
    device_cls = MagicMock()
    with patch.object(manager_module.USBPrinterOutputDevice, "USBPrinterOutputDevice", device_cls):
        manager.addOutputDevice("COM1")
    # The stale handle is closed before the new device takes its place, so
    # there is never more than one open handle on the same port.
    old_device.close.assert_called_once_with()
    device_cls.assert_called_once_with("COM1", baud_rate=None)
    assert manager._usb_output_devices["COM1"] is not old_device


# ---------------------------------------------------------------------------
# Manager: reconnect applies the stored settings
# ---------------------------------------------------------------------------

def test_reconnectWithManualSettings_closes_stale_and_readds_manual():
    manager = _make_manager(_make_preferences({USB_MANUAL_PORT_PREFERENCE_KEY: "COM3"}))
    stale = MagicMock()
    current = MagicMock()
    manager._usb_output_devices = {"COM9": stale, "COM3": current}
    manager._serial_port_list = ["COM9", "COM3"]
    with patch.object(manager, "_addRemovePorts") as add_remove:
        manager.reconnectWithManualSettings()
    # Both are closed: recreating COM3 without closing it first would leave
    # two open serial handles on the same port ("Access denied" writes).
    stale.close.assert_called_once_with()
    current.close.assert_called_once_with()
    add_remove.assert_called_once_with(["COM3"])


def test_reconnectWithManualSettings_auto_mode_resets_scan_list():
    manager = _make_manager()
    device = MagicMock()
    manager._usb_output_devices = {"COM1": device}
    manager._serial_port_list = ["COM1"]
    with patch.object(manager, "_addRemovePorts") as add_remove:
        manager.reconnectWithManualSettings()
    device.close.assert_called_once_with()
    add_remove.assert_not_called()
    assert manager._serial_port_list == []


# ---------------------------------------------------------------------------
# Extension: options, validation, persistence
# ---------------------------------------------------------------------------

def test_baudRateOptions_starts_with_auto_and_contains_all_rates():
    extension, _ = _make_extension()
    options = list(extension.baudRateOptions)
    assert options[0] == AUTO_LABEL
    for baud_rate in ALL_BAUD_RATES:
        assert str(baud_rate) in options


def test_setManualPort_stores_trimmed_value():
    from .. import USBPrintingExtension as extension_module
    extension, application = _make_extension()
    with patch.object(extension_module, "CuraApplication") as cura_app:
        cura_app.getInstance.return_value = application
        extension.setManualPort("  COM3  ")
    assert application.getPreferences.return_value.store[USB_MANUAL_PORT_PREFERENCE_KEY] == "COM3"


def test_setManualPort_auto_clears_value():
    from .. import USBPrintingExtension as extension_module
    extension, application = _make_extension()
    application.getPreferences.return_value.store[USB_MANUAL_PORT_PREFERENCE_KEY] = "COM3"
    with patch.object(extension_module, "CuraApplication") as cura_app:
        cura_app.getInstance.return_value = application
        extension.setManualPort(AUTO_LABEL)
    assert application.getPreferences.return_value.store[USB_MANUAL_PORT_PREFERENCE_KEY] == ""


def test_setManualBaudRate_accepts_known_rate():
    from .. import USBPrintingExtension as extension_module
    extension, application = _make_extension()
    with patch.object(extension_module, "CuraApplication") as cura_app:
        cura_app.getInstance.return_value = application
        extension.setManualBaudRate("115200")
    assert application.getPreferences.return_value.store[USB_MANUAL_BAUDRATE_PREFERENCE_KEY] == "115200"


@pytest.mark.parametrize("value", ["999999", "not-a-number", ""])
def test_setManualBaudRate_rejects_unknown_rate(value):
    from .. import USBPrintingExtension as extension_module
    extension, application = _make_extension()
    application.getPreferences.return_value.store[USB_MANUAL_BAUDRATE_PREFERENCE_KEY] = "115200"
    with patch.object(extension_module, "CuraApplication") as cura_app:
        cura_app.getInstance.return_value = application
        if value == "":
            extension.setManualBaudRate(AUTO_LABEL)  # Auto must clear, not keep.
            assert application.getPreferences.return_value.store[USB_MANUAL_BAUDRATE_PREFERENCE_KEY] == ""
        else:
            extension.setManualBaudRate(value)  # Invalid values are ignored.
            assert application.getPreferences.return_value.store[USB_MANUAL_BAUDRATE_PREFERENCE_KEY] == "115200"


def test_reconnect_delegates_to_manager():
    from .. import USBPrinterOutputDeviceManager as manager_module
    from .. import USBPrintingExtension as extension_module
    extension, application = _make_extension()
    manager = MagicMock()
    with patch.object(extension_module, "CuraApplication") as cura_app, \
         patch.object(manager_module.USBPrinterOutputDeviceManager, "getInstance", return_value=manager):
        cura_app.getInstance.return_value = application
        extension.reconnect()
    manager.reconnectWithManualSettings.assert_called_once_with()


def test_reconnect_without_manager_does_not_raise():
    from .. import USBPrinterOutputDeviceManager as manager_module
    from .. import USBPrintingExtension as extension_module
    extension, application = _make_extension()
    with patch.object(extension_module, "CuraApplication") as cura_app, \
         patch.object(manager_module.USBPrinterOutputDeviceManager, "getInstance", return_value=None):
        cura_app.getInstance.return_value = application
        extension.reconnect()  # Must not raise; logs a warning instead.
