# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser #To parse preference files.
import io #To serialise the preference files afterwards.

from UM.VersionUpgrade import VersionUpgrade #We're inheriting from this.


# a list of all legacy "Not Supported" quality profiles
_OLD_NOT_SUPPORTED_PROFILES = [
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
]


class VersionUpgrade30to31(VersionUpgrade):
    ##  Gets the version number from a CFG file in Uranium's 3.0 format.
    #
    #   Since the format may change, this is implemented for the 3.0 format only
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

    ##  Upgrades a preferences file from version 3.0 to 3.1.
    #
    #   \param serialised The serialised form of a preferences file.
    #   \param filename The name of the file to upgrade.
    def upgradePreferences(self, serialised, filename):
        parser = configparser.ConfigParser(interpolation=None)
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
    def upgradeInstanceContainer(self, serialised, filename):
        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(serialised)

        for each_section in ("general", "metadata"):
            if not parser.has_section(each_section):
                parser.add_section(each_section)

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
    def upgradeStack(self, serialised, filename):
        parser = configparser.ConfigParser(interpolation=None)
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
