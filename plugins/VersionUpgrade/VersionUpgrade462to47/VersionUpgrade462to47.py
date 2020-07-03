# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser
from typing import Tuple, List, Dict
import io

from UM.Util import parseBool
from UM.VersionUpgrade import VersionUpgrade


# Renamed definition files
_RENAMED_DEFINITION_DICT = {
    "dagoma_discoeasy200": "dagoma_discoeasy200_bicolor",
} # type: Dict[str, str]


class VersionUpgrade462to47(VersionUpgrade):
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
        parser["metadata"]["setting_version"] = "15"

        if "cura" in parser and "jobname_prefix" in parser["cura"]:
            if not parseBool(parser["cura"]["jobname_prefix"]):
                parser["cura"]["job_name_template"] = "{project_name}"
            del parser["cura"]["jobname_prefix"]
        # else: When the jobname_prefix preference is True or not set,
        # the default value for job_name_template ("{machine_name_short}_{project_name}") will be used

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

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
        parser["metadata"]["setting_version"] = "15"

        if "values" in parser:
            # Maximum Deviation's effect was corrected. Previously the deviation
            # ended up being only half of what the user had entered. This was
            # fixed in Cura 4.7 so there we need to halve the deviation that the
            # user had entered.
            #
            # This got accidentally merged in Cura 4.6.0. In 4.6.2 we removed
            # that. In 4.7 it's not unmerged, so there we need to revert all
            # that again.
            if "meshfix_maximum_deviation" in parser["values"]:
                maximum_deviation = parser["values"]["meshfix_maximum_deviation"]
                if maximum_deviation.startswith("="):
                    maximum_deviation = maximum_deviation[1:]
                maximum_deviation = "=(" + maximum_deviation + ") / 2"
                parser["values"]["meshfix_maximum_deviation"] = maximum_deviation

            # Ironing inset is now based on the flow-compensated line width to make the setting have a more logical UX.
            # Adjust so that the actual print result remains the same.
            if "ironing_inset" in parser["values"]:
                ironing_inset = parser["values"]["ironing_inset"]
                if ironing_inset.startswith("="):
                    ironing_inset = ironing_inset[1:]
                if "ironing_pattern" in parser["values"] and parser["values"]["ironing_pattern"] == "concentric":
                    correction = " + ironing_line_spacing - skin_line_width * (1.0 + ironing_flow / 100) / 2"
                else:  # If ironing_pattern doesn't exist, it means the default (zigzag) is selected
                    correction = " + skin_line_width * (1.0 - ironing_flow / 100) / 2"
                ironing_inset = "=(" + ironing_inset + ")" + correction
                parser["values"]["ironing_inset"] = ironing_inset

        # Check renamed definitions
        if "definition" in parser["general"] and parser["general"]["definition"] in _RENAMED_DEFINITION_DICT:
            parser["general"]["definition"] = _RENAMED_DEFINITION_DICT[parser["general"]["definition"]]

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeStack(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades stacks to have the new version number.
        :param serialized: The original contents of the stack.
        :param filename: The original file name of the stack.
        :return: A list of new file names, and a list of the new contents for
        those files.
        """
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        if "metadata" not in parser:
            parser["metadata"] = {}
        parser["metadata"]["setting_version"] = "15"

        # Update Pause at Height script parameters if present.
        if "post_processing_scripts" in parser["metadata"]:
            new_scripts_entries = []
            for script_str in parser["metadata"]["post_processing_scripts"].split("\n"):
                if not script_str:
                    continue
                script_str = script_str.replace(r"\\\n", "\n").replace(r"\\\\", "\\\\")  # Unescape escape sequences.
                script_parser = configparser.ConfigParser(interpolation=None)
                script_parser.optionxform = str  # type: ignore  # Don't transform the setting keys as they are case-sensitive.
                script_parser.read_string(script_str)

                # Unify all Pause at Height
                script_id = script_parser.sections()[0]
                if script_id in ["BQ_PauseAtHeight", "PauseAtHeightRepRapFirmwareDuet", "PauseAtHeightforRepetier"]:
                    script_settings = script_parser.items(script_id)
                    script_settings.append(("pause_method", {
                        "BQ_PauseAtHeight": "bq",
                        "PauseAtHeightforRepetier": "repetier",
                        "PauseAtHeightRepRapFirmwareDuet": "reprap"
                    }[script_id]))

                    # Since we cannot rename a section, we remove the original section and create a new section with the new script id.
                    script_parser.remove_section(script_id)
                    script_id = "PauseAtHeight"
                    script_parser.add_section(script_id)
                    for setting_tuple in script_settings:
                        script_parser.set(script_id, setting_tuple[0], setting_tuple[1])

                # Update redo_layers to redo_layer
                if "PauseAtHeight" in script_parser:
                    if "redo_layers" in script_parser["PauseAtHeight"]:
                        script_parser["PauseAtHeight"]["redo_layer"] = str(int(script_parser["PauseAtHeight"]["redo_layers"]) > 0)
                        del script_parser["PauseAtHeight"]["redo_layers"]  # Has been renamed to without the S.
                script_io = io.StringIO()
                script_parser.write(script_io)
                script_str = script_io.getvalue()
                script_str = script_str.replace("\\\\", r"\\\\").replace("\n", r"\\\n")  # Escape newlines because configparser sees those as section delimiters.
                new_scripts_entries.append(script_str)
            parser["metadata"]["post_processing_scripts"] = "\n".join(new_scripts_entries)
        # check renamed definition
        if parser.has_option("containers", "7") and parser["containers"]["7"] in _RENAMED_DEFINITION_DICT:
            parser["containers"]["7"] = _RENAMED_DEFINITION_DICT[parser["containers"]["7"]]
        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]
