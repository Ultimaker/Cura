# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import configparser #To parse preference files.
import io #To serialise the preference files afterwards.

from UM.VersionUpgrade import VersionUpgrade #We're inheriting from this.

_renamed_themes = {
    "cura": "cura-light"
}
_renamed_i18n = {
    "7s": "en_7S",
    "de": "de_DE",
    "en": "en_US",
    "es": "es_ES",
    "fi": "fi_FI",
    "fr": "fr_FR",
    "hu": "hu_HU",
    "it": "it_IT",
    "jp": "ja_JP",
    "ko": "ko_KR",
    "nl": "nl_NL",
    "pl": "pl_PL",
    "ptbr": "pt_BR",
    "ru": "ru_RU",
    "tr": "tr_TR"
}


class VersionUpgrade27to30(VersionUpgrade):
    ##  Gets the version number from a CFG file in Uranium's 2.7 format.
    #
    #   Since the format may change, this is implemented for the 2.7 format only
    #   and needs to be included in the version upgrade system rather than
    #   globally in Uranium.
    #
    #   \param serialised The serialised form of a CFG file.
    #   \return The version number stored in the CFG file.
    #   \raises ValueError The format of the version number in the file is
    #   incorrect.
    #   \raises KeyError The format of the file is incorrect.
    def getCfgVersion(self, serialised):
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialised)
        format_version = int(parser.get("general", "version")) #Explicitly give an exception when this fails. That means that the file format is not recognised.
        setting_version = int(parser.get("metadata", "setting_version", fallback = 0))
        return format_version * 1000000 + setting_version

    ##  Upgrades a preferences file from version 2.7 to 3.0.
    #
    #   \param serialised The serialised form of a preferences file.
    #   \param filename The name of the file to upgrade.
    def upgradePreferences(self, serialised, filename):
        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(serialised)

        # Update version numbers
        if "general" not in parser:
            parser["general"] = {}
        parser["general"]["version"] = "5"
        if "metadata" not in parser:
            parser["metadata"] = {}
        parser["metadata"]["setting_version"] = "3"

        #Renamed themes.
        if "theme" in parser["general"]:
            if parser["general"]["theme"] in _renamed_themes:
                parser["general"]["theme"] = _renamed_themes[parser["general"]["theme"]]

        #Renamed languages.
        if "language" in parser["general"]:
            if parser["general"]["language"] in _renamed_i18n:
                parser["general"]["language"] = _renamed_i18n[parser["general"]["language"]]

        # Renamed settings for skin pre-shrink settings
        if parser.has_section("general") and "visible_settings" in parser["general"]:
            visible_settings = parser["general"]["visible_settings"].split(";")
            new_visible_settings = []
            renamed_skin_preshrink_names = {"expand_upper_skins": "top_skin_expand_distance",
                                            "expand_lower_skins": "bottom_skin_expand_distance"}
            for setting in visible_settings:
                if setting == "expand_skins_into_infill":
                    continue # this one is removed
                if setting in renamed_skin_preshrink_names:
                    new_visible_settings.append(renamed_skin_preshrink_names[setting])
                    continue #Don't add the original.
                new_visible_settings.append(setting) #No special handling, so just add the original visible setting back.
            parser["general"]["visible_settings"] = ";".join(new_visible_settings)

        # Re-serialise the file.
        output = io.StringIO()
        parser.write(output)
        return [filename], [output.getvalue()]

    ##  Upgrades the given instance container file from version 2.7 to 3.0.
    #
    #   \param serialised The serialised form of the container file.
    #   \param filename The name of the file to upgrade.
    def upgradeOtherContainer(self, serialised, filename):
        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(serialised)

        # Update the skin pre-shrink settings:
        #  - Remove the old ones
        #  - Do not add the new ones. The default values will be used for them.
        if parser.has_section("values"):
            for remove_key in ["expand_skins_into_infill", "expand_upper_skins", "expand_lower_skins"]:
                if remove_key in parser["values"]:
                    del parser["values"][remove_key]

        for each_section in ("general", "metadata"):
            if not parser.has_section(each_section):
                parser.add_section(each_section)

        # Update version numbers
        parser["general"]["version"] = "2"
        parser["metadata"]["setting_version"] = "3"

        # Re-serialise the file.
        output = io.StringIO()
        parser.write(output)
        return [filename], [output.getvalue()]

    ##  Upgrades a container stack from version 2.7 to 3.0.
    #
    #   \param serialised The serialised form of a container stack.
    #   \param filename The name of the file to upgrade.
    def upgradeStack(self, serialised, filename):
        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(serialised)

        for each_section in ("general", "metadata"):
            if not parser.has_section(each_section):
                parser.add_section(each_section)

        # Update version numbers
        if "general" not in parser:
            parser["general"] = {}
        parser["general"]["version"] = "3"

        if "metadata" not in parser:
            parser["metadata"] = {}
        parser["metadata"]["setting_version"] = "3"

        # Re-serialise the file.
        output = io.StringIO()
        parser.write(output)
        return [filename], [output.getvalue()]
