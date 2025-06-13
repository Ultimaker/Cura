# Copyright (c) 2024 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

import configparser
from typing import Dict, List, Tuple
import io
from UM.VersionUpgrade import VersionUpgrade

# Just to be sure, since in my testing there were both 0.1.0 and 0.2.0 settings about.
_PLUGIN_NAME = "_plugin__curaenginegradualflow"
_FROM_PLUGINS_SETTINGS = {
    "gradual_flow_enabled",
    "max_flow_acceleration",
    "layer_0_max_flow_acceleration",
    "gradual_flow_discretisation_step_size",
    "reset_flow_duration",
}  # type: Set[str]

_NEW_SETTING_VERSION = "24"


class VersionUpgrade58to59(VersionUpgrade):
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
        parser["metadata"]["setting_version"] = _NEW_SETTING_VERSION

        # Fix renamed settings for visibility
        if "visible_settings" in parser["general"]:
            all_setting_keys = parser["general"]["visible_settings"].strip().split(";")
            if all_setting_keys:
                for idx, key in enumerate(all_setting_keys):
                    if key.startswith(_PLUGIN_NAME):
                        all_setting_keys[idx] = key.split("__")[-1]
                parser["general"]["visible_settings"] = ";".join(all_setting_keys)

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
        parser["metadata"]["setting_version"] = _NEW_SETTING_VERSION

        # Rename settings.
        if "values" in parser:
            for key, value in parser["values"].items():
                if key.startswith(_PLUGIN_NAME):
                    parser["values"][key.split("__")[-1]] = parser["values"][key]
                    del parser["values"][key]

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

        parser["metadata"]["setting_version"] = _NEW_SETTING_VERSION

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]
