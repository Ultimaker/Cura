# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser #To parse preference files.
import io #To serialise the preference files afterwards.
from typing import Dict, List, Tuple

from UM.VersionUpgrade import VersionUpgrade #We're inheriting from this.

_renamed_settings = {
    "infill_hollow": "infill_support_enabled"
} # type: Dict[str, str]

##  Upgrades configurations from the state they were in at version 3.3 to the
#   state they should be in at version 3.4.
class VersionUpgrade33to34(VersionUpgrade):
    ##  Gets the version number from a CFG file in Uranium's 3.3 format.
    #
    #   Since the format may change, this is implemented for the 3.3 format only
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

        if "values" in parser:
            #If infill_hollow was enabled and the overhang angle was adjusted, copy that overhang angle to the new infill support angle.
            if "infill_hollow" in parser["values"] and parser["values"]["infill_hollow"] and "support_angle" in parser["values"]:
                parser["values"]["infill_support_angle"] = parser["values"]["support_angle"]

            #Renamed settings.
            for original, replacement in _renamed_settings.items():
                if original in parser["values"]:
                    parser["values"][replacement] = parser["values"][original]
                    del parser["values"][original]

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]