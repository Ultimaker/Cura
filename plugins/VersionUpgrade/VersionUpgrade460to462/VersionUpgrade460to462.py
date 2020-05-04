# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser
from typing import Tuple, List
import io
from UM.VersionUpgrade import VersionUpgrade

class VersionUpgrade460to462(VersionUpgrade):
    def getCfgVersion(self, serialised: str) -> int:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialised)
        format_version = int(parser.get("general", "version"))  # Explicitly give an exception when this fails. That means that the file format is not recognised.
        setting_version = int(parser.get("metadata", "setting_version", fallback = "0"))
        return format_version * 1000000 + setting_version

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
        parser["metadata"]["setting_version"] = "13"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeInstanceContainer(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades instance containers to have the new version number.

        This changes the maximum deviation setting if that setting was present
        in the profile.
        :param serialized: The original contents of the instance container.
        :param filename: The original file name of the instance container.
        :return: A list of new file names, and a list of the new contents for
        those files.
        """
        parser = configparser.ConfigParser(interpolation = None, comment_prefixes = ())
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "13"

        if "values" in parser:
            # Maximum Deviation's effect was corrected. Previously the deviation
            # ended up being only half of what the user had entered. This was
            # fixed in Cura 4.7 so there we need to halve the deviation that the
            # user had entered.
            if "meshfix_maximum_deviation" in parser["values"]:
                maximum_deviation = parser["values"]["meshfix_maximum_deviation"]
                if maximum_deviation.startswith("="):
                    maximum_deviation = maximum_deviation[1:]
                maximum_deviation = "=(" + maximum_deviation + ") / 2"
                parser["values"]["meshfix_maximum_deviation"] = maximum_deviation

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
        parser["metadata"]["setting_version"] = "13"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]
