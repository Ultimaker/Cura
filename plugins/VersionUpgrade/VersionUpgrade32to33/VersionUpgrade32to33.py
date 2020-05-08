# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser #To parse preference files.
import io #To serialise the preference files afterwards.
from typing import Dict, List, Tuple

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
} # type: Dict[str, int]

_RENAMED_QUALITY_PROFILES = {
    "low": "fast",
    "um2_low": "um2_fast"
} # type: Dict[str, str]

_RENAMED_QUALITY_TYPES = {
    "low": "fast"
} # type: Dict[str, str]

##  Upgrades configurations from the state they were in at version 3.2 to the
#   state they should be in at version 3.3.
class VersionUpgrade32to33(VersionUpgrade):
    temporary_group_name_counter = 1

    ##  Upgrades a preferences file from version 3.2 to 3.3.
    #
    #   \param serialised The serialised form of a preferences file.
    #   \param filename The name of the file to upgrade.
    def upgradePreferences(self, serialised: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialised)

        # Update version numbers
        if "general" not in parser:
            parser["general"] = {}
        parser["general"]["version"] = "6"
        if "metadata" not in parser:
            parser["metadata"] = {}
        parser["metadata"]["setting_version"] = "4"

        # The auto_slice preference changed its default value to "disabled" so if there is no value in previous versions,
        # then it means the desired value is auto_slice "enabled"
        if "auto_slice" not in parser["general"]:
            parser["general"]["auto_slice"] = "True"
        elif parser["general"]["auto_slice"] == "False":   # If the value is False, then remove the entry
            del parser["general"]["auto_slice"]

        # Re-serialise the file.
        output = io.StringIO()
        parser.write(output)
        return [filename], [output.getvalue()]

    ##  Upgrades a container stack from version 3.2 to 3.3.
    #
    #   \param serialised The serialised form of a container stack.
    #   \param filename The name of the file to upgrade.
    def upgradeStack(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        if "metadata" in parser and "um_network_key" in parser["metadata"]:
            if "hidden" not in parser["metadata"]:
                parser["metadata"]["hidden"] = "False"
            if "connect_group_name" not in parser["metadata"]:
                parser["metadata"]["connect_group_name"] = "Temporary group name #" + str(self.temporary_group_name_counter)
                self.temporary_group_name_counter += 1

        #Update version number.
        parser["general"]["version"] = "4"

        #Update the name of the quality profile.
        if parser["containers"]["2"] in _RENAMED_QUALITY_PROFILES:
            parser["containers"]["2"] = _RENAMED_QUALITY_PROFILES[parser["containers"]["2"]]

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    ##  Upgrades non-quality-changes instance containers to have the new version
    #   number.
    def upgradeInstanceContainer(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        #Update version number.
        parser["general"]["version"] = "3"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    ##  Upgrades a quality changes container to the new format.
    def upgradeQualityChanges(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
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

        quality_type = parser["metadata"]["quality_type"]
        quality_type = quality_type.lower()
        if quality_type in _RENAMED_QUALITY_TYPES:
            quality_type = _RENAMED_QUALITY_TYPES[quality_type]
        parser["metadata"]["quality_type"] = quality_type

        #Update version number.
        parser["general"]["version"] = "3"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    ##  Upgrades a variant container to the new format.
    def upgradeVariants(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        #Add the hardware type to the variants
        if "metadata" in parser and "hardware_type" not in parser["metadata"]:
            parser["metadata"]["hardware_type"] = "nozzle"

        #Update version number.
        parser["general"]["version"] = "3"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]