# Copyright (c) 2026 UltiMaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

"""Maintenance / preparation routines for USB-connected printers.

All G-code here uses only relative-safe moves and explicit temperatures.
Temperatures are *not* hardcoded: the caller (USBPrintingExtension) resolves
them from the active material profile and machine definition, so a TPU
profile with an unheated bed (0 C) behaves differently from a PLA profile.

Kept free of Qt/Cura imports so it stays unit-testable with plain pytest.
"""

from typing import List, Optional, Tuple

# Preheat temperature that softens filament for probing without oozing.
NO_OOZE_HOTEND_TEMP = 150

# Sanity caps: resolved values above these mean a broken profile, not a hot printer.
MAX_SANE_HOTEND_TEMP = 300
MAX_SANE_BED_TEMP = 130


def clean_temperature(value) -> Optional[int]:
    """Coerce a resolved profile temperature to int degrees, or None when unusable."""
    try:
        if value is None:
            return None
        result = int(round(float(value)))
    except (TypeError, ValueError):
        return None
    if result < 0:
        return None
    return result


def validate_maintenance_temps(hotend: Optional[int], bed: Optional[int]) -> Tuple[str, str]:
    """Check resolved temps before running a maintenance routine.

    Returns (status, reason) with status one of:
      "ok"             -- run immediately.
      "confirm_bed"    -- bed target is 0 (valid for e.g. TPU, wrong for PLA):
                          caller must ask the user to confirm.
      "blocked"        -- caller must refuse with the returned reason.
    """
    if hotend is None:
        return "blocked", "hotend temperature is not available (no material selected?)"
    if hotend <= 0:
        return "blocked", "hotend temperature is 0 C, heating is required"
    if hotend > MAX_SANE_HOTEND_TEMP:
        return "blocked", "hotend temperature %d C looks like a broken profile" % hotend
    if bed is None:
        return "blocked", "bed temperature is not available (no material selected?)"
    if bed > MAX_SANE_BED_TEMP:
        return "blocked", "bed temperature %d C looks like a broken profile" % bed
    if bed == 0:
        return "confirm_bed", "bed target is 0 C (unheated bed, normal for TPU)"
    return "ok", ""


def build_prep_script(hotend: int, bed: int) -> List[str]:
    """Heat (no-ooze) -> home -> auto-level -> heat to print temps.

    M190 is only included for a heated bed: M190 S0 could block while a
    warm bed cools down.
    """
    script = [
        "M140 S%d" % bed,
        "M104 S%d" % NO_OOZE_HOTEND_TEMP,
        "G28",
        "G29",
        "M109 S%d" % hotend,
    ]
    if bed > 0:
        script.append("M190 S%d" % bed)
    return script


def build_purge_script(hotend: int) -> List[str]:
    """Heat and extrude a purge blob with relative moves (printer-agnostic)."""
    return [
        "M109 S%d" % hotend,
        "G92 E0",
        "G91",
        "G1 E20 F150",
        "G1 E-2 F300",
        "G90",
        "G92 E0",
    ]


def build_unload_script(hotend: int) -> List[str]:
    """Heat, retract the filament clear of the extruder, then cool the hotend."""
    return [
        "M109 S%d" % hotend,
        "G92 E0",
        "G91",
        "G1 E-80 F300",
        "G90",
        "M104 S0",
    ]
