# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser
from typing import Tuple, List
import io

from UM.VersionUpgrade import VersionUpgrade


class VersionUpgrade47to48(VersionUpgrade):
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
        parser["metadata"]["setting_version"] = "16"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeInstanceContainer(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades instance containers to have the new version number.

        This this also changes the unit of the Scaling Factor Shrinkage
        Compensation setting.
        :param serialized: The original contents of the instance container.
        :param filename: The original file name of the instance container.
        :return: A list of new file names, and a list of the new contents for
        those files.
        """
        parser = configparser.ConfigParser(interpolation = None, comment_prefixes = ())
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "16"

        if "values" in parser:
            # Shrinkage factor used to be a percentage based around 0% (where 0% meant that it doesn't shrink or expand).
            # Since 4.8, it is a percentage based around 100% (where 100% means that it doesn't shrink or expand).
            if "material_shrinkage_percentage" in parser["values"]:
                shrinkage_percentage = parser["values"]["meshfix_maximum_deviation"]
                if shrinkage_percentage.startswith("="):
                    shrinkage_percentage = shrinkage_percentage[1:]
                shrinkage_percentage = "=(" + shrinkage_percentage + ") + 100"
                parser["values"]["material_shrinkage_percentage"] = shrinkage_percentage

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
        parser["metadata"]["setting_version"] = "16"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]
