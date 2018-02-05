#!/usr/bin/env python
import configparser
import json
import os
import sys


class PresetSettingsValidator:

    def __init__(self, cura_dir: str):
        self._cura_dir = os.path.abspath(cura_dir)
        self._resource_dir = os.path.join(self._cura_dir, "resources")
        self._definitions_dir = os.path.join(self._resource_dir, "definitions")
        self._preset_settings_dir = os.path.join(self._resource_dir, "preset_setting_visibility_groups")

        self._fdmprinter_def_path = os.path.join(self._definitions_dir, "fdmprinter.def.json")

    def validate(self) -> bool:
        """
        Validates the preset settings files and returns True or False indicating whether there are invalid files.
        """
        if not os.path.isfile(self._fdmprinter_def_path):
            raise FileNotFoundError("[%s] is not a file or doesn't exist, please make sure you have specified the correct cura directory [%s]." % (self._fdmprinter_def_path, self._cura_dir))

        if not os.path.isdir(self._preset_settings_dir):
            raise FileNotFoundError("[%s] is not a directory or doesn't exist, please make sure you have specified the correct cura directory [%s]." % (self._preset_settings_dir, self._cura_dir))

        # parse the definition file
        setting_tree_dict = self._parse_definition_file(self._fdmprinter_def_path)

        has_invalid_files = False

        # go through all the preset settings files
        for root_dir, _, filenames in os.walk(self._preset_settings_dir):
            for filename in filenames:
                file_path = os.path.join(root_dir, filename)
                print("Validating [%s] ..." % file_path)

                incorrect_sections = []
                incorrect_settings = {}

                parser = configparser.ConfigParser(allow_no_value = True)
                with open(file_path, "r", encoding = "utf-8") as f:
                    parser.read_file(f)

                for key in parser:
                    # skip general
                    if key in ("general", configparser.DEFAULTSECT):
                        continue

                    if key not in setting_tree_dict:
                        incorrect_sections.append(key)
                        continue

                    for setting_key in parser[key]:
                        if setting_key not in setting_tree_dict[key]:
                            if setting_key not in incorrect_settings:
                                incorrect_settings[setting_key] = {"seen_in": [],
                                                                   "should_be_in": self._should_setting_be_in(setting_tree_dict, setting_key)}

                            incorrect_settings[setting_key]["seen_in"].append(key)

                # show results
                print("==========================================")
                if incorrect_sections or incorrect_settings:
                    has_invalid_files = True
                    print("[INVALID] [%s] is invalid, details below" % file_path)

                    # show details
                    for section_name in sorted(incorrect_sections):
                        print(" -- section name [%s] is incorrect, please check fdmprinter.def.json." % section_name)

                    for setting_name in sorted(incorrect_settings.keys()):
                        details_dict = incorrect_settings[setting_name]
                        msg = " -- setting [%s] is found in sections [%s], " % (setting_name, ", ".join(details_dict["seen_in"]))
                        if details_dict["should_be_in"] is not None:
                            msg += "but should be in section [%s] only." % details_dict["should_be_in"]
                        else:
                            msg += "but it cannot be found in fdmprinter.def.json"
                        print(msg)

                else:
                    print("[%s] is valid" % file_path)
                print("==========================================")

        return not has_invalid_files

    def _parse_definition_file(self, file_path: str):
        with open(file_path, "r", encoding = "utf-8") as f:
            def_dict = json.load(f, encoding = "utf-8")

        tree_dict = {}
        for key, item in def_dict.get("settings", {}).items():
            setting_list = []
            self._generate_tree(setting_list, item.get("children", {}))
            tree_dict[key] = setting_list

        return tree_dict

    def _generate_tree(self, setting_list: list, setting_dict: dict):
        for key, item in setting_dict.items():
            setting_list.append(key)
            if "children" in item:
                self._generate_tree(setting_list, item["children"])

    def _should_setting_be_in(self, setting_dict: dict, setting_name: str) -> str:
        """
        Check which section the given setting belongs to. Returns None if the setting cannot be found.
        """
        section_name = None
        for key, setting_list in setting_dict.items():
            if setting_name in setting_list:
                section_name = key
                break
        return section_name


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.realpath(__file__))
    cura_dir = os.path.abspath(os.path.join(script_dir, ".."))

    validator = PresetSettingsValidator(cura_dir)
    is_everything_validate = validator.validate()

    ret_code = 0 if is_everything_validate else 1
    sys.exit(ret_code)
