# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser #To parse the files we need to upgrade and write the new files.
import io #To serialise configparser output to a string.
from typing import Dict, List, Tuple

from UM.VersionUpgrade import VersionUpgrade

# a dict of renamed quality profiles:  <old_id> : <new_id>
_renamed_quality_profiles = {
    "um3_aa0.4_PVA_Not_Supported_Quality": "um3_aa0.4_PVA_Fast_Print",

    "um3_aa0.8_CPEP_Not_Supported_Quality": "um3_aa0.8_CPEP_Fast_Print",
    "um3_aa0.8_CPEP_Not_Supported_Superdraft_Quality": "um3_aa0.8_CPEP_Superdraft_Print",
    "um3_aa0.8_CPEP_Not_Supported_Verydraft_Quality": "um3_aa0.8_CPEP_Verydraft_Print",

    "um3_aa0.8_PC_Not_Supported_Quality": "um3_aa0.8_PC_Fast_Print",
    "um3_aa0.8_PC_Not_Supported_Superdraft_Quality": "um3_aa0.8_PC_Superdraft_Print",
    "um3_aa0.8_PC_Not_Supported_Verydraft_Quality": "um3_aa0.8_PC_Verydraft_Print",

    "um3_aa0.8_PVA_Not_Supported_Quality": "um3_aa0.8_PVA_Fast_Print",
    "um3_aa0.8_PVA_Not_Supported_Superdraft_Quality": "um3_aa0.8_PVA_Superdraft_Print",

    "um3_bb0.4_ABS_Not_Supported_Quality": "um3_bb0.4_ABS_Fast_print",
    "um3_bb0.4_ABS_Not_Supported_Superdraft_Quality": "um3_bb0.4_ABS_Superdraft_Print",

    "um3_bb0.4_CPE_Not_Supported_Quality": "um3_bb0.4_CPE_Fast_Print",
    "um3_bb0.4_CPE_Not_Supported_Superdraft_Quality": "um3_bb0.4_CPE_Superdraft_Print",

    "um3_bb0.4_CPEP_Not_Supported_Quality": "um3_bb0.4_CPEP_Fast_Print",
    "um3_bb0.4_CPEP_Not_Supported_Superdraft_Quality": "um3_bb0.4_CPEP_Superdraft_Print",

    "um3_bb0.4_Nylon_Not_Supported_Quality": "um3_bb0.4_Nylon_Fast_Print",
    "um3_bb0.4_Nylon_Not_Supported_Superdraft_Quality": "um3_bb0.4_Nylon_Superdraft_Print",

    "um3_bb0.4_PC_Not_Supported_Quality": "um3_bb0.4_PC_Fast_Print",

    "um3_bb0.4_PLA_Not_Supported_Quality": "um3_bb0.4_PLA_Fast_Print",
    "um3_bb0.4_PLA_Not_Supported_Superdraft_Quality": "um3_bb0.4_PLA_Superdraft_Print",

    "um3_bb0.4_TPU_Not_Supported_Quality": "um3_bb0.4_TPU_Fast_Print",
    "um3_bb0.4_TPU_Not_Supported_Superdraft_Quality": "um3_bb0.4_TPU_Superdraft_Print",

    "um3_bb0.8_ABS_Not_Supported_Quality": "um3_bb0.8_ABS_Fast_Print",
    "um3_bb0.8_ABS_Not_Supported_Superdraft_Quality": "um3_bb0.8_ABS_Superdraft_Print",

    "um3_bb0.8_CPE_Not_Supported_Quality": "um3_bb0.8_CPE_Fast_Print",
    "um3_bb0.8_CPE_Not_Supported_Superdraft_Quality": "um3_bb0.8_CPE_Superdraft_Print",

    "um3_bb0.8_CPEP_Not_Supported_Quality": "um3_bb0.um3_bb0.8_CPEP_Fast_Print",
    "um3_bb0.8_CPEP_Not_Supported_Superdraft_Quality": "um3_bb0.8_CPEP_Superdraft_Print",

    "um3_bb0.8_Nylon_Not_Supported_Quality": "um3_bb0.8_Nylon_Fast_Print",
    "um3_bb0.8_Nylon_Not_Supported_Superdraft_Quality": "um3_bb0.8_Nylon_Superdraft_Print",

    "um3_bb0.8_PC_Not_Supported_Quality": "um3_bb0.8_PC_Fast_Print",
    "um3_bb0.8_PC_Not_Supported_Superdraft_Quality": "um3_bb0.8_PC_Superdraft_Print",

    "um3_bb0.8_PLA_Not_Supported_Quality": "um3_bb0.8_PLA_Fast_Print",
    "um3_bb0.8_PLA_Not_Supported_Superdraft_Quality": "um3_bb0.8_PLA_Superdraft_Print",

    "um3_bb0.8_TPU_Not_Supported_Quality": "um3_bb0.8_TPU_Fast_print",
    "um3_bb0.8_TPU_Not_Supported_Superdraft_Quality": "um3_bb0.8_TPU_Superdraft_Print",
} # type: Dict[str, str]


