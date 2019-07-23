# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser
import io
import uuid
from typing import Dict, List, Tuple

from UM.VersionUpgrade import VersionUpgrade

_renamed_quality_profiles = {
    "gmax15plus_pla_dual_normal": "gmax15plus_global_dual_normal",
    "gmax15plus_pla_dual_thick": "gmax15plus_global_dual_thick",
    "gmax15plus_pla_dual_thin": "gmax15plus_global_dual_thin",
    "gmax15plus_pla_dual_very_thick": "gmax15plus_global_dual_very_thick",
    "gmax15plus_pla_normal": "gmax15plus_global_normal",
    "gmax15plus_pla_thick": "gmax15plus_global_thick",
    "gmax15plus_pla_thin": "gmax15plus_global_thin",
    "gmax15plus_pla_very_thick": "gmax15plus_global_very_thick"
} # type: Dict[str, str]


##  Upgrades configurations from the state they were in at version 4.0 to the
#   state they should be in at version 4.1.
class VersionUpgrade40to41(VersionUpgrade):
    ##  Gets the version number from a CFG file in Uranium's 4.0 format.
    #
    #   Since the format may change, this is implemented for the 4.0 format only
    #   and needs to be included in the version upgrade system rather than
    #   globally in Uranium.
    #
    #   \param serialised The serialised form of a CFG file.
    #   \return The version number stored in the CFG file.
    #   \raises ValueError The format of the version number in the file is
    #   incorrect.
    #   \raises KeyError The format of the file is incorrect.
    def getCfgVersion(self, serialised: str) -> int:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialised)
        format_version = int(parser.get("general", "version")) #Explicitly give an exception when this fails. That means that the file format is not recognised.
        setting_version = int(parser.get("metadata", "setting_version", fallback = "0"))
        return format_version * 1000000 + setting_version

    ##  Upgrades instance containers to have the new version
    #   number.
    def upgradeInstanceContainer(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        parser["general"]["version"] = "4"
        parser["metadata"]["setting_version"] = "7"

        # Limit Maximum Deviation instead of Maximum Resolution. This should have approximately the same effect as before the algorithm change, only more consistent.
        if "values" in parser and "meshfix_maximum_resolution" in parser["values"]:
            resolution = parser["values"]["meshfix_maximum_resolution"]
            if resolution.startswith("="):
                resolution = resolution[1:]
            deviation = "=(" + resolution + ") / 2"
            parser["values"]["meshfix_maximum_deviation"] = deviation
            del parser["values"]["meshfix_maximum_resolution"]

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    ##  Upgrades Preferences to have the new version number.
    def upgradePreferences(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        parser["general"]["version"] = "6"
        if "metadata" not in parser:
            parser["metadata"] = {}

        # Remove changelog plugin
        if "latest_version_changelog_shown" in parser["general"]:
            del parser["general"]["latest_version_changelog_shown"]

        parser["metadata"]["setting_version"] = "7"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    ##  Upgrades stacks to have the new version number.
    def upgradeStack(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        parser["general"]["version"] = "4"
        parser["metadata"]["setting_version"] = "7"

        #Update the name of the quality profile.
        if parser["containers"]["4"] in _renamed_quality_profiles:
            parser["containers"]["4"] = _renamed_quality_profiles[parser["containers"]["4"]]

        # Assign a GlobalStack to a unique group_id. If the GlobalStack has a UM network connection, use the UM network
        # key as the group_id.
        if "um_network_key" in parser["metadata"]:
            parser["metadata"]["group_id"] = parser["metadata"]["um_network_key"]
        elif "group_id" not in parser["metadata"]:
            parser["metadata"]["group_id"] = str(uuid.uuid4())

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]
