# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser
import io
from typing import Dict, List, Set, Tuple

from UM.VersionUpgrade import VersionUpgrade

deleted_settings = {"prime_tower_wall_thickness", "dual_pre_wipe", "prime_tower_purge_volume"} # type: Set[str]

changed_settings = {"retraction_combing": "noskin"} # type: Dict[str, str]
updated_settings = {"retraction_combing": "infill"} # type: Dict[str, str]

_RENAMED_MATERIAL_PROFILES = {
    "dsm_arnitel2045_175_cartesio_0.25_mm": "dsm_arnitel2045_175_cartesio_0.25mm_thermoplastic_extruder",
    "dsm_arnitel2045_175_cartesio_0.4_mm": "dsm_arnitel2045_175_cartesio_0.4mm_thermoplastic_extruder",
    "dsm_arnitel2045_175_cartesio_0.8_mm": "dsm_arnitel2045_175_cartesio_0.8mm_thermoplastic_extruder",
    "dsm_novamid1070_175_cartesio_0.25_mm": "dsm_novamid1070_175_cartesio_0.25mm_thermoplastic_extruder",
    "dsm_novamid1070_175_cartesio_0.4_mm": "dsm_novamid1070_175_cartesio_0.4mm_thermoplastic_extruder",
    "dsm_novamid1070_175_cartesio_0.8_mm": "dsm_novamid1070_175_cartesio_0.8mm_thermoplastic_extruder",
    "generic_abs_175_cartesio_0.25_mm": "generic_abs_175_cartesio_0.25mm_thermoplastic_extruder",
    "generic_abs_175_cartesio_0.4_mm": "generic_abs_175_cartesio_0.4mm_thermoplastic_extruder",
    "generic_abs_175_cartesio_0.8_mm": "generic_abs_175_cartesio_0.8mm_thermoplastic_extruder",
    "generic_hips_175_cartesio_0.25_mm": "generic_hips_175_cartesio_0.25mm_thermoplastic_extruder",
    "generic_hips_175_cartesio_0.4_mm": "generic_hips_175_cartesio_0.4mm_thermoplastic_extruder",
    "generic_hips_175_cartesio_0.8_mm": "generic_hips_175_cartesio_0.8mm_thermoplastic_extruder",
    "generic_nylon_175_cartesio_0.25_mm": "generic_nylon_175_cartesio_0.25mm_thermoplastic_extruder",
    "generic_nylon_175_cartesio_0.4_mm": "generic_nylon_175_cartesio_0.4mm_thermoplastic_extruder",
    "generic_nylon_175_cartesio_0.8_mm": "generic_nylon_175_cartesio_0.8mm_thermoplastic_extruder",
    "generic_pc_cartesio_0.25_mm": "generic_pc_cartesio_0.25mm_thermoplastic_extruder",
    "generic_pc_cartesio_0.4_mm": "generic_pc_cartesio_0.4mm_thermoplastic_extruder",
    "generic_pc_cartesio_0.8_mm": "generic_pc_cartesio_0.8mm_thermoplastic_extruder",
    "generic_pc_175_cartesio_0.25_mm": "generic_pc_175_cartesio_0.25mm_thermoplastic_extruder",
    "generic_pc_175_cartesio_0.4_mm": "generic_pc_175_cartesio_0.4mm_thermoplastic_extruder",
    "generic_pc_175_cartesio_0.8_mm": "generic_pc_175_cartesio_0.8mm_thermoplastic_extruder",
    "generic_petg_175_cartesio_0.25_mm": "generic_petg_175_cartesio_0.25mm_thermoplastic_extruder",
    "generic_petg_175_cartesio_0.4_mm": "generic_petg_175_cartesio_0.4mm_thermoplastic_extruder",
    "generic_petg_175_cartesio_0.8_mm": "generic_petg_175_cartesio_0.8mm_thermoplastic_extruder",
    "generic_pla_175_cartesio_0.25_mm": "generic_pla_175_cartesio_0.25mm_thermoplastic_extruder",
    "generic_pla_175_cartesio_0.4_mm": "generic_pla_175_cartesio_0.4mm_thermoplastic_extruder",
    "generic_pla_175_cartesio_0.8_mm": "generic_pla_175_cartesio_0.8mm_thermoplastic_extruder",
    "generic_pva_cartesio_0.25_mm": "generic_pva_cartesio_0.25mm_thermoplastic_extruder",
    "generic_pva_cartesio_0.4_mm": "generic_pva_cartesio_0.4mm_thermoplastic_extruder",
    "generic_pva_cartesio_0.8_mm": "generic_pva_cartesio_0.8mm_thermoplastic_extruder",
    "generic_pva_175_cartesio_0.25_mm": "generic_pva_175_cartesio_0.25mm_thermoplastic_extruder",
    "generic_pva_175_cartesio_0.4_mm": "generic_pva_175_cartesio_0.4mm_thermoplastic_extruder",
    "generic_pva_175_cartesio_0.8_mm": "generic_pva_175_cartesio_0.8mm_thermoplastic_extruder",
    "ultimaker_pc_black_cartesio_0.25_mm": "ultimaker_pc_black_cartesio_0.25mm_thermoplastic_extruder",
    "ultimaker_pc_black_cartesio_0.4_mm": "ultimaker_pc_black_cartesio_0.4mm_thermoplastic_extruder",
    "ultimaker_pc_black_cartesio_0.8_mm": "ultimaker_pc_black_cartesio_0.8mm_thermoplastic_extruder",
    "ultimaker_pc_transparent_cartesio_0.25_mm": "ultimaker_pc_transparent_cartesio_0.25mm_thermoplastic_extruder",
    "ultimaker_pc_transparent_cartesio_0.4_mm": "ultimaker_pc_transparent_cartesio_0.4mm_thermoplastic_extruder",
    "ultimaker_pc_transparent_cartesio_0.8_mm": "ultimaker_pc_transparent_cartesio_0.8mm_thermoplastic_extruder",
    "ultimaker_pc_white_cartesio_0.25_mm": "ultimaker_pc_white_cartesio_0.25mm_thermoplastic_extruder",
    "ultimaker_pc_white_cartesio_0.4_mm": "ultimaker_pc_white_cartesio_0.4mm_thermoplastic_extruder",
    "ultimaker_pc_white_cartesio_0.8_mm": "ultimaker_pc_white_cartesio_0.8mm_thermoplastic_extruder",
    "ultimaker_pva_cartesio_0.25_mm": "ultimaker_pva_cartesio_0.25mm_thermoplastic_extruder",
    "ultimaker_pva_cartesio_0.4_mm": "ultimaker_pva_cartesio_0.4mm_thermoplastic_extruder",
    "ultimaker_pva_cartesio_0.8_mm": "ultimaker_pva_cartesio_0.8mm_thermoplastic_extruder"
} # type: Dict[str, str]

