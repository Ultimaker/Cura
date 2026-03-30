# Copyright (c) 2026 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

import configparser
import io
from typing import Tuple, List

from UM.VersionUpgrade import VersionUpgrade

_REMOVED_SETTINGS = {
    "infill_randomize_start_location"
}

_NEW_SETTING_VERSION = "27"


class VersionUpgrade512to513(VersionUpgrade):
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
            # Update the randomize option to infill start/end preference
            if "infill_randomize_start_location" in parser["values"] and parser["values"]["infill_randomize_start_location"] == "True":
                parser["values"]["infill_start_end_preference"] = "start_random"

            # Remove deleted settings from the instance containers.
            for removed in _REMOVED_SETTINGS:
                if removed in parser["values"]:
                    del parser["values"][removed]

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
