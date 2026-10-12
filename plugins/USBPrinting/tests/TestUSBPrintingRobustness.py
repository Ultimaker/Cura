# Copyright (c) 2026 UltiMaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

"""Unit tests for the USB serial robustness hardening.

Covers: strict one-line-per-ok pacing, no position advance on readline
timeouts while printing, write-timeout retry without skipping lines,
resend-storm guard, stalled-print detection and the communication log.

Follows the repo's testing model: plain pytest functions with unittest.mock.
Run with: pytest plugins/USBPrinting/tests/ -v
"""

from collections import deque
from queue import Queue
from threading import Event
from time import time
from unittest.mock import MagicMock, patch

import pytest

from serial import SerialTimeoutException

from cura.PrinterOutput.PrinterOutputDevice import ConnectionState

from .. import USBPrinterOutputDevice as device_module
from .. import USBPrintingExtension as extension_module


def _make_device():
    """Build a USBPrinterOutputDevice without running __init__ (needs Qt app)."""
    device = device_module.USBPrinterOutputDevice.__new__(device_module.USBPrinterOutputDevice)
    device._id = "test-port"
    device._serial_port = "COM3"
    device._baud_rate = 115200
    device._timeout = 3
    device._gcode = ["G1 X10", "G1 X20", "G1 X30"]
    device._gcode_position = 0
    device._is_printing = True
    device._paused = False
    device._printer_busy = True  # Suppress the M105 temperature polling.
    device._firmware_name_requested = True  # Skip the M115 firmware request.
    device._firmware_idle_count = 0
    device._idle_timeouts_while_printing = 0
    device._last_busy_time = None
    device._resend_timestamps = deque()
    device._last_temperature_request = time()
    device._connection_state = ConnectionState.Connected
    device._command_queue = Queue()
    device._command_received = Event()
    device._command_received.set()
    device._serial = MagicMock()
    device._printers = [MagicMock()]
    device._print_start_time = time()
    device._print_estimated_time = 100
    device._comm_log_file = None
    device._firmware_name = None
    return device


def _make_preferences(store=None):
    store = dict(store) if store is not None else {}
    preferences = MagicMock()
    preferences.getValue.side_effect = lambda key: store.get(key)
    preferences.setValue.side_effect = lambda key, value: store.__setitem__(key, value)
    preferences.store = store
    return preferences


def test_initial_burst_is_single_line():
    # Bursting several lines risks overflowing small 8-bit RX buffers.
    assert device_module.INITIAL_BURST_LINES == 1


def test_ok_advances_one_line():
    device = _make_device()
    device._handleSerialLine(b"ok")
    assert device._gcode_position == 1
    sent = device._serial.write.call_args[0][0]
    assert sent.startswith(b"N0G1 X10*")


def test_read_timeouts_while_printing_do_not_advance():
    device = _make_device()
    device._handleSerialLine(b"")
    device._handleSerialLine(b"")
    device._handleSerialLine(b"")
    assert device._gcode_position == 0
    device._serial.write.assert_not_called()
    assert device._firmware_idle_count == 3


def test_read_timeouts_while_idle_still_flush_the_queue():
    device = _make_device()
    device._is_printing = False
    device._command_queue.put("M105")
    device._handleSerialLine(b"")
    device._serial.write.assert_not_called()
    device._handleSerialLine(b"")
    sent = device._serial.write.call_args[0][0]
    assert sent == b"M105\n"


def test_resend_rewinds_position():
    device = _make_device()
    device._gcode_position = 2
    device._handleSerialLine(b"Resend: 1")
    assert device._gcode_position == 1
    assert not device._paused


def test_resend_storm_pauses_print_and_warns():
    device = _make_device()
    with patch.object(device_module, "Message") as message_cls:
        for _ in range(device_module.RESEND_STORM_LIMIT):
            device._handleSerialLine(b"Resend: 1")
    assert device._paused
    device._printers[0].activePrintJob.updateState.assert_called_with("paused")
    message_cls.return_value.show.assert_called_once_with()


def test_stalled_print_closes_connection_and_warns():
    device = _make_device()
    with patch.object(device_module, "Message") as message_cls, \
         patch.object(device, "setConnectionState") as set_state, \
         patch.object(device_module, "MAX_IDLE_TIMEOUTS_WHILE_PRINTING", 3):
        device._handleSerialLine(b"")
        device._handleSerialLine(b"")
        assert device._is_printing  # Not yet: below the threshold.
        device._handleSerialLine(b"")
    assert not device._is_printing
    set_state.assert_called_once_with(ConnectionState.Error)
    message_cls.return_value.show.assert_called_once_with()


def test_write_timeout_does_not_advance_position_and_flushes_newline():
    device = _make_device()
    device._serial.write.side_effect = SerialTimeoutException("timeout")
    device._sendNextGcodeLine()
    assert device._gcode_position == 0
    # First the line, then a newline to flush the partial line from the firmware buffer.
    assert device._serial.write.call_count == 2
    assert device._serial.write.call_args[0][0] == b"\n"


def test_echo_busy_resets_idle_counters():
    device = _make_device()
    device._handleSerialLine(b"")
    device._handleSerialLine(b"echo:busy: processing")
    assert device._idle_timeouts_while_printing == 0
    assert device._firmware_idle_count == 0


def test_comm_log_records_tx_and_rx(tmp_path):
    device = _make_device()
    log_path = str(tmp_path / "usb-serial.log")
    preferences = _make_preferences({device_module.LOG_COMM_PREFERENCE_KEY: True})
    application = MagicMock()
    application.getPreferences.return_value = preferences
    with patch.object(device_module.CuraApplication, "getInstance", return_value=application), \
         patch.object(device_module, "getCommLogPath", return_value=log_path):
        device._openCommLog()
        device._handleSerialLine(b"ok")
        device._closeCommLog()
    content = open(log_path, encoding="utf-8").read()
    assert "TX" in content and "N0G1 X10" in content
    assert "RX" in content and "ok" in content


def test_comm_log_stays_closed_when_disabled(tmp_path):
    device = _make_device()
    preferences = _make_preferences({device_module.LOG_COMM_PREFERENCE_KEY: False})
    application = MagicMock()
    application.getPreferences.return_value = preferences
    with patch.object(device_module.CuraApplication, "getInstance", return_value=application), \
         patch.object(device_module, "getCommLogPath", return_value=str(tmp_path / "usb-serial.log")):
        device._openCommLog()
    assert device._comm_log_file is None


def test_extension_log_flag_roundtrip():
    extension = extension_module.USBPrintingExtension.__new__(extension_module.USBPrintingExtension)
    extension._dialog = None
    extension._cached_ports = []
    # Instances built without QObject.__init__ cannot emit real signals.
    extension.settingsChanged = MagicMock()
    extension.portsChanged = MagicMock()
    preferences = _make_preferences()
    application = MagicMock()
    application.getPreferences.return_value = preferences
    with patch.object(extension_module, "CuraApplication") as cura_app:
        cura_app.getInstance.return_value = application
        assert not extension.logCommunication
        extension.setLogCommunication(True)
        assert extension.logCommunication
        assert preferences.store[device_module.LOG_COMM_PREFERENCE_KEY] is True
