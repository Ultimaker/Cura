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

    def upgradeDefinitionChanges(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades definition changes files to the new version number.

        This applies all of the changes that are applied in other instance
        containers as well.

        In the case of Deltacomb printers, it splits the 2 extruder definition
        changes into 4.
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
                third_extruder_changes = copy.copy(parser)
                fourth_extruder_changes = copy.copy(parser)

                parser["general"]["definition"] = "deltacomb_base_extruder_1"
                third_extruder_changes["general"]["definition"] = "deltacomb_base_extruder_2"
                fourth_extruder_changes["general"]["definition"] = "deltacomb_base_extruder_3"
                results.append((third_extruder_changes, filename[:-len(".inst.cfg")] + "_e2_upgrade.inst.cfg"))  # Hopefully not already taken.
                results.append((fourth_extruder_changes, filename[:-len(".inst.cfg")] + "_e3_upgrade.inst.cfg"))  # Hopefully not already taken.
            elif parser["general"]["definition"] == "deltacomb":  # Global stack.
                parser["general"]["definition"] = "deltacomb_dc20"

        # Now go upgrade with the generic instance container method.
        final_serialised = []
        final_filenames = []
        for result_parser, result_filename in results:
            result_ss = io.StringIO()
            result_parser.write(result_ss)
            result_serialised = result_ss.getvalue()
            # The upgrade function itself might also return multiple files, so we need to append all of those into the final list.
            this_filenames_upgraded, this_serialised_upgraded = self.upgradeInstanceContainer(result_serialised, result_filename)
            final_serialised += this_serialised_upgraded
            final_filenames += this_filenames_upgraded

        return final_filenames, final_serialised

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
        result_parsers = [parser]
        result_filenames = [filename]

        # Update version number.
        if "metadata" not in parser:
            parser["metadata"] = {}
        parser["metadata"]["setting_version"] = "13"

        if "containers" in parser and "7" in parser["containers"]:
            if parser["containers"]["7"] == "deltacomb_extruder_0" or parser["containers"]["7"] == "deltacomb_extruder_1":
                if "5" in parser["containers"]:
                    parser["containers"]["5"] = renamed_nozzles.get(parser["containers"]["5"], default = parser["containers"]["5"])
                    if "3" in parser["containers"] and "4" in parser["containers"] and parser["containers"]["3"] == "empty_quality":
                        parser["containers"]["3"] = default_qualities_per_nozzle_and_material[parser["containers"]["5"]].get(parser["containers"]["4"], "empty_quality")
                if parser["containers"]["7"] == "deltacomb_extruder_1":
                    parser["containers"]["7"] = "deltacomb_base_extruder_1"
                else:
                    parser["containers"]["7"] = "deltacomb_base_extruder_0"
                    # Copy this extruder to extruder 3 and 4.
                    extruder3 = copy.copy(parser)
                    extruder3["metadata"]["position"] = "2"
                    extruder3["containers"]["0"] += "_e2_upgrade"
                    extruder3["containers"]["6"] += "_e2_upgrade"
                    extruder3["containers"]["7"] = "deltacomb_base_extuder_2"
                    result_parsers.append(extruder3)
                    result_filenames.append(filename[:-len(".extruder.cfg")] + "_e2_upgrade.extruder.cfg")
                    extruder4 = copy.copy(parser)
                    extruder4["metadata"]["position"] = "3"
                    extruder4["containers"]["0"] += ".inst.cfg_e3_upgrade"
                    extruder4["containers"]["6"] += ".inst.cfg_e3_upgrade"
                    extruder4["containers"]["7"] = "deltacomb_base_extruder_3"
                    result_parsers.append(extruder4)
                    result_filenames.append(filename[:-len(".extruder.cfg")] + "_e3_upgrade.extruder.cfg")

        result_serialized = []
        for result_parser in result_parsers:
            result_ss = io.StringIO()
            result_parser.write(result_ss)
            result_serialized.append(result_ss.getvalue())

        return result_filenames, result_serialized
