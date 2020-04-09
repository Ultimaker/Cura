# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser
import copy  # To split up files.
from typing import Tuple, List
import io
from UM.VersionUpgrade import VersionUpgrade

renamed_nozzles = {
    "deltacomb_025_e3d": "deltacomb_dc20_fbe025",
    "deltacomb_040_e3d": "deltacomb_dc20_fbe040",
    "deltacomb_080_e3d": "deltacomb_dc20_vfbe080"
}
default_qualities_per_nozzle_and_material = {  # Can't define defaults for user-defined materials, since we only have the material ID. Those will get reset to empty quality :(
    "deltacomb_dc20_fbe025": {
        "generic_pla_175": "deltacomb_FBE0.25_PLA_C",
        "generic_abs_175": "deltacomb_FBE0.25_ABS_C"
    },
    "deltacomb_dc20_fbe040": {
        "generic_pla_175": "deltacomb_FBE0.40_PLA_C",
        "generic_abs_175": "deltacomb_FBE0.40_ABS_C",
        "generic_petg_175": "deltacomb_FBE0.40_PETG_C",
        "generic_tpu_175": "deltacomb_FBE0.40_TPU_C"
    },
    "deltacomb_dc20_vfbe080": {
        "generic_pla_175": "deltacomb_VFBE0.80_PLA_D",
        "generic_abs_175": "deltacomb_VFBE0.80_ABS_D"
    }
}

