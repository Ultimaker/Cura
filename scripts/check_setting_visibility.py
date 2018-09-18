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
        self.all_settings_keys = {}

    def defineAllCuraSettings(self, fdmprinter_json_path: str) -> None:

        with open(fdmprinter_json_path) as f:
            json_data = json.load(f)
            self._flattenAllSettings(json_data)


    def _flattenAllSettings(self, json_file: Dict[str, str]) -> None:
        for key, data in json_file["settings"].items():  # top level settings are categories

            if "type" in data and data["type"] == "category":

                self.all_settings_keys[key] = []
                self._flattenSettings(data["children"], key)  # actual settings are children of top level category-settings

    def _flattenSettings(self, settings: Dict[str, str], category) -> None:
        for key, setting in settings.items():

            if "type" in setting and setting["type"] != "category":
                self.all_settings_keys[category].append(key)

            if "children" in setting:
                self._flattenSettings(setting["children"], category)


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

        not_valid_categories = {}
        not_valid_setting_by_category = {}
        not_valid_setting_by_order = {}

        visible_settings_order = [] # This list is used to make sure that the settings are in the correct order.
        # basic.cfg -> advanced.cfg -> expert.cfg. Like: if the setting 'layer_height' in 'basic.cfg' then the same setting
        # also should be in 'advanced.cfg'

        all_settings_categories = list(self.all_settings_keys.keys())

        # visibility_type = basic, advanced, expert
        for visibility_type in setting_visibility:
            item = setting_visibility_items[visibility_type]

            not_valid_setting_by_category[visibility_type] = [] # this list is for keeping invalid settings.
            not_valid_categories[visibility_type] = []

            for category, category_settings in item.items():

                # Validate Category, If category is not defined then the test will fail
                if category not in all_settings_categories:
                    not_valid_categories[visibility_type].append(category)

                for setting in category_settings:

                    # Check whether the setting exist in fdmprinter.def.json or not.
                    # If the setting is defined in the wrong category or does not exist there then the test will fail
                    if setting not in self.all_settings_keys[category]:
                        not_valid_setting_by_category[visibility_type].append(setting)

                    # Add the 'basic' settings to the list
                    if visibility_type == "basic":
                        visible_settings_order.append(setting)


        # Check whether the settings are added in right order or not.
        # The basic settings should be in advanced, and advanced in expert
        for visibility_type in setting_visibility:

            # Skip the basic because it cannot be compared to previous list
            if visibility_type == 'basic':
                continue

            all_settings_in_this_type = []
            not_valid_setting_by_order[visibility_type] = []

            item = setting_visibility_items[visibility_type]
            for category, category_settings in item.items():
                all_settings_in_this_type.extend(category_settings)


            for setting in visible_settings_order:
                if setting not in all_settings_in_this_type:
                    not_valid_setting_by_order[visibility_type].append(setting)


        # If any of the settings is defined not correctly then the test is failed
        has_invalid_settings = False

        for type, settings in not_valid_categories.items():
            if len(settings) > 0:
                has_invalid_settings = True
                print("The following categories are defined incorrectly")
                print("  Visibility type : '%s'" % (type))
                print("  Incorrect categories : '%s'" % (settings))
                print()



        for type, settings in not_valid_setting_by_category.items():
            if len(settings) > 0:
                has_invalid_settings = True
                print("The following settings do not exist anymore in fdmprinter definition or in wrong category")
                print("  Visibility type : '%s'" % (type))
                print("  Incorrect settings : '%s'" % (settings))
                print()


        for type, settings in not_valid_setting_by_order.items():
            if len(settings) > 0:
                has_invalid_settings = True
                print("The following settings are defined in the incorrect order in setting visibility definitions")
                print("  Visibility type : '%s'" % (type))
                print("  Incorrect settings : '%s'" % (settings))

        return has_invalid_settings


if __name__ == "__main__":

    all_setting_visibility_files = glob.glob(os.path.join(os.path.join(SCRIPT_DIR, "..", "resources", "setting_visibility"), '*.cfg'))
    fdmprinter_def_path = os.path.join(SCRIPT_DIR, "..", "resources", "definitions", "fdmprinter.def.json")

    inspector = SettingVisibilityInspection()
    inspector.defineAllCuraSettings(fdmprinter_def_path)

    setting_visibility_items = {}
    for file_path in all_setting_visibility_files:
        temp = inspector.getSettingsFromSettingVisibilityFile(file_path)

        base_name = os.path.basename(file_path)
        visibility_type = base_name.split('.')[0]

        setting_visibility_items[visibility_type] = temp

    has_invalid_settings = inspector.validateSettingsVisibility(setting_visibility_items)

    sys.exit(0 if not has_invalid_settings else 1)
