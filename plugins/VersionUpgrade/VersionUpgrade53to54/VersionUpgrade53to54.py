# Copyright (c) 2023 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

import configparser
from typing import Tuple, List
import io
from UM.VersionUpgrade import VersionUpgrade

_REMOVED_SETTINGS = {
    "wireframe_enabled",
    "wireframe_height",
    "wireframe_roof_inset",
    "wireframe_printspeed",
    "wireframe_printspeed_bottom",
    "wireframe_printspeed_up",
    "wireframe_printspeed_down",
    "wireframe_printspeed_flat",
    "wireframe_flow",
    "wireframe_flow_connection",
    "wireframe_flow_flat",
    "wireframe_top_delay",
    "wireframe_bottom_delay",
    "wireframe_flat_delay",
    "wireframe_up_half_speed",
    "wireframe_top_jump",
    "wireframe_fall_down",
    "wireframe_drag_along",
    "wireframe_strategy",
    "wireframe_straight_before_down",
    "wireframe_roof_fall_down",
    "wireframe_roof_drag_along",
    "wireframe_roof_outer_delay",
    "wireframe_nozzle_clearance",
    "support_tree_branch_distance",
    "support_tree_collision_resolution",
}

_RENAMED_PROFILES = {
    "abs_040012": "elegoo_abs_nozzle_0.40_layer_0.10",
    "abs_040016": "elegoo_abs_nozzle_0.40_layer_0.15",
    "abs_040020": "elegoo_abs_nozzle_0.40_layer_0.20",
    "abs_040024": "elegoo_abs_nozzle_0.40_layer_0.20",
    "abs_040028": "elegoo_abs_nozzle_0.40_layer_0.30",

    "asa_040012": "elegoo_asa_nozzle_0.40_layer_0.10",
    "asa_040016": "elegoo_asa_nozzle_0.40_layer_0.15",
    "asa_040020": "elegoo_asa_nozzle_0.40_layer_0.20",
    "asa_040024": "elegoo_asa_nozzle_0.40_layer_0.20",
    "asa_040028": "elegoo_asa_nozzle_0.40_layer_0.30",

    "petg_040012": "elegoo_petg_nozzle_0.40_layer_0.10",
    "petg_040016": "elegoo_petg_nozzle_0.40_layer_0.15",
    "petg_040020": "elegoo_petg_nozzle_0.40_layer_0.20",
    "petg_040024": "elegoo_petg_nozzle_0.40_layer_0.20",
    "petg_040028": "elegoo_petg_nozzle_0.40_layer_0.30",

    "pla_040012": "elegoo_pla_nozzle_0.40_layer_0.10",
    "pla_040016": "elegoo_pla_nozzle_0.40_layer_0.15",
    "pla_040020": "elegoo_pla_nozzle_0.40_layer_0.20",
    "pla_040024": "elegoo_pla_nozzle_0.40_layer_0.20",
    "pla_040028": "elegoo_pla_nozzle_0.40_layer_0.30",

    "tpu_040012": "elegoo_tpu_nozzle_0.40_layer_0.10",
    "tpu_040016": "elegoo_tpu_nozzle_0.40_layer_0.15",
    "tpu_040020": "elegoo_tpu_nozzle_0.40_layer_0.20",
    "tpu_040024": "elegoo_tpu_nozzle_0.40_layer_0.20",
    "tpu_040028": "elegoo_tpu_nozzle_0.40_layer_0.30",

    "elegoo_global_012_high": "elegoo_layer_0.10",
    "elegoo_global_016_normal": "elegoo_layer_0.15",
    "elegoo_global_020_fine": "elegoo_layer_0.20",
    "elegoo_global_024_medium": "elegoo_layer_0.20",
    "elegoo_global_028_draft": "elegoo_layer_0.30",
}


class VersionUpgrade53to54(VersionUpgrade):
    def upgradePreferences(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades preferences to remove from the visibility list the settings that were removed in this version.
        It also changes the preferences to have the new version number.

        This removes any settings that were removed in the new Cura version.
        :param serialized: The original contents of the preferences file.
        :param filename: The file name of the preferences file.
        :return: A list of new file names, and a list of the new contents for
        those files.
        """
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "22"

        # Remove deleted settings from the visible settings list.
        if "general" in parser and "visible_settings" in parser["general"]:
            visible_settings = set(parser["general"]["visible_settings"].split(";"))
            for removed in _REMOVED_SETTINGS:
                if removed in visible_settings:
                    visible_settings.remove(removed)

            parser["general"]["visible_settings"] = ";".join(visible_settings)

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeInstanceContainer(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades instance containers to remove the settings that were removed in this version.
        It also changes the instance containers to have the new version number.

        This removes any settings that were removed in the new Cura version and updates settings that need to be updated
        with a new value.

        :param serialized: The original contents of the instance container.
        :param filename: The original file name of the instance container.
        :return: A list of new file names, and a list of the new contents for
        those files.
        """
        parser = configparser.ConfigParser(interpolation = None, comment_prefixes = ())
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "22"

        if "values" in parser:
            # Remove deleted settings from the instance containers.
            for removed in _REMOVED_SETTINGS:
                if removed in parser["values"]:
                    del parser["values"][removed]

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

        parser["metadata"]["setting_version"] = "22"

        for container in parser['containers']:
            parser['containers'][container] = _RENAMED_PROFILES.get(parser['containers'][container], parser['containers'][container])

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]
