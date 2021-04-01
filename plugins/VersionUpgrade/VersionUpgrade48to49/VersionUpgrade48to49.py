# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser
from typing import Tuple, List
import io

from UM.VersionUpgrade import VersionUpgrade


class VersionUpgrade48to49(VersionUpgrade):
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
        parser["metadata"]["setting_version"] = "17"

        # Update visibility settings to include new top_bottom category
        parser["general"]["visible_settings"] += ";top_bottom"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeInstanceContainer(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades instance containers to have the new version number.
        :param serialized: The original contents of the instance container.
        :param filename: The original file name of the instance container.
        :return: A list of new file names, and a list of the new contents for
        those files.
        """
        parser = configparser.ConfigParser(interpolation = None, comment_prefixes = ())
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "17"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeStack(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades stacks to have the new version number.

        This updates the post-processing scripts with new parameters.
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
        parser["metadata"]["setting_version"] = "17"

        # Update Display Progress on LCD script parameters if present.
        if "post_processing_scripts" in parser["metadata"]:
            new_scripts_entries = []
            for script_str in parser["metadata"]["post_processing_scripts"].split("\n"):
                if not script_str:
                    continue
                script_str = script_str.replace(r"\\\n", "\n").replace(r"\\\\", "\\\\")  # Unescape escape sequences.
                script_parser = configparser.ConfigParser(interpolation=None)
                script_parser.optionxform = str  # type: ignore  # Don't transform the setting keys as they are case-sensitive.
                script_parser.read_string(script_str)

                # Update Display Progress on LCD parameters.
                script_id = script_parser.sections()[0]
                if script_id == "DisplayProgressOnLCD":
                    script_parser[script_id]["time_remaining"] = "m117" if script_parser[script_id]["time_remaining"] == "True" else "none"

                script_io = io.StringIO()
                script_parser.write(script_io)
                script_str = script_io.getvalue()
                script_str = script_str.replace("\\\\", r"\\\\").replace("\n", r"\\\n")  # Escape newlines because configparser sees those as section delimiters.
                new_scripts_entries.append(script_str)
            parser["metadata"]["post_processing_scripts"] = "\n".join(new_scripts_entries)

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeSettingVisibility(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades setting visibility to have a version number and move moved settings to a different category

        This updates the post-processing scripts with new parameters.
        :param serialized: The original contents of the stack.
        :param filename: The original file name of the stack.
        :return: A list of new file names, and a list of the new contents for
        those files.
        """
        parser = configparser.ConfigParser(interpolation = None, allow_no_value=True)
        parser.read_string(serialized)

        moved_settings = ["top_bottom_extruder_nr", "top_bottom_thickness", "top_thickness", "top_layers",
                          "bottom_thickness", "bottom_layers", "ironing_enabled"]

        # add version number for the first time
        parser["general"]["version"] = "2"

        if "top_bottom" not in parser:
            parser["top_bottom"] = {}

        if "shell" in parser:
            for setting in parser["shell"]:
                if setting in moved_settings:
                    parser["top_bottom"][setting] = None
                    del parser["shell"][setting]

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]
