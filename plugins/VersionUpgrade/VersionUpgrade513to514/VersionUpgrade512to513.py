# Copyright (c) 2026 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

import configparser
import io
from typing import Tuple, List

from UM.VersionUpgrade import VersionUpgrade

_REMOVED_SETTINGS = {}

_NEW_SETTING_VERSION = "28"


class VersionUpgrade512to513(VersionUpgrade):
    def upgradePreferences(self, serialized: str, filename: str):
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = _NEW_SETTING_VERSION

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeInstanceContainer(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None, comment_prefixes = ())
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = _NEW_SETTING_VERSION

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
