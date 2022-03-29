# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser
from typing import Tuple, List
import io
from UM.VersionUpgrade import VersionUpgrade

_removed_settings = {
    "travel_compensate_overlapping_walls_enabled",
    "travel_compensate_overlapping_walls_0_enabled",
    "travel_compensate_overlapping_walls_x_enabled",
    "fill_perimeter_gaps",
    "filter_out_tiny_gaps",
    "wall_min_flow",
    "wall_min_flow_retract",
    "speed_equalize_flow_enabled",
    "speed_equalize_flow_min"
}


class VersionUpgrade413to50(VersionUpgrade):
    def upgradePreferences(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades preferences to remove from the visibility list the settings that were removed in this version.
        It also changes the preferences to have the new version number.

        This removes any settings that were removed in the new Cura version.
        :param serialized: The original contents of the preferences file.
        :param filename: The file name of the preferences file.
        :return: A list of new file names, and a list of the new contents for
        those files.
        """
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "19"

        # Remove deleted settings from the visible settings list.
        if "general" in parser and "visible_settings" in parser["general"]:
            visible_settings = set(parser["general"]["visible_settings"].split(";"))
            for removed in _removed_settings:
                if removed in visible_settings:
                    visible_settings.remove(removed)

            # Replace Outer Before Inner Walls with equivalent.
            if "outer_inset_first" in visible_settings:
                visible_settings.remove("outer_inset_first")
                visible_settings.add("inset_direction")

            parser["general"]["visible_settings"] = ";".join(visible_settings)

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeInstanceContainer(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades instance containers to remove the settings that were removed in this version.
        It also changes the instance containers to have the new version number.

        This removes any settings that were removed in the new Cura version and updates settings that need to be updated
        with a new value.

        :param serialized: The original contents of the instance container.
        :param filename: The original file name of the instance container.
        :return: A list of new file names, and a list of the new contents for
        those files.
        """
        parser = configparser.ConfigParser(interpolation = None, comment_prefixes = ())
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "19"

        if "values" in parser:
            # Remove deleted settings from the instance containers.
            for removed in _removed_settings:
                if removed in parser["values"]:
                    del parser["values"][removed]

            # Replace Outer Before Inner Walls with equivalent setting.
            if "outer_inset_first" in parser["values"]:
                old_value = parser["values"]["outer_inset_first"]
                if old_value.startswith("="):  # Was already a formula.
                    old_value = old_value[1:]
                parser["values"]["inset_direction"] = f"='outside_in' if ({old_value}) else 'inside_out'"  # Makes it work both with plain setting values and formulas.

            # Disable Fuzzy Skin as it doesn't work with with the libArachne walls
            if "magic_fuzzy_skin_enabled" in parser["values"]:
                parser["values"]["magic_fuzzy_skin_enabled"] = "False"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeStack(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades stacks to have the new version number.

        :param serialized: The original contents of the stack.
        :param filename: The original file name of the stack.
        :return: A list of new file names, and a list of the new contents for
        those files.
        """
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        if "metadata" not in parser:
            parser["metadata"] = {}

        parser["general"]["version"] = "5"
        parser["metadata"]["setting_version"] = "19"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]
