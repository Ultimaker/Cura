# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser
import io
import os.path  # To get the file ID.
from typing import Dict, List, Tuple

from UM.VersionUpgrade import VersionUpgrade

_renamed_settings = {
    "support_minimal_diameter": "support_tower_maximum_supported_diameter"
}  # type: Dict[str, str]
_removed_settings = ["prime_tower_circular", "max_feedrate_z_override"]  # type: List[str]
_renamed_profiles = {
    # Include CreawsomeMod profiles here as well for the people who installed that.
    # Definitions.
    "creawsome_base": "creality_base",
    "creawsome_cr10": "creality_cr10",
    "creawsome_cr10mini": "creality_cr10mini",
    "creawsome_cr10s": "creality_cr10s",
    "creawsome_cr10s4": "creality_cr10s4",
    "creawsome_cr10s5": "creality_cr10s5",
    "creawsome_cr10spro": "creality_cr10spro",
    "creawsome_cr20": "creality_cr20",
    "creawsome_cr20pro": "creality_cr20pro",
    "creawsome_ender2": "creality_ender2",
    "creawsome_ender3": "creality_ender3",
    "creawsome_ender4": "creality_ender4",
    "creawsome_ender5": "creality_ender5",

    # Extruder definitions.
    "creawsome_base_extruder_0": "creality_base_extruder_0",

    # Variants.
    "creawsome_base_0.2": "creality_base_0.2",
    "creawsome_base_0.3": "creality_base_0.3",
    "creawsome_base_0.4": "creality_base_0.4",
    "creawsome_base_0.5": "creality_base_0.5",
    "creawsome_base_0.6": "creality_base_0.6",
    "creawsome_base_0.8": "creality_base_0.8",
    "creawsome_base_1.0": "creality_base_1.0",
    "creawsome_cr10_0.2": "creality_cr10_0.2",
    "creawsome_cr10_0.3": "creality_cr10_0.3",
    "creawsome_cr10_0.4": "creality_cr10_0.4",
    "creawsome_cr10_0.5": "creality_cr10_0.5",
    "creawsome_cr10_0.6": "creality_cr10_0.6",
    "creawsome_cr10_0.8": "creality_cr10_0.8",
    "creawsome_cr10_1.0": "creality_cr10_1.0",
    "creawsome_cr10mini_0.2": "creality_cr10mini_0.2",
    "creawsome_cr10mini_0.3": "creality_cr10mini_0.3",
    "creawsome_cr10mini_0.4": "creality_cr10mini_0.4",
    "creawsome_cr10mini_0.5": "creality_cr10mini_0.5",
    "creawsome_cr10mini_0.6": "creality_cr10mini_0.6",
    "creawsome_cr10mini_0.8": "creality_cr10mini_0.8",
    "creawsome_cr10mini_1.0": "creality_cr10mini_1.0",
    "creawsome_cr10s4_0.2": "creality_cr10s4_0.2",
    "creawsome_cr10s4_0.3": "creality_cr10s4_0.3",
    "creawsome_cr10s4_0.4": "creality_cr10s4_0.4",
    "creawsome_cr10s4_0.5": "creality_cr10s4_0.5",
    "creawsome_cr10s4_0.6": "creality_cr10s4_0.6",
    "creawsome_cr10s4_0.8": "creality_cr10s4_0.8",
    "creawsome_cr10s4_1.0": "creality_cr10s4_1.0",
    "creawsome_cr10s5_0.2": "creality_cr10s5_0.2",
    "creawsome_cr10s5_0.3": "creality_cr10s5_0.3",
    "creawsome_cr10s5_0.4": "creality_cr10s5_0.4",
    "creawsome_cr10s5_0.5": "creality_cr10s5_0.5",
    "creawsome_cr10s5_0.6": "creality_cr10s5_0.6",
    "creawsome_cr10s5_0.8": "creality_cr10s5_0.8",
    "creawsome_cr10s5_1.0": "creality_cr10s5_1.0",
    "creawsome_cr10s_0.2": "creality_cr10s_0.2",
    "creawsome_cr10s_0.3": "creality_cr10s_0.3",
    "creawsome_cr10s_0.4": "creality_cr10s_0.4",
    "creawsome_cr10s_0.5": "creality_cr10s_0.5",
    "creawsome_cr10s_0.6": "creality_cr10s_0.6",
    "creawsome_cr10s_0.8": "creality_cr10s_0.8",
    "creawsome_cr10s_1.0": "creality_cr10s_1.0",
    "creawsome_cr10spro_0.2": "creality_cr10spro_0.2",
    "creawsome_cr10spro_0.3": "creality_cr10spro_0.3",
    "creawsome_cr10spro_0.4": "creality_cr10spro_0.4",
    "creawsome_cr10spro_0.5": "creality_cr10spro_0.5",
    "creawsome_cr10spro_0.6": "creality_cr10spro_0.6",
    "creawsome_cr10spro_0.8": "creality_cr10spro_0.8",
    "creawsome_cr10spro_1.0": "creality_cr10spro_1.0",
    "creawsome_cr20_0.2": "creality_cr20_0.2",
    "creawsome_cr20_0.3": "creality_cr20_0.3",
    "creawsome_cr20_0.4": "creality_cr20_0.4",
    "creawsome_cr20_0.5": "creality_cr20_0.5",
    "creawsome_cr20_0.6": "creality_cr20_0.6",
    "creawsome_cr20_0.8": "creality_cr20_0.8",
    "creawsome_cr20_1.0": "creality_cr20_1.0",
    "creawsome_cr20pro_0.2": "creality_cr20pro_0.2",
    "creawsome_cr20pro_0.3": "creality_cr20pro_0.3",
    "creawsome_cr20pro_0.4": "creality_cr20pro_0.4",
    "creawsome_cr20pro_0.5": "creality_cr20pro_0.5",
    "creawsome_cr20pro_0.6": "creality_cr20pro_0.6",
    "creawsome_cr20pro_0.8": "creality_cr20pro_0.8",
    "creawsome_cr20pro_1.0": "creality_cr20pro_1.0",
    "creawsome_ender2_0.2": "creality_ender2_0.2",
    "creawsome_ender2_0.3": "creality_ender2_0.3",
    "creawsome_ender2_0.4": "creality_ender2_0.4",
    "creawsome_ender2_0.5": "creality_ender2_0.5",
    "creawsome_ender2_0.6": "creality_ender2_0.6",
    "creawsome_ender2_0.8": "creality_ender2_0.8",
    "creawsome_ender2_1.0": "creality_ender2_1.0",
    "creawsome_ender3_0.2": "creality_ender3_0.2",
    "creawsome_ender3_0.3": "creality_ender3_0.3",
    "creawsome_ender3_0.4": "creality_ender3_0.4",
    "creawsome_ender3_0.5": "creality_ender3_0.5",
    "creawsome_ender3_0.6": "creality_ender3_0.6",
    "creawsome_ender3_0.8": "creality_ender3_0.8",
    "creawsome_ender3_1.0": "creality_ender3_1.0",
    "creawsome_ender4_0.2": "creality_ender4_0.2",
    "creawsome_ender4_0.3": "creality_ender4_0.3",
    "creawsome_ender4_0.4": "creality_ender4_0.4",
    "creawsome_ender4_0.5": "creality_ender4_0.5",
    "creawsome_ender4_0.6": "creality_ender4_0.6",
    "creawsome_ender4_0.8": "creality_ender4_0.8",
    "creawsome_ender4_1.0": "creality_ender4_1.0",
    "creawsome_ender5_0.2": "creality_ender5_0.2",
    "creawsome_ender5_0.3": "creality_ender5_0.3",
    "creawsome_ender5_0.4": "creality_ender5_0.4",
    "creawsome_ender5_0.5": "creality_ender5_0.5",
    "creawsome_ender5_0.6": "creality_ender5_0.6",
    "creawsome_ender5_0.8": "creality_ender5_0.8",
    "creawsome_ender5_1.0": "creality_ender5_1.0",

    # Upgrade for people who had the original Creality profiles from 4.1 and earlier.
    "creality_cr10_extruder_0": "creality_base_extruder_0",
    "creality_cr10s4_extruder_0": "creality_base_extruder_0",
    "creality_cr10s5_extruder_0": "creality_base_extruder_0",
    "creality_ender3_extruder_0": "creality_base_extruder_0"
}