##  A collection of functions that convert the configuration of the user in Cura
#   2.6 to a configuration for Cura 2.7.
#
#   All of these methods are essentially stateless.
class VersionUpgrade26to27(VersionUpgrade):
    ##  Upgrades a preferences file from version 2.6 to 2.7.
    #
    #   \param serialised The serialised form of a preferences file.
    #   \param filename The name of the file to upgrade.
    def upgradePreferences(self, serialised: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialised)

        # Update version numbers
        if "general" not in parser:
            parser["general"] = {}
        parser["general"]["version"] = "4"

        if "metadata" not in parser:
            parser["metadata"] = {}
        parser["metadata"]["setting_version"] = "2"

        #Renamed setting value for g-code flavour.
        if "values" in parser and "machine_gcode_flavor" in parser["values"]:
            if parser["values"]["machine_gcode_flavor"] == "RepRap (Volumatric)":
                parser["values"]["machine_gcode_flavor"] = "RepRap (Volumetric)"

        # Re-serialise the file.
        output = io.StringIO()
        parser.write(output)
        return [filename], [output.getvalue()]

    ##  Upgrades a container file other than a container stack file from version 2.6 to 2.7.
    #
    #   \param serialised The serialised form of a container file.
    #   \param filename The name of the file to upgrade.
    def upgradeOtherContainer(self, serialised: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialised)

        # Update version numbers
        if "general" not in parser:
            parser["general"] = {}
        parser["general"]["version"] = "2"

        if "metadata" not in parser:
            parser["metadata"] = {}
        parser["metadata"]["setting_version"] = "2"

        # Re-serialise the file.
        output = io.StringIO()
        parser.write(output)
        return [filename], [output.getvalue()]

    ##  Upgrades a container stack from version 2.6 to 2.7.
    #
    #   \param serialised The serialised form of a container stack.
    #   \param filename The name of the file to upgrade.
    def upgradeStack(self, serialised: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialised)

        # Update IDs of the renamed quality profiles
        if parser.has_section("containers"):
            key_list = [key for key in parser["containers"].keys()]
            for key in key_list:
                container_id = parser.get("containers", key)
                new_id = _renamed_quality_profiles.get(container_id)
                if new_id is not None:
                    parser.set("containers", key, new_id)

        if "6" not in parser["containers"]:
            parser["containers"]["6"] = parser["containers"]["5"]
            parser["containers"]["5"] = "empty"

        for each_section in ("general", "metadata"):
            if not parser.has_section(each_section):
                parser.add_section(each_section)

        # Update version numbers
        if "general" not in parser:
            parser["general"] = {}
        parser["general"]["version"] = "3"

        if "metadata" not in parser:
            parser["metadata"] = {}
        parser["metadata"]["setting_version"] = "2"

        # Re-serialise the file.
        output = io.StringIO()
        parser.write(output)
        return [filename], [output.getvalue()]
