# USBPrinting

Cura plugin (bundled) for printing over a USB serial connection.

## What it does

- Watches the system's serial ports and creates one `USBPrinterOutputDevice`
  per port (`USBPrinterOutputDeviceManager`, one scan every 5 s).
- Streams the sliced G-code to the printer over `pyserial`, with line numbers
  and checksums (`N<num><line>*<checksum>`), one command in flight at a time.
- Polls temperatures (`M105`), reads the firmware name (`M115`), tracks
  `ok` / `echo:busy` / `resend` / `!!` responses, and reports progress through
  `PrintJobOutputModel`.
- Supports pausing / resuming / cancelling prints and AVR firmware updates
  (`avr_isp/` + `AvrFirmwareUpdater`).
- When no baud rate is known, it probes all common rates with
  `AutoDetectBaudJob`, which is **very slow** (tens of seconds to minutes).

## Manual port / baud rate settings (custom addition)

To skip the slow auto-detection, this fork adds an `Extension` with a
settings dialog: **Extensions > USB Printing > USB Printing Settings...**

- **COM port** dropdown (`Auto` = keep scanning all ports, as before).
- **Baud rate** dropdown (`Auto` = probe all rates, as before).
- `Reconnect now` button applies the selection immediately.

Settings are stored as Cura preferences (persisted in `cura.cfg`):

| Key | Default | Meaning |
|---|---|---|
| `usb_printing/enabled` | `false` | Master switch (checkbox in Preferences > General) |
| `usb_printing/manual_port` | `""` | Fixed port, e.g. `COM3`. Empty = auto-scan |
| `usb_printing/manual_baudrate` | `""` | Fixed rate, e.g. `115200`. Empty = auto-detect |

When a manual port is set, the manager only watches that port. When a manual
baud rate is set, the device opens the serial port directly instead of
launching `AutoDetectBaudJob`.

## Files

| File | Role |
|---|---|
| `__init__.py` | Registers both `output_device` (manager) and `extension` (settings UI) |
| `USBPrinterOutputDeviceManager.py` | Port scanning, device lifecycle, manual-settings override (`getManualPort`, `getManualBaudRate`, `resolvePortList`, `reconnectWithManualSettings`) |
| `USBPrinterOutputDevice.py` | Serial protocol, G-code streaming, temperature parsing (unchanged) |
| `AutoDetectBaudJob.py` | Baud-rate probing, used only in `Auto` mode (unchanged) |
| `USBPrintingExtension.py` | Extension + menu entry, preference access, port listing for the dialog |
| `USBPrintingSettingsDialog.qml` | Settings dialog (port + baud dropdowns, refresh, reconnect) |
| `MonitorItem.qml` | Monitor-stage panel (unchanged) |
| `tests/TestUSBPrintingManualSettings.py` | Unit tests (17 tests, pytest + `unittest.mock`) |

## Status

- [x] Settings dialog opens from the Extensions menu (verified on Cura 5.12, fixed QML `contents` property error)
- [x] Manual baud rate skips auto-detection; manual port restricts scanning
- [x] Unit tests written (`pytest plugins/USBPrinting/tests/ -v`); logic verified with a stub harness where Qt deps were unavailable
- [ ] End-to-end test with a real printer over USB
- [ ] Optional: per-printer persistence, connection-status feedback in the dialog

## Local install (Windows, Cura 5.12)

1. Close Cura.
2. Back up `C:\Program Files\UltiMaker Cura 5.12.0\share\cura\plugins\USBPrinting`
   to `USBPrinting.orig` (admin rights required).
3. Copy this folder's contents over it.
4. Start Cura, enable USB printing in Preferences > General if needed, then
   use Extensions > USB Printing > USB Printing Settings...