# For legacy Creality printers, select the correct quality profile depending on the material.
_creality_quality_per_material = {
    # Since legacy Creality printers didn't have different variants, we always pick the 0.4mm variant.
    "generic_abs_175": {
        "high": "base_0.4_ABS_super",
        "normal": "base_0.4_ABS_super",
        "fast": "base_0.4_ABS_super",
        "draft": "base_0.4_ABS_standard",
        "extra_fast": "base_0.4_ABS_low",
        "coarse": "base_0.4_ABS_low",
        "extra_coarse": "base_0.4_ABS_low"
    },
    "generic_petg_175": {
        "high": "base_0.4_PETG_super",
        "normal": "base_0.4_PETG_super",
        "fast": "base_0.4_PETG_super",
        "draft": "base_0.4_PETG_standard",
        "extra_fast": "base_0.4_PETG_low",
        "coarse": "base_0.4_PETG_low",
        "extra_coarse": "base_0.4_PETG_low"
    },
    "generic_pla_175": {
        "high": "base_0.4_PLA_super",
        "normal": "base_0.4_PLA_super",
        "fast": "base_0.4_PLA_super",
        "draft": "base_0.4_PLA_standard",
        "extra_fast": "base_0.4_PLA_low",
        "coarse": "base_0.4_PLA_low",
        "extra_coarse": "base_0.4_PLA_low"
    },
    "generic_tpu_175": {
        "high": "base_0.4_TPU_super",
        "normal": "base_0.4_TPU_super",
        "fast": "base_0.4_TPU_super",
        "draft": "base_0.4_TPU_standard",
        "extra_fast": "base_0.4_TPU_standard",
        "coarse": "base_0.4_TPU_standard",
        "extra_coarse": "base_0.4_TPU_standard"
    },
    "empty_material": {  # For the global stack.
        "high": "base_global_super",
        "normal": "base_global_super",
        "fast": "base_global_super",
        "draft": "base_global_standard",
        "extra_fast": "base_global_low",
        "coarse": "base_global_low",
        "extra_coarse": "base_global_low"
    }
}

