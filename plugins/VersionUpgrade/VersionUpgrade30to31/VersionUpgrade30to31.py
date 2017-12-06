# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser #To parse preference files.
import io #To serialise the preference files afterwards.
import os
from urllib.parse import quote_plus

from UM.Resources import Resources
from UM.VersionUpgrade import VersionUpgrade #We're inheriting from this.

from cura.CuraApplication import CuraApplication


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


# Some containers have their specific empty containers, those need to be set correctly.
_EMPTY_CONTAINER_DICT = {
    "1": "empty_quality_changes",
    "2": "empty_quality",
    "3": "empty_material",
    "4": "empty_variant",
}


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

        # Copy global quality changes to extruder quality changes for single extrusion machines
        if parser["metadata"]["type"] == "quality_changes":
            all_quality_changes = self._getSingleExtrusionMachineQualityChanges(parser)
            # Note that DO NOT!!! use the quality_changes returned from _getSingleExtrusionMachineQualityChanges().
            # Those are loaded from the hard drive which are original files that haven't been upgraded yet.
            # NOTE 2: The number can be 0 or 1 depends on whether you are loading it from the qualities folder or
            #         from a project file. When you load from a project file, the custom profile may not be in cura
            #         yet, so you will get 0.
            if len(all_quality_changes) <= 1 and not parser.has_option("metadata", "extruder"):
                self._createExtruderQualityChangesForSingleExtrusionMachine(filename, parser)

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

            # fix empty containers
            for key, specific_empty_container in _EMPTY_CONTAINER_DICT.items():
                if parser.has_option("containers", key) and parser["containers"][key] == "empty":
                    parser["containers"][key] = specific_empty_container

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

    def _getSingleExtrusionMachineQualityChanges(self, quality_changes_container):
        quality_changes_dir = Resources.getPath(CuraApplication.ResourceTypes.QualityInstanceContainer)
        quality_changes_containers = []

        for item in os.listdir(quality_changes_dir):
            file_path = os.path.join(quality_changes_dir, item)
            if not os.path.isfile(file_path):
                continue

            parser = configparser.ConfigParser()
            try:
                parser.read([file_path])
            except:
                # skip, it is not a valid stack file
                continue

            if not parser.has_option("metadata", "type"):
                continue
            if "quality_changes" != parser["metadata"]["type"]:
                continue

            if not parser.has_option("general", "name"):
                continue
            if quality_changes_container["general"]["name"] != parser["general"]["name"]:
                continue

            quality_changes_containers.append(parser)

        return quality_changes_containers

    def _createExtruderQualityChangesForSingleExtrusionMachine(self, filename, global_quality_changes):
        suffix = "_" + quote_plus(global_quality_changes["general"]["name"].lower())
        machine_name = os.path.os.path.basename(filename).replace(".inst.cfg", "").replace(suffix, "")

        # Why is this here?!
        # When we load a .curaprofile file the deserialize will trigger a version upgrade, creating a dangling file.
        # This file can be recognized by it's lack of a machine name in the target filename.
        # So when we detect that situation here, we don't create the file and return.
        if machine_name == "":
            return

        new_filename = machine_name + "_" + "fdmextruder" + suffix

        extruder_quality_changes_parser = configparser.ConfigParser()
        extruder_quality_changes_parser.add_section("general")
        extruder_quality_changes_parser["general"]["version"] = str(2)
        extruder_quality_changes_parser["general"]["name"] = global_quality_changes["general"]["name"]
        extruder_quality_changes_parser["general"]["definition"] = global_quality_changes["general"]["definition"]

        extruder_quality_changes_parser.add_section("metadata")
        extruder_quality_changes_parser["metadata"]["quality_type"] = global_quality_changes["metadata"]["quality_type"]
        extruder_quality_changes_parser["metadata"]["type"] = global_quality_changes["metadata"]["type"]
        extruder_quality_changes_parser["metadata"]["setting_version"] = str(4)
        extruder_quality_changes_parser["metadata"]["extruder"] = "fdmextruder"

        extruder_quality_changes_output = io.StringIO()
        extruder_quality_changes_parser.write(extruder_quality_changes_output)
        extruder_quality_changes_filename = quote_plus(new_filename) + ".inst.cfg"

        quality_changes_dir = Resources.getPath(CuraApplication.ResourceTypes.QualityInstanceContainer)

        with open(os.path.join(quality_changes_dir, extruder_quality_changes_filename), "w") as f:
            f.write(extruder_quality_changes_output.getvalue())
