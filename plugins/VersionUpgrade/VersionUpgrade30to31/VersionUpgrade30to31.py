# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser #To parse preference files.
import io #To serialise the preference files afterwards.
from typing import Dict, List, Set, Tuple

from UM.VersionUpgrade import VersionUpgrade #We're inheriting from this.


# a list of all legacy "Not Supported" quality profiles
_OLD_NOT_SUPPORTED_PROFILES = {
    "um2p_pp_0.25_normal",
    "um2p_tpu_0.8_normal",
    "um3_bb0.4_ABS_Fast_Print",
    "um3_bb0.4_ABS_Superdraft_Print",
    "um3_bb0.4_CPEP_Fast_Print",
    "um3_bb0.4_CPEP_Superdraft_Print",
    "um3_bb0.4_CPE_Fast_Print",
    "um3_bb0.4_CPE_Superdraft_Print",
    "um3_bb0.4_Nylon_Fast_Print",
    "um3_bb0.4_Nylon_Superdraft_Print",
    "um3_bb0.4_PC_Fast_Print",
    "um3_bb0.4_PLA_Fast_Print",
    "um3_bb0.4_PLA_Superdraft_Print",
    "um3_bb0.4_PP_Fast_Print",
    "um3_bb0.4_PP_Superdraft_Print",
    "um3_bb0.4_TPU_Fast_Print",
    "um3_bb0.4_TPU_Superdraft_Print",
    "um3_bb0.8_ABS_Fast_Print",
    "um3_bb0.8_ABS_Superdraft_Print",
    "um3_bb0.8_CPEP_Fast_Print",
    "um3_bb0.8_CPEP_Superdraft_Print",
    "um3_bb0.8_CPE_Fast_Print",
    "um3_bb0.8_CPE_Superdraft_Print",
    "um3_bb0.8_Nylon_Fast_Print",
    "um3_bb0.8_Nylon_Superdraft_Print",
    "um3_bb0.8_PC_Fast_Print",
    "um3_bb0.8_PC_Superdraft_Print",
    "um3_bb0.8_PLA_Fast_Print",
    "um3_bb0.8_PLA_Superdraft_Print",
    "um3_bb0.8_PP_Fast_Print",
    "um3_bb0.8_PP_Superdraft_Print",
    "um3_bb0.8_TPU_Fast_print",
    "um3_bb0.8_TPU_Superdraft_Print",
} # type: Set[str]


# Some containers have their specific empty containers, those need to be set correctly.
_EMPTY_CONTAINER_DICT = {
    "1": "empty_quality_changes",
    "2": "empty_quality",
    "3": "empty_material",
    "4": "empty_variant",
} # type: Dict[str, str]


# Renamed definition files
_RENAMED_DEFINITION_DICT = {
    "jellybox": "imade3d_jellybox",
} # type: Dict[str, str]


class VersionUpgrade30to31(VersionUpgrade):
    ##  Upgrades a preferences file from version 3.0 to 3.1.
    #
    #   \param serialised The serialised form of a preferences file.
    #   \param filename The name of the file to upgrade.
    def upgradePreferences(self, serialised: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialised)

        # Update version numbers
        if "general" not in parser:
            parser["general"] = {}
        parser["general"]["version"] = "5"
        if "metadata" not in parser:
            parser["metadata"] = {}
        parser["metadata"]["setting_version"] = "4"

        # Re-serialise the file.
        output = io.StringIO()
        parser.write(output)
        return [filename], [output.getvalue()]

    ##  Upgrades the given instance container file from version 3.0 to 3.1.
    #
    #   \param serialised The serialised form of the container file.
    #   \param filename The name of the file to upgrade.
    def upgradeInstanceContainer(self, serialised: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialised)

        for each_section in ("general", "metadata"):
            if not parser.has_section(each_section):
                parser.add_section(each_section)

        # Check renamed definitions
        if "definition" in parser["general"] and parser["general"]["definition"] in _RENAMED_DEFINITION_DICT:
            parser["general"]["definition"] = _RENAMED_DEFINITION_DICT[parser["general"]["definition"]]

        # Update version numbers
        parser["general"]["version"] = "2"
        parser["metadata"]["setting_version"] = "4"

        # Re-serialise the file.
        output = io.StringIO()
        parser.write(output)
        return [filename], [output.getvalue()]

    ##  Upgrades a container stack from version 3.0 to 3.1.
    #
    #   \param serialised The serialised form of a container stack.
    #   \param filename The name of the file to upgrade.
    def upgradeStack(self, serialised: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialised)

        for each_section in ("general", "metadata"):
            if not parser.has_section(each_section):
                parser.add_section(each_section)

        # change "not supported" quality profiles to empty because they no longer exist
        if parser.has_section("containers"):
            if parser.has_option("containers", "2"):
                quality_profile_id = parser["containers"]["2"]
                if quality_profile_id in _OLD_NOT_SUPPORTED_PROFILES:
                    parser["containers"]["2"] = "empty_quality"

            # fix empty containers
            for key, specific_empty_container in _EMPTY_CONTAINER_DICT.items():
                if parser.has_option("containers", key) and parser["containers"][key] == "empty":
                    parser["containers"][key] = specific_empty_container

            # check renamed definition
            if parser.has_option("containers", "6") and parser["containers"]["6"] in _RENAMED_DEFINITION_DICT:
                parser["containers"]["6"] = _RENAMED_DEFINITION_DICT[parser["containers"]["6"]]

        # Update version numbers
        if "general" not in parser:
            parser["general"] = {}
        parser["general"]["version"] = "3"

        if "metadata" not in parser:
            parser["metadata"] = {}
        parser["metadata"]["setting_version"] = "4"

        # Re-serialise the file.
        output = io.StringIO()
        parser.write(output)
        return [filename], [output.getvalue()]
