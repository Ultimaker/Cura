# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser #To parse preference files.
import io #To serialise the preference files afterwards.

from UM.VersionUpgrade import VersionUpgrade #We're inheriting from this.

##  Mapping extruder definition IDs to the positions that they are in.
_EXTRUDER_TO_POSITION = {
    "builder_premium_large_front": 1,
    "builder_premium_large_rear": 0,
    "builder_premium_medium_front": 1,
    "builder_premium_medium_rear": 0,
    "builder_premium_small_front": 1,
    "builder_premium_small_rear": 0,
    "cartesio_extruder_0": 0,
    "cartesio_extruder_1": 1,
    "cartesio_extruder_2": 2,
    "cartesio_extruder_3": 3,
    "custom_extruder_1": 0, #Warning, non-programmers are attempting to count here.
    "custom_extruder_2": 1,
    "custom_extruder_3": 2,
    "custom_extruder_4": 3,
    "custom_extruder_5": 4,
    "custom_extruder_6": 5,
    "custom_extruder_7": 6,
    "custom_extruder_8": 7,
    "hBp_extruder_left": 0,
    "hBp_extruder_right": 1,
    "makeit_dual_1st": 0,
    "makeit_dual_2nd": 1,
    "makeit_l_dual_1st": 0,
    "makeit_l_dual_2nd": 1,
    "ord_extruder_0": 0,
    "ord_extruder_1": 1,
    "ord_extruder_2": 2,
    "ord_extruder_3": 3,
    "ord_extruder_4": 4,
    "punchtec_connect_xl_extruder_left": 0,
    "punchtec_connect_xl_extruder_right": 1,
    "raise3D_N2_dual_extruder_0": 0,
    "raise3D_N2_dual_extruder_1": 1,
    "raise3D_N2_plus_dual_extruder_0": 0,
    "raise3D_N2_plus_dual_extruder_1": 1,
    "ultimaker3_extended_extruder_left": 0,
    "ultimaker3_extended_extruder_right": 1,
    "ultimaker3_extruder_left": 0,
    "ultimaker3_extruder_right": 1,
    "ultimaker_original_dual_1st": 0,
    "ultimaker_original_dual_2nd": 1,
    "vertex_k8400_dual_1st": 0,
    "vertex_k8400_dual_2nd": 1
}

##  Upgrades configurations from the state they were in at version 3.2 to the
#   state they should be in at version 3.3.
class VersionUpgrade32to33(VersionUpgrade):
    ##  Gets the version number from a CFG file in Uranium's 3.2 format.
    #
    #   Since the format may change, this is implemented for the 3.2 format only
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

    ##  Upgrades non-quality-changes instance containers to have the new version
    #   number.
    def upgradeInstanceContainer(self, serialized, filename):
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        #Update version number.
        parser["general"]["version"] = "3"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    ##  Upgrades a quality changes container to the new format.
    def upgradeQualityChanges(self, serialized, filename):
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        #Extruder quality changes profiles have the extruder position instead of the ID of the extruder definition.
        if "metadata" in parser and "extruder" in parser["metadata"]: #Only do this for extruder profiles.
            extruder_id = parser["metadata"]["extruder"]
            if extruder_id in _EXTRUDER_TO_POSITION:
                extruder_position = _EXTRUDER_TO_POSITION[extruder_id]
            else:
                extruder_position = 0 #The user was using custom extruder definitions. He's on his own then.

            parser["metadata"]["position"] = str(extruder_position)
            del parser["metadata"]["extruder"]

        #Update version number.
        parser["general"]["version"] = "3"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]