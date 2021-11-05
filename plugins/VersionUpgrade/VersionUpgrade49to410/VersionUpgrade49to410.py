# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser
import io
import os.path  # To get the file ID.
from typing import Dict, List, Tuple

from UM.VersionUpgrade import VersionUpgrade


class VersionUpgrade49to410(VersionUpgrade):
    """
    Upgrades configurations from the state they were in at version 4.9 to the state they should be in at version 4.10.
    """

    _renamed_profiles = {
        # Definitions.
        "twotrees_bluer"           : "two_trees_bluer",

        # Upgrade for people who had the original TwoTrees Bluer profiles from 4.9 and earlier.
        "twotrees_bluer_extruder_0": "two_trees_base_extruder_0",
        "twotrees_bluer_extruder_1": "two_trees_base_extruder_0"
    }

    _quality_changes_to_two_trees_base = {
        "twotrees_bluer_extruder_0",
        "twotrees_bluer_extruder_1",
        "twotrees_bluer"
    }

    # Default variant to select for legacy TwoTrees printers, now that we have variants.
    _default_variants = {
        "twotrees_bluer_extruder_0"  : "two_trees_bluer_0.4",
        "twotrees_bluer_extruder_1"  : "two_trees_bluer_0.4"
    }

    _two_trees_bluer_quality_type_conversion = {
        "high"        : "ultra",
        "normal"      : "super",
        "fast"        : "standard",
        "draft"       : "standard",
        "extra_fast"  : "low",
        "coarse"      : "draft",
        "extra_coarse": "draft"
    }

    _two_trees_quality_per_material = {
        # Since legacy TwoTrees printers didn't have different variants, we always pick the 0.4mm variant.
        "generic_abs_175" : {
            "high"        : "two_trees_0.4_ABS_super",
            "normal"      : "two_trees_0.4_ABS_super",
            "fast"        : "two_trees_0.4_ABS_super",
            "draft"       : "two_trees_0.4_ABS_standard",
            "extra_fast"  : "two_trees_0.4_ABS_low",
            "coarse"      : "two_trees_0.4_ABS_low",
            "extra_coarse": "two_trees_0.4_ABS_low"
        },
        "generic_petg_175": {
            "high"        : "two_trees_0.4_PETG_super",
            "normal"      : "two_trees_0.4_PETG_super",
            "fast"        : "two_trees_0.4_PETG_super",
            "draft"       : "two_trees_0.4_PETG_standard",
            "extra_fast"  : "two_trees_0.4_PETG_low",
            "coarse"      : "two_trees_0.4_PETG_low",
            "extra_coarse": "two_trees_0.4_PETG_low"
        },
        "generic_pla_175" : {
            "high"        : "two_trees_0.4_PLA_super",
            "normal"      : "two_trees_0.4_PLA_super",
            "fast"        : "two_trees_0.4_PLA_super",
            "draft"       : "two_trees_0.4_PLA_standard",
            "extra_fast"  : "two_trees_0.4_PLA_low",
            "coarse"      : "two_trees_0.4_PLA_low",
            "extra_coarse": "two_trees_0.4_PLA_low"
        },
        "generic_tpu_175" : {
            "high"        : "two_trees_0.4_TPU_super",
            "normal"      : "two_trees_0.4_TPU_super",
            "fast"        : "two_trees_0.4_TPU_super",
            "draft"       : "two_trees_0.4_TPU_standard",
            "extra_fast"  : "two_trees_0.4_TPU_standard",
            "coarse"      : "two_trees_0.4_TPU_standard",
            "extra_coarse": "two_trees_0.4_TPU_standard"
        },
        "empty_material"  : {  # For the global stack.
            "high"        : "two_trees_global_super",
            "normal"      : "two_trees_global_super",
            "fast"        : "two_trees_global_super",
            "draft"       : "two_trees_global_standard",
            "extra_fast"  : "two_trees_global_low",
            "coarse"      : "two_trees_global_low",
            "extra_coarse": "two_trees_global_low"
        }
    }

    _deltacomb_quality_type_conversion = {
        "a" : "D005",
        "b" : "D010",
        "c" : "D015",
        "d" : "D020",
        "e" : "D030",
        "f" : "D045",
        "g" : "D060"
    }

    def upgradePreferences(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades preferences to have the new version number.
        :param serialized: The original contents of the preferences file.
        :param filename: The file name of the preferences file.
        :return: A list of new file names, and a list of the new contents for
        those files.
        """
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "17"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]


    def upgradeInstanceContainer(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """Upgrades instance containers to have the new version number.

        This renames the renamed settings in the containers.
        """
        parser = configparser.ConfigParser(interpolation = None, comment_prefixes = ())
        parser.read_string(serialized)

        # Update setting version number.
        if "metadata" not in parser:
            parser["metadata"] = {}
        parser["metadata"]["setting_version"] = "17"

        if "general" not in parser:
            parser["general"] = {}
        # Certain instance containers (such as definition changes) reference to a certain definition container
        # Since a number of those changed name, we also need to update those.
        old_definition = parser.get("general", "definition", fallback = "")
        if old_definition in self._renamed_profiles:
            parser["general"]["definition"] = self._renamed_profiles[old_definition]

        # For quality-changes profiles made for TwoTrees Bluer printers, change the definition to the two_trees_base and make sure that the quality is something we have a profile for.
        if parser.get("metadata", "type", fallback = "") == "quality_changes":
            for possible_printer in self._quality_changes_to_two_trees_base:
                if os.path.basename(filename).startswith(possible_printer + "_"):
                    parser["general"]["definition"] = "two_trees_base"
                    parser["metadata"]["quality_type"] = self._two_trees_bluer_quality_type_conversion.get(parser.get("metadata", "quality_type", fallback = "fast"), "standard")
                    break

                if os.path.basename(filename).startswith("deltacomb_"):
                    parser["general"]["definition"] = "deltacomb_base"
                    parser["metadata"]["quality_type"] = self._deltacomb_quality_type_conversion.get(parser.get("metadata", "quality_type", fallback = "c"), "D015")
                    break

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeStack(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """Upgrades stacks to have the new version number."""

        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update setting version number.
        if "metadata" not in parser:
            parser["metadata"] = {}
        parser["metadata"]["setting_version"] = "17"

        # Change renamed profiles.
        if "containers" in parser:
            definition_id = parser["containers"]["7"]
            if definition_id in self._quality_changes_to_two_trees_base:
                material_id = parser["containers"]["4"]
                old_quality_id = parser["containers"]["3"]
                if parser["metadata"].get("type", "machine") == "extruder_train":
                    if parser["containers"]["5"] == "empty_variant":
                        if definition_id in self._default_variants:
                            parser["containers"]["5"] = self._default_variants[definition_id]  # For legacy TwoTrees printers, change the variant to 0.4.

                # Also change the quality to go along with it.
                if material_id in self._two_trees_quality_per_material and old_quality_id in self._two_trees_quality_per_material[material_id]:
                    parser["containers"]["3"] = self._two_trees_quality_per_material[material_id][old_quality_id]
                stack_copy = {}  # type: Dict[str, str]  # Make a copy so that we don't modify the dict we're iterating over.
                stack_copy.update(parser["containers"])
                for position, profile_id in stack_copy.items():
                    if profile_id in self._renamed_profiles:
                        parser["containers"][position] = self._renamed_profiles[profile_id]

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]