# Default variant to select for legacy Creality printers, now that we have variants.
_default_variants = {
    "creality_cr10_extruder_0": "creality_cr10_0.4",
    "creality_cr10s4_extruder_0": "creality_cr10s4_0.4",
    "creality_cr10s5_extruder_0": "creality_cr10s5_0.4",
    "creality_ender3_extruder_0": "creality_ender3_0.4"
}

# Whether the quality changes profile belongs to one of the upgraded printers can only be recognised by how they start.
# If they are, they must use the creality base definition so that they still belong to those printers.
_quality_changes_to_creality_base = {
    "creality_cr10_extruder_0",
    "creality_cr10s4_extruder_0",
    "creality_cr10s5_extruder_0",
    "creality_ender3_extruder_0"
    "creality_cr10",
    "creality_cr10s4",
    "creality_cr10s5",
    "creality_ender3",
}
_creality_limited_quality_type = {
    "high": "super",
    "normal": "super",
    "fast": "super",
    "draft": "draft",
    "extra_fast": "draft",
    "coarse": "draft",
    "extra_coarse": "draft"
}

##  Upgrades configurations from the state they were in at version 4.1 to the
#   state they should be in at version 4.2.
class VersionUpgrade41to42(VersionUpgrade):
    ##  Gets the version number from a CFG file in Uranium's 4.1 format.
    #
    #   Since the format may change, this is implemented for the 4.1 format only
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
        format_version = int(parser.get("general", "version"))  # Explicitly give an exception when this fails. That means that the file format is not recognised.
        setting_version = int(parser.get("metadata", "setting_version", fallback = "0"))
        return format_version * 1000000 + setting_version

    ##  Upgrades instance containers to have the new version
    #   number.
    #
    #   This renames the renamed settings in the containers.
    def upgradeInstanceContainer(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "8"

        # Certain instance containers (such as definition changes) reference to a certain definition container
        # Since a number of those changed name, we also need to update those.
        old_definition = parser["general"]["definition"]
        if old_definition in _renamed_profiles:
            parser["general"]["definition"] = _renamed_profiles[old_definition]

        # Rename settings.
        if "values" in parser:
            for old_name, new_name in _renamed_settings.items():
                if old_name in parser["values"]:
                    parser["values"][new_name] = parser["values"][old_name]
                    del parser["values"][old_name]
            # Remove settings.
            for key in _removed_settings:
                if key in parser["values"]:
                    del parser["values"][key]

        # For quality-changes profiles made for Creality printers, change the definition to the creality_base and make sure that the quality is something we have a profile for.
        if parser["metadata"].get("type", "") == "quality_changes":
            for possible_printer in _quality_changes_to_creality_base:
                if os.path.basename(filename).startswith(possible_printer + "_"):
                    parser["general"]["definition"] = "creality_base"
                    parser["metadata"]["quality_type"] = _creality_limited_quality_type.get(parser["metadata"]["quality_type"], "draft")
                    break

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    ##  Upgrades Preferences to have the new version number.
    #
    #   This renames the renamed settings in the list of visible settings.
    def upgradePreferences(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "8"

        # Renamed settings.
        if "visible_settings" in parser["general"]:
            visible_settings = parser["general"]["visible_settings"]
            visible_setting_set = set(visible_settings.split(";"))
            for old_name, new_name in _renamed_settings.items():
                if old_name in visible_setting_set:
                    visible_setting_set.remove(old_name)
                    visible_setting_set.add(new_name)
            for removed_key in _removed_settings:
                if removed_key in visible_setting_set:
                    visible_setting_set.remove(removed_key)
            parser["general"]["visible_settings"] = ";".join(visible_setting_set)

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    ##  Upgrades stacks to have the new version number.
    def upgradeStack(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "8"
        parser["general"]["version"] = "5"

        # We should only have 6 levels when we start.
        assert "7" not in parser["containers"]

        # We added the intent container in Cura 4.2. This means that all other containers move one step down.
        parser["containers"]["7"] = parser["containers"]["6"]
        parser["containers"]["6"] = parser["containers"]["5"]
        parser["containers"]["5"] = parser["containers"]["4"]
        parser["containers"]["4"] = parser["containers"]["3"]
        parser["containers"]["3"] = parser["containers"]["2"]
        parser["containers"]["2"] = "empty_intent"

        # Change renamed profiles.
        if "containers" in parser:
            # For legacy Creality printers, change the variant to 0.4.
            definition_id = parser["containers"]["6"]
            if parser["metadata"].get("type", "machine") == "extruder_train":
                if parser["containers"]["4"] == "empty_variant":  # Necessary for people entering from CreawsomeMod who already had a variant.
                    if definition_id in _default_variants:
                        parser["containers"]["4"] = _default_variants[definition_id]
                        if definition_id == "creality_cr10_extruder_0":  # We can't disambiguate between Creality CR-10 and Creality-CR10S since they share the same extruder definition. Have to go by the name.
                            if "cr-10s" in parser["metadata"].get("machine", "Creality CR-10").lower():  # Not perfect, since the user can change this name :(
                                parser["containers"]["4"] = "creality_cr10s_0.4"

            # Also change the quality to go along with it.
            material_id = parser["containers"]["3"]
            old_quality_id = parser["containers"]["2"]
            if material_id in _creality_quality_per_material and old_quality_id in _creality_quality_per_material[material_id]:
                parser["containers"]["2"] = _creality_quality_per_material[material_id][old_quality_id]

            stack_copy = {}  # type: Dict[str, str]  # Make a copy so that we don't modify the dict we're iterating over.
            stack_copy.update(parser["containers"])
            for position, profile_id in stack_copy.items():
                if profile_id in _renamed_profiles:
                    parser["containers"][position] = _renamed_profiles[profile_id]

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]