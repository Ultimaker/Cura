#!/usr/bin/env python3
#
# This script check correctness of settings visibility list
#
from typing import Dict
import os
import sys
import json
import configparser
import glob

# Directory where this python file resides
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))


# The order of settings type. If the setting is in basic list then it also should be in expert
setting_visibility = ["basic", "advanced", "expert"]


class SettingVisibilityInspection:


    def __init__(self) -> None:
        self.all_settings_keys = []
        self.all_settings_categories = []


    def defineAllCuraSettings(self, fdmprinter_json_path: str) -> None:

        with open(fdmprinter_json_path) as f:
            json_data = json.load(f)
            self._flattenAllSettings(json_data)


    def _flattenAllSettings(self, json_file: Dict[str, str]) -> None:
        for key, data in json_file["settings"].items():  # top level settings are categories
            self._flattenSettings(data["children"])  # actual settings are children of top level category-settings

    def _flattenSettings(self, settings: Dict[str, str]) -> None:
        for key, setting in settings.items():

            if "type" in setting and setting["type"] != "category":
                self.all_settings_keys.append(key)
            else:
                self.all_settings_categories.append(key)

            if "children" in setting:
                self._flattenSettings(setting["children"])


    def getSettingsFromSettingVisibilityFile(self, file_path: str):
        parser = configparser.ConfigParser(allow_no_value = True)
        parser.read([file_path])

        if not parser.has_option("general", "name") or not parser.has_option("general", "weight"):
            raise NotImplementedError("Visibility setting file missing general data")

        settings = {}
        for section in parser.sections():
            if section == 'general':
                continue

            if section not in settings:
                settings[section] = []

            for option in parser[section].keys():
                settings[section].append(option)

        return settings

    def validateSettingsVisibility(self, setting_visibility_items: Dict):

        for visibility_type in setting_visibility:
            item = setting_visibility_items[visibility_type]

            for category, settings in item.items():
                ss = 3




if __name__ == "__main__":

    all_setting_visibility_files = glob.glob(os.path.join(os.path.join(SCRIPT_DIR, "..", "resources", "setting_visibility"), '*.cfg'))
    fdmprinter_def_path = os.path.join(SCRIPT_DIR, "..", "resources", "definitions", "fdmprinter.def.json")

    inspector = SettingVisibilityInspection()
    inspector.defineAllCuraSettings(fdmprinter_def_path)

    setting_visibility_items = {}
    for file_path in all_setting_visibility_files:
        temp = inspector.getSettingsFromSettingVisibilityFile(all_setting_visibility_files[0])

        base_name = os.path.basename(file_path)
        visibility_type = base_name.split('.')[0]

        setting_visibility_items[visibility_type] = temp


    inspector.validateSettingsVisibility(setting_visibility_items)

    found_error = False
    # Validate settings
    # for item in setting_visibility:








    sys.exit(0 if not found_error else 1)