class VersionUpgrade46to47(VersionUpgrade):
    def getCfgVersion(self, serialised: str) -> int:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialised)
        format_version = int(parser.get("general", "version"))  # Explicitly give an exception when this fails. That means that the file format is not recognised.
        setting_version = int(parser.get("metadata", "setting_version", fallback = "0"))
        return format_version * 1000000 + setting_version

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
        parser["metadata"]["setting_version"] = "13"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeExtruderInstanceContainer(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades per-extruder instance containers to the new version number.

        This applies all of the changes that are applied in other instance
        containers as well.

        In the case of Deltacomb printers, it splits the 2 extruders into 4 and
        changes the definition.
        :param serialized: The original contents of the instance container.
        :param filename: The original file name of the instance container.
        :return: A list of new file names, and a list of the new contents for
        those files.
        """
        parser = configparser.ConfigParser(interpolation = None, comment_prefixes = ())
        parser.read_string(serialized)
        results = [(parser, filename)]

        if "general" in parser and "definition" in parser["general"]:
            if parser["general"]["definition"] == "deltacomb_extruder_0":
                parser["general"]["definition"] = "deltacomb_base_extruder_0"
            elif parser["general"]["definition"] == "deltacomb_extruder_1":  # Split up the second Deltacomb extruder into 3, creating an extra two extruders.
                parser_e2 = copy.deepcopy(parser)
                parser_e3 = copy.deepcopy(parser)

                parser["general"]["definition"] = "deltacomb_base_extruder_1"
                parser_e2["general"]["definition"] = "deltacomb_base_extruder_2"
                parser_e3["general"]["definition"] = "deltacomb_base_extruder_3"
                results.append((parser_e2, filename + "_e2_upgrade"))  # Hopefully not already taken.
                results.append((parser_e3, filename + "_e3_upgrade"))
            elif parser["general"]["definition"] == "deltacomb":  # On the global stack OR the per-extruder user container.
                parser["general"]["definition"] = "deltacomb_dc20"

                if "metadata" in parser and "extruder" in parser["metadata"]:  # Per-extruder user container.
                    parser_e2 = copy.deepcopy(parser)
                    parser_e3 = copy.deepcopy(parser)
                    parser_e2["metadata"]["extruder"] += "_e2_upgrade"
                    parser_e3["metadata"]["extruder"] += "_e3_upgrade"
                    results.append((parser_e2, filename + "_e2_upgrade"))
                    results.append((parser_e3, filename + "_e3_upgrade"))

        # Now go upgrade with the generic instance container method.
        final_serialized = []  # type: List[str]
        final_filenames = []  # type: List[str]
        for result_parser, result_filename in results:
            result_ss = io.StringIO()
            result_parser.write(result_ss)
            result_serialized = result_ss.getvalue()
            # The upgrade function itself might also return multiple files, so we need to append all of those into the final list.
            this_filenames_upgraded, this_serialized_upgraded = self.upgradeInstanceContainer(result_serialized, result_filename)
            final_serialized += this_serialized_upgraded
            final_filenames += this_filenames_upgraded

        return final_filenames, final_serialized

    def upgradeInstanceContainer(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades instance containers to have the new version number.

        This changes the maximum deviation setting if that setting was present
        in the profile.
        :param serialized: The original contents of the instance container.
        :param filename: The original file name of the instance container.
        :return: A list of new file names, and a list of the new contents for
        those files.
        """
        parser = configparser.ConfigParser(interpolation = None, comment_prefixes = ())
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "13"

        if "values" in parser:
            # Maximum Deviation's effect was corrected. Previously the deviation
            # ended up being only half of what the user had entered. This was
            # fixed in Cura 4.7 so there we need to halve the deviation that the
            # user had entered.
            if "meshfix_maximum_deviation" in parser["values"]:
                maximum_deviation = parser["values"]["meshfix_maximum_deviation"]
                if maximum_deviation.startswith("="):
                    maximum_deviation = maximum_deviation[1:]
                maximum_deviation = "=(" + maximum_deviation + ") / 2"
                parser["values"]["meshfix_maximum_deviation"] = maximum_deviation

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeStack(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades stacks to have the new version number.

        This upgrades Deltacomb printers to their new profile structure, and
        gives them 4 extruders.
        :param serialized: The original contents of the stack.
        :param filename: The original file name of the stack.
        :return: A list of new file names, and a list of the new contents for
        those files.
        """
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)
        results = [(parser, filename)]

        # Update version number.
        if "metadata" not in parser:
            parser["metadata"] = {}
        parser["metadata"]["setting_version"] = "13"

        if "containers" in parser and "7" in parser["containers"]:
            if parser["containers"]["7"] == "deltacomb_extruder_0" or parser["containers"]["7"] == "deltacomb_extruder_1":  # Extruder stack.
                if "5" in parser["containers"]:
                    parser["containers"]["5"] = renamed_nozzles.get(parser["containers"]["5"], parser["containers"]["5"])
                    if "3" in parser["containers"] and "4" in parser["containers"] and parser["containers"]["3"] == "empty_quality":
                        parser["containers"]["3"] = default_qualities_per_nozzle_and_material[parser["containers"]["5"]].get(parser["containers"]["4"], "empty_quality")
                if parser["containers"]["7"] == "deltacomb_extruder_0":
                    parser["containers"]["7"] = "deltacomb_base_extruder_0"
                else:
                    parser["containers"]["7"] = "deltacomb_base_extruder_1"
                    # Copy this extruder to extruder 3 and 4.
                    extruder3 = copy.deepcopy(parser)
                    extruder4 = copy.deepcopy(parser)

                    extruder3["general"]["id"] += "_e2_upgrade"
                    extruder3["metadata"]["position"] = "2"
                    extruder3["containers"]["0"] += "_e2_upgrade"
                    if extruder3["containers"]["1"] != "empty_quality_changes":
                        extruder3["containers"]["1"] += "_e2_upgrade"
                    extruder3["containers"]["6"] += "_e2_upgrade"
                    extruder3["containers"]["7"] = "deltacomb_base_extruder_2"
                    results.append((extruder3, filename + "_e2_upgrade"))

                    extruder4["general"]["id"] += "_e3_upgrade"
                    extruder4["metadata"]["position"] = "3"
                    extruder4["containers"]["0"] += "_e3_upgrade"
                    if extruder4["containers"]["1"] != "empty_quality_changes":
                        extruder4["containers"]["1"] += "_e3_upgrade"
                    extruder4["containers"]["6"] += "_e3_upgrade"
                    extruder4["containers"]["7"] = "deltacomb_base_extruder_3"
                    results.append((extruder4, filename + "_e3_upgrade"))
            elif parser["containers"]["7"] == "deltacomb":  # Global stack.
                parser["containers"]["7"] = "deltacomb_dc20"
                parser["containers"]["3"] = "deltacomb_global_C"

        result_serialized = []
        result_filenames = []
        for result_parser, result_filename in results:
            result_ss = io.StringIO()
            result_parser.write(result_ss)
            result_serialized.append(result_ss.getvalue())
            result_filenames.append(result_filename)

        return result_filenames, result_serialized
