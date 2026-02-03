# Copyright (c) 2026 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

import configparser
import io
from typing import Tuple, List

from UM.VersionUpgrade import VersionUpgrade

_REMOVED_SETTINGS = {
    "skin_edge_support_thickness",
    "skin_edge_support_layers",
    "extra_infill_lines_to_support_skins",
    "bridge_sparse_infill_max_density",
}

_HIGH_SPEED_PRINTERS = {
    "ultimaker_factor4",
}

_OVERLAPPING_INFILLS = {
    "grid",
    "triangles",
    "cubic"
}

_NEW_SETTING_VERSION = "26"


class VersionUpgrade511to512(VersionUpgrade):
    def upgradePreferences(self, serialized: str, filename: str):
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = _NEW_SETTING_VERSION

        # Remove deleted settings from the visible settings list.
        if "general" in parser and "visible_settings" in parser["general"]:
            visible_settings = set(parser["general"]["visible_settings"].split(";"))
            for removed in _REMOVED_SETTINGS:
                if removed in visible_settings:
                    visible_settings.remove(removed)

            parser["general"]["visible_settings"] = ";".join(visible_settings)

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeInstanceContainer(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None, comment_prefixes = ())
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = _NEW_SETTING_VERSION

        if "values" in parser:
            # Enable the new skin_support based on the value of bridge_sparse_infill_max_density
            if "bridge_sparse_infill_max_density" in parser["values"]:
                parser["values"]["skin_support"] = f"=infill_sparse_density < {parser["values"]["bridge_sparse_infill_max_density"]}"

            # Remove deleted settings from the instance containers.
            for removed in _REMOVED_SETTINGS:
                if removed in parser["values"]:
                    del parser["values"][removed]

            # Force honeycomb infill pattern for high speed printers if using an overlapping pattern
            printer_definition = ""
            if "general" in parser and "definition" in parser["general"]:
                printer_definition = parser["general"]["definition"]

            infill_pattern = ""
            if "infill_pattern" in parser["values"]:
                infill_pattern = parser["values"]["infill_pattern"]

            if printer_definition in _HIGH_SPEED_PRINTERS and infill_pattern in _OVERLAPPING_INFILLS:
                parser["values"]["infill_pattern"] = "honeycomb"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeStack(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        if "metadata" not in parser:
            parser["metadata"] = {}

        parser["metadata"]["setting_version"] = _NEW_SETTING_VERSION

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]
