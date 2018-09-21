#!/usr/bin/env python3
#
# This script checks the correctness of the list of visibility settings
#
import collections
import configparser
import json
import os
import sys
from typing import Any, Dict, List

# Directory where this python file resides
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))


#
# This class
#
class SettingVisibilityInspection:

    def __init__(self) -> None:
        # The order of settings type. If the setting is in basic list then it also should be in expert
        self._setting_visibility_order = ["basic", "advanced", "expert"]

        # This is dictionary with categories as keys and all setting keys as values.
        self.all_settings_keys = {}  # type: Dict[str, List[str]]

    # Load all Cura setting keys from the given fdmprinter.json file
    def loadAllCuraSettingKeys(self, fdmprinter_json_path: str) -> None:
        with open(fdmprinter_json_path, "r", encoding = "utf-8") as f:
            json_data = json.load(f)

        # Get all settings keys in each category
        for key, data in json_data["settings"].items():  # top level settings are categories
            if "type" in data and data["type"] == "category":
                self.all_settings_keys[key] = []
                self._flattenSettings(data["children"], key)  # actual settings are children of top level category-settings

    def _flattenSettings(self, settings: Dict[str, str], category: str) -> None:
        for key, setting in settings.items():
            if "type" in setting and setting["type"] != "category":
                self.all_settings_keys[category].append(key)

            if "children" in setting:
                self._flattenSettings(setting["children"], category)

    # Loads the given setting visibility file and returns a dict with categories as keys and a list of setting keys as
    # values.
    def _loadSettingVisibilityConfigFile(self, file_name: str) -> Dict[str, List[str]]:
        with open(file_name, "r", encoding = "utf-8") as f:
            parser = configparser.ConfigParser(allow_no_value = True)
            parser.read_file(f)

        data_dict = {}
        for category, option_dict in parser.items():
            if category in (parser.default_section, "general"):
                continue

            data_dict[category] = []
            for key in option_dict:
                data_dict[category].append(key)

        return data_dict

    def validateSettingsVisibility(self, setting_visibility_files: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        # First load all setting visibility files into the dict "setting_visibility_dict" in the following structure:
        #  <visibility_name>  ->   <category>  ->  <list-fo-setting-keys>
        #     "basic"        ->     "info"
        setting_visibility_dict = {}  # type: Dict[str, Dict[str, List[str]]]
        for visibility_name, file_path in setting_visibility_files.items():
            setting_visibility_dict[visibility_name] = self._loadSettingVisibilityConfigFile(file_path)

        # The result is in the format:
        #   <visibility_name> -> dict
        #     "basic"    ->    "file_name":  "basic.cfg"
        #                      "is_valid":   True / False
        #                      "invalid_categories": List[str]
        #                      "invalid_settings":   Dict[category -> List[str]]
        #                      "missing_categories_from_previous": List[str]
        #                      "missing_settings_from_previous":   Dict[category -> List[str]]
        all_result_dict = dict()  # type: Dict[str, Dict[str, Any]]

        previous_result = None
        previous_visibility_dict = None
        is_all_valid = True
        for visibility_name in self._setting_visibility_order:
            invalid_categories = []
            invalid_settings = collections.defaultdict(list)

            this_visibility_dict = setting_visibility_dict[visibility_name]
            # Check if categories and keys exist at all
            for category, key_list in this_visibility_dict.items():
                if category not in self.all_settings_keys:
                    invalid_categories.append(category)
                    continue  # If this category doesn't exist at all, not need to check for details

                for key in key_list:
                    if key not in self.all_settings_keys[category]:
                        invalid_settings[category].append(key)

            is_settings_valid = len(invalid_categories) == 0 and len(invalid_settings) == 0
            file_path = setting_visibility_files[visibility_name]
            result_dict = {"file_name": os.path.basename(file_path),
                           "is_valid": is_settings_valid,
                           "invalid_categories": invalid_categories,
                           "invalid_settings": invalid_settings,
                           "missing_categories_from_previous": list(),
                           "missing_settings_from_previous": dict(),
                           }

            # If this is not the first item in the list, check if the settings are defined in the previous
            # visibility file.
            # A visibility with more details SHOULD add more settings. It SHOULD NOT remove any settings defined
            # in the less detailed visibility.
            if previous_visibility_dict is not None:
                missing_categories_from_previous = []
                missing_settings_from_previous = collections.defaultdict(list)

                for prev_category, prev_key_list in previous_visibility_dict.items():
                    # Skip the categories that are invalid
                    if prev_category in previous_result["invalid_categories"]:
                        continue
                    if prev_category not in this_visibility_dict:
                        missing_categories_from_previous.append(prev_category)
                        continue

                    this_key_list = this_visibility_dict[prev_category]
                    for key in prev_key_list:
                        # Skip the settings that are invalid
                        if key in previous_result["invalid_settings"][prev_category]:
                            continue

                        if key not in this_key_list:
                            missing_settings_from_previous[prev_category].append(key)

                result_dict["missing_categories_from_previous"] = missing_categories_from_previous
                result_dict["missing_settings_from_previous"] = missing_settings_from_previous
                is_settings_valid = len(missing_categories_from_previous) == 0 and len(missing_settings_from_previous) == 0
                result_dict["is_valid"] = result_dict["is_valid"] and is_settings_valid

            # Update the complete result dict
            all_result_dict[visibility_name] = result_dict
            previous_result = result_dict
            previous_visibility_dict = this_visibility_dict

            is_all_valid = is_all_valid and result_dict["is_valid"]

        all_result_dict["all_results"] = {"is_valid": is_all_valid}

        return all_result_dict

    def printResults(self, all_result_dict: Dict[str, Dict[str, Any]]) -> None:
        print("")
        print("Setting Visibility Check Results:")

        prev_visibility_name = None
        for visibility_name in self._setting_visibility_order:
            if visibility_name not in all_result_dict:
                continue

            result_dict = all_result_dict[visibility_name]
            print("=============================")
            result_str = "OK" if result_dict["is_valid"] else "INVALID"
            print("[%s] : [%s] : %s" % (visibility_name, result_dict["file_name"], result_str))

            if result_dict["is_valid"]:
                continue

            # Print details of invalid settings
            if result_dict["invalid_categories"]:
                print("It has the following non-existing CATEGORIES:")
                for category in result_dict["invalid_categories"]:
                    print(" - [%s]" % category)

            if result_dict["invalid_settings"]:
                print("")
                print("It has the following non-existing SETTINGS:")
                for category, key_list in result_dict["invalid_settings"].items():
                    for key in key_list:
                        print(" - [%s / %s]" % (category, key))

            if prev_visibility_name is not None:
                if result_dict["missing_categories_from_previous"]:
                    print("")
                    print("The following CATEGORIES are defined in the previous visibility [%s] but not here:" % prev_visibility_name)
                    for category in result_dict["missing_categories_from_previous"]:
                        print(" - [%s]" % category)

                if result_dict["missing_settings_from_previous"]:
                    print("")
                    print("The following SETTINGS are defined in the previous visibility [%s] but not here:" % prev_visibility_name)
                    for category, key_list in result_dict["missing_settings_from_previous"].items():
                        for key in key_list:
                            print(" - [%s / %s]" % (category, key))

            print("")
            prev_visibility_name = visibility_name


#
# Returns a dictionary of setting visibility .CFG files in the given search directory.
# The dict has the name of the visibility type as the key (such as "basic", "advanced", "expert"), and
# the actual file path (absolute path).
#
def getAllSettingVisiblityFiles(search_dir: str) -> Dict[str, str]:
    visibility_file_dict = dict()
    extension = ".cfg"
    for file_name in os.listdir(search_dir):
        file_path = os.path.join(search_dir, file_name)

        # Only check files that has the .cfg extension
        if not os.path.isfile(file_path):
            continue
        if not file_path.endswith(extension):
            continue

        base_filename = os.path.basename(file_name)[:-len(extension)]
        visibility_file_dict[base_filename] = file_path
    return visibility_file_dict


def main() -> None:
    setting_visibility_files_dir = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "resources", "setting_visibility"))
    fdmprinter_def_path = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "resources", "definitions", "fdmprinter.def.json"))

    setting_visibility_files_dict = getAllSettingVisiblityFiles(setting_visibility_files_dir)

    inspector = SettingVisibilityInspection()
    inspector.loadAllCuraSettingKeys(fdmprinter_def_path)

    check_result = inspector.validateSettingsVisibility(setting_visibility_files_dict)
    is_result_valid = check_result["all_results"]["is_valid"]
    inspector.printResults(check_result)

    sys.exit(0 if is_result_valid else 1)


if __name__ == "__main__":
    main()
