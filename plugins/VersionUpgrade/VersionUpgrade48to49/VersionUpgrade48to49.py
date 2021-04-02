# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser
from typing import Tuple, List
import io

from UM.VersionUpgrade import VersionUpgrade


class VersionUpgrade48to49(VersionUpgrade):
    _moved_visibility_settings = ["top_bottom_extruder_nr", "top_bottom_thickness", "top_thickness", "top_layers",
                                  "bottom_thickness", "bottom_layers", "ironing_enabled"]

    def upgradePreferences(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades preferences to have the new version number.
        :param serialized: The original contents of the preferences file.
        :param filename: The file name of the preferences file.
        :return: A list of new file names, and a list of the new contents for
        those files.
        """
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        parser["general"]["version"] = "7"

        # Update visibility settings to include new top_bottom category
        parser["general"]["visible_settings"] += ";top_bottom"

        if any([setting in parser["cura"]["categories_expanded"] for setting in self._moved_visibility_settings]):
            parser["cura"]["categories_expanded"] += ";top_bottom"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeSettingVisibility(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades setting visibility to have a version number and move moved settings to a different category

        :param serialized: The original contents of the stack.
        :param filename: The original file name of the stack.
        :return: A list of new file names, and a list of the new contents for
        those files.
        """
        parser = configparser.ConfigParser(interpolation = None, allow_no_value=True)
        parser.read_string(serialized)

        # add version number for the first time
        parser["general"]["version"] = "2"

        if "top_bottom" not in parser:
            parser["top_bottom"] = {}

        if "shell" in parser:
            for setting in parser["shell"]:
                if setting in self._moved_visibility_settings:
                    parser["top_bottom"][setting] = None
                    del parser["shell"][setting]

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]
