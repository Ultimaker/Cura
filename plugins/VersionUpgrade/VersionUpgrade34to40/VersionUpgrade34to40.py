# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser
import io

from UM.VersionUpgrade import VersionUpgrade

deleted_settings = {"prime_tower_wall_thickness", "dual_pre_wipe", "prime_tower_purge_volume"}

##  Upgrades configurations from the state they were in at version 3.4 to the
#   state they should be in at version 4.0.
class VersionUpgrade34to40(VersionUpgrade):

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
    def getCfgVersion(self, serialised):
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialised)
        format_version = int(parser.get("general", "version")) #Explicitly give an exception when this fails. That means that the file format is not recognised.
        setting_version = int(parser.get("metadata", "setting_version", fallback = 0))
        return format_version * 1000000 + setting_version

    ##  Upgrades Preferences to have the new version number.
    def upgradePreferences(self, serialized, filename):
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        parser["general"]["version"] = "6"
        if "metadata" not in parser:
            parser["metadata"] = {}
        parser["metadata"]["setting_version"] = "5"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    ##  Upgrades stacks to have the new version number.
    def upgradeStack(self, serialized, filename):
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        parser["general"]["version"] = "4"
        parser["metadata"]["setting_version"] = "5"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    ##  Upgrades instance containers to have the new version
    #   number.
    def upgradeInstanceContainer(self, serialized, filename):
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        parser["general"]["version"] = "4"
        parser["metadata"]["setting_version"] = "5"

        self._resetConcentric3DInfillPattern(parser)
        if "values" in parser:
            for deleted_setting in deleted_settings:
                if deleted_setting not in parser["values"]:
                    continue
                del parser["values"][deleted_setting]

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def _resetConcentric3DInfillPattern(self, parser):
        if "values" not in parser:
            return

        # Reset the patterns which are concentric 3d
        for key in ("infill_pattern",
                    "support_pattern",
                    "support_interface_pattern",
                    "support_roof_pattern",
                    "support_bottom_pattern",
                    ):
            if key not in parser["values"]:
                continue
            if parser["values"][key] == "concentric_3d":
                del parser["values"][key]