##  Upgrades configurations from the state they were in at version 3.4 to the
#   state they should be in at version 3.5.
class VersionUpgrade34to35(VersionUpgrade):
    ##  Gets the version number from a CFG file in Uranium's 3.4 format.
    #
    #   Since the format may change, this is implemented for the 3.4 format only
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

    ##  Upgrades Preferences to have the new version number.
    def upgradePreferences(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Need to show the data collection agreement again because the data Cura collects has been changed.
        if parser.has_option("info", "asked_send_slice_info"):
            parser.set("info", "asked_send_slice_info", "False")
        if parser.has_option("info", "send_slice_info"):
            parser.set("info", "send_slice_info", "True")

        # Update version number.
        parser["general"]["version"] = "6"
        if "metadata" not in parser:
            parser["metadata"] = {}
        parser["metadata"]["setting_version"] = "5"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    ##  Upgrades stacks to have the new version number.
    def upgradeStack(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        parser["general"]["version"] = "4"
        parser["metadata"]["setting_version"] = "5"

        #Update the name of the quality profile.
        if parser["containers"]["3"] in _RENAMED_MATERIAL_PROFILES:
            parser["containers"]["3"] = _RENAMED_MATERIAL_PROFILES[parser["containers"]["3"]]

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    ##  Upgrades instance containers to have the new version
    #   number.
    def upgradeInstanceContainer(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
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

            for setting_key in changed_settings:
                if setting_key not in parser["values"]:
                    continue

                if parser["values"][setting_key] == changed_settings[setting_key]:
                    parser["values"][setting_key] = updated_settings[setting_key]

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def _resetConcentric3DInfillPattern(self, parser: configparser.ConfigParser) -> None:
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