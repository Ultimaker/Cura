# Copyright (c) 2026 UltiMaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

"""Unit tests for the USB maintenance routines.

Covers: temperature cleanup/validation (0 C bed is valid for TPU, 0 C
hotend never is), script builders, device-side safety guards and the
extension confirm flow for an unheated bed.

Follows the repo's testing model: plain pytest functions with unittest.mock.
Run with: pytest plugins/USBPrinting/tests/ -v
"""

from threading import Event
from unittest.mock import MagicMock, patch

from cura.PrinterOutput.PrinterOutputDevice import ConnectionState

from .. import USBMaintenance as maint
from .. import USBPrinterOutputDevice as device_module
from .. import USBPrintingExtension as extension_module


def _make_device(connected=True, printing=False):
    device = device_module.USBPrinterOutputDevice.__new__(device_module.USBPrinterOutputDevice)
    device._serial = MagicMock() if connected else None
    device._connection_state = ConnectionState.Connected if connected else ConnectionState.Closed
    device._is_printing = printing
    device._comm_log_file = None
    device._command_received = Event()
    device._command_received.set()
    device.sendCommand = MagicMock()
    return device


def _make_extension():
    extension = extension_module.USBPrintingExtension.__new__(extension_module.USBPrintingExtension)
    extension._pending_maintenance = None
    return extension


# ---------------------------------------------------------------------------
# Temperature cleanup / validation
# ---------------------------------------------------------------------------

def test_clean_temperature_accepts_numbers_and_strings():
    assert maint.clean_temperature(210.0) == 210
    assert maint.clean_temperature("60") == 60
    assert maint.clean_temperature(0) == 0  # valid: unheated bed (TPU)


def test_clean_temperature_rejects_garbage():
    assert maint.clean_temperature(None) is None
    assert maint.clean_temperature("n/a") is None
    assert maint.clean_temperature(-5) is None


def test_validate_ok_for_normal_temps():
    assert maint.validate_maintenance_temps(210, 60)[0] == "ok"


def test_validate_zero_bed_needs_confirmation_not_block():
    status, reason = maint.validate_maintenance_temps(210, 0)
    assert status == "confirm_bed"
    assert reason != ""


def test_validate_zero_hotend_is_blocked():
    assert maint.validate_maintenance_temps(0, 60)[0] == "blocked"
    assert maint.validate_maintenance_temps(0, 0)[0] == "blocked"


def test_validate_missing_or_insane_values_blocked():
    assert maint.validate_maintenance_temps(None, 60)[0] == "blocked"
    assert maint.validate_maintenance_temps(210, None)[0] == "blocked"
    assert maint.validate_maintenance_temps(400, 60)[0] == "blocked"
    assert maint.validate_maintenance_temps(210, 200)[0] == "blocked"


# ---------------------------------------------------------------------------
# Script builders
# ---------------------------------------------------------------------------

def test_prep_script_heats_levels_then_soaks():
    script = maint.build_prep_script(210, 60)
    assert script.index("G28") < script.index("G29")
    assert "M109 S210" in script
    assert "M190 S60" in script
    # Full heat comes after probing (no-ooze heat first).
    assert script.index("M104 S150") < script.index("G28")


def test_prep_script_skips_bed_wait_for_unheated_bed():
    script = maint.build_prep_script(210, 0)
    assert "M140 S0" in script  # bed explicitly off
    assert not [line for line in script if line.startswith("M190")]


def test_purge_script_uses_relative_moves():
    script = maint.build_purge_script(210)
    assert "M109 S210" in script
    assert "G91" in script and "G90" in script
    assert "G1 E20 F150" in script


def test_unload_script_retracts_and_cools():
    script = maint.build_unload_script(230)
    assert "M109 S230" in script
    assert "G1 E-80 F300" in script
    assert script[-1] == "M104 S0"


# ---------------------------------------------------------------------------
# Device guards
# ---------------------------------------------------------------------------

def test_runMaintenanceScript_queues_when_idle_connected():
    device = _make_device()
    assert device.runMaintenanceScript(["G28", "G29"], "Prepare + Level") is True
    assert device.sendCommand.call_count == 2


def test_runMaintenanceScript_refuses_when_offline_or_printing():
    assert _make_device(connected=False).runMaintenanceScript(["G28"], "x") is False
    assert _make_device(printing=True).runMaintenanceScript(["G28"], "x") is False


# ---------------------------------------------------------------------------
# Extension flow
# ---------------------------------------------------------------------------

def test_maintenancePrepare_runs_directly_with_heated_bed():
    extension = _make_extension()
    device = MagicMock()
    message_cls = MagicMock()
    with patch.object(extension, "_getMaintenanceTemps", return_value=(210, 60)), \
         patch.object(extension, "_findIdleUsbDevice", return_value=device), \
         patch.object(extension_module, "Message", message_cls):
        extension.maintenancePrepare()
    device.runMaintenanceScript.assert_called_once()
    lines = device.runMaintenanceScript.call_args[0][0]
    assert "G28" in lines and "G29" in lines and "M190 S60" in lines


def test_maintenancePrepare_asks_confirmation_for_zero_bed():
    extension = _make_extension()
    device = MagicMock()
    message_cls = MagicMock()
    message = message_cls.return_value
    with patch.object(extension, "_getMaintenanceTemps", return_value=(230, 0)), \
         patch.object(extension, "_findIdleUsbDevice", return_value=device), \
         patch.object(extension_module, "Message", message_cls):
        extension.maintenancePrepare()
    device.runMaintenanceScript.assert_not_called()
    assert extension._pending_maintenance is not None
    action_ids = [call[0][0] for call in message.addAction.call_args_list]
    assert "run" in action_ids and "cancel" in action_ids
    message.show.assert_called_once()


def test_onMaintenanceAction_run_starts_pending_cancel_drops_it():
    extension = _make_extension()
    device = MagicMock()
    script = ["G28"]
    with patch.object(extension, "_findIdleUsbDevice", return_value=device), \
         patch.object(extension_module, "Message", MagicMock()):
        extension._pending_maintenance = ("Prepare + Level", script, 210, 0)
        extension._onMaintenanceAction(MagicMock(), "cancel")
        device.runMaintenanceScript.assert_not_called()
        assert extension._pending_maintenance is None

        extension._pending_maintenance = ("Prepare + Level", script, 210, 0)
        extension._onMaintenanceAction(MagicMock(), "run")
        device.runMaintenanceScript.assert_called_once_with(script, "Prepare + Level")


def test_maintenance_blocked_without_temps():
    extension = _make_extension()
    device = MagicMock()
    message_cls = MagicMock()
    with patch.object(extension, "_getMaintenanceTemps", return_value=(None, None)), \
         patch.object(extension, "_findIdleUsbDevice", return_value=device), \
         patch.object(extension_module, "Message", message_cls):
        extension.maintenancePurge()
    device.runMaintenanceScript.assert_not_called()
    message_cls.assert_called_once()  # error message shown
