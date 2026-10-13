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
| `usb_printing/log_communication` | `false` | Log all USB TX/RX traffic to `usb-serial.log` (checkbox in the settings dialog) |

When a manual port is set, the manager only watches that port. When a manual
baud rate is set, the device opens the serial port directly instead of
launching `AutoDetectBaudJob`.

## Serial robustness hardening

Intermittent mid-print head crashes (e.g. nozzle ramming to the X end) were
traced to plausible serial-protocol weaknesses, all mitigated in
`USBPrinterOutputDevice.py`:

- **Strict pacing**: only one line is sent up front and then one line per
  `ok` (`INITIAL_BURST_LINES = 1`). Bursting risks overflowing the small RX
  buffers of 8-bit boards; a dropped byte corrupts a line mid-print.
- **No advance on readline timeouts while printing**: an empty read only
  means "no data within 3 s", not "firmware idle". Advancing without a real
  `ok` piles unverified lines into the firmware buffer. After
  `MAX_IDLE_TIMEOUTS_WHILE_PRINTING` (40) consecutive timeouts with no
  `echo:busy` in between, the print is declared stalled: the user is warned
  and the connection is closed instead of corrupting moves.
- **Write-timeout retry without skipping**: if a line is not fully written,
  the position is kept so the same line number is retried, and a newline is
  flushed first so the firmware rejects the fragment cleanly (checksum error
  -> resend) instead of gluing the next line onto it.
- **Resend-storm guard**: 10 resends within 60 s pause the print with a
  warning (check cable / baud rate) instead of re-executing old lines forever.
- **Communication log**: when enabled, every TX/RX line is appended with a
  timestamp to `usb-serial.log` in the Cura config folder. On each new
  connection the previous session is preserved as `usb-serial.prev.log`
  (rotation, not truncation), so a mid-print glitch trace survives the
  reconnect or Cura restart that usually follows it.
- The update thread also survives single malformed lines (per-line
  try/except via the extracted `_handleSerialLine`).

## Files

| File | Role |
|---|---|
| `__init__.py` | Registers both `output_device` (manager) and `extension` (settings UI) |
| `USBPrinterOutputDeviceManager.py` | Port scanning, device lifecycle, manual-settings override (`getManualPort`, `getManualBaudRate`, `resolvePortList`, `reconnectWithManualSettings`) |
| `USBPrinterOutputDevice.py` | Serial protocol, G-code streaming, temperature parsing, robustness hardening (pacing, idle/timeout/resend guards, comm log) |
| `AutoDetectBaudJob.py` | Baud-rate probing, used only in `Auto` mode (unchanged) |
| `USBPrintingExtension.py` | Extension + menu entry, preference access, port listing, log flag for the dialog |
| `USBPrintingSettingsDialog.qml` | Settings dialog (port + baud dropdowns, refresh, reconnect, comm-log checkbox) |
| `MonitorItem.qml` | Monitor-stage panel (unchanged) |
| `tests/TestUSBPrintingManualSettings.py` | Unit tests for manual port/baud (17 tests, pytest + `unittest.mock`) |
| `tests/TestUSBPrintingRobustness.py` | Unit tests for pacing, timeouts, resends, stall detection, comm log |

## Status

- [x] Settings dialog opens from the Extensions menu (verified on Cura 5.12, fixed QML `contents` property error)
- [x] Manual baud rate skips auto-detection; manual port restricts scanning
- [x] Unit tests written (`pytest plugins/USBPrinting/tests/ -v`); logic verified with a stub harness where Qt deps were unavailable
- [x] Serial hardening implemented (pacing, idle guard, timeout retry, resend-storm guard, comm log); handler logic verified with a stub harness executing the real code (9 scenarios)
- [x] Reconnect closes stale handles (no more double handle / "Access denied" on the same port); comm log rotates to `usb-serial.prev.log` instead of truncating
- [ ] End-to-end test with a real printer over USB, with comm log enabled to capture the next glitch

## Local install (Windows, Cura 5.12)

1. Close Cura.
2. Back up `C:\Program Files\UltiMaker Cura 5.12.0\share\cura\plugins\USBPrinting`
   to `USBPrinting.orig` (admin rights required).
3. Copy this folder's contents over it. For later updates it is enough to
   re-copy the changed files (currently `__init__.py`,
   `USBPrinterOutputDevice.py`, `USBPrinterOutputDeviceManager.py`,
   `USBPrintingExtension.py`, `USBPrintingSettingsDialog.qml`).
4. Start Cura, enable USB printing in Preferences > General if needed, then
   use Extensions > USB Printing > USB Printing Settings...

## Capturing the next glitch

1. In the settings dialog, tick **Log USB communication to file**.
2. Print over USB as usual. Every TX/RX line lands with a timestamp in
   `usb-serial.log` inside the Cura config folder
   (`Help > Show Configuration Folder`). At each new connection the previous
   session is kept as `usb-serial.prev.log`, so reconnecting or restarting
   Cura after a glitch does not destroy the trace.
3. If the head crashes again, keep **both** log files: the last lines before the
   crash show whether a corrupted line, a resend storm or a silent printer
   caused it. Disable the checkbox afterwards (the file can grow several MB
   on long prints).
