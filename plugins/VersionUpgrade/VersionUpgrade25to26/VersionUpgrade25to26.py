# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import configparser #To parse the files we need to upgrade and write the new files.
import io #To serialise configparser output to a string.

from UM.VersionUpgrade import VersionUpgrade
from cura.CuraApplication import CuraApplication

_removed_settings = { #Settings that were removed in 2.5.
    "start_layers_at_same_position",
    "sub_div_rad_mult"
}

_split_settings = { #These settings should be copied to all settings it was split into.
    "support_interface_line_distance": {"support_roof_line_distance", "support_bottom_line_distance"}
}

##  A collection of functions that convert the configuration of the user in Cura
#   2.5 to a configuration for Cura 2.6.
#
#   All of these methods are essentially stateless.
class VersionUpgrade25to26(VersionUpgrade):
    ##  Gets the version number from a CFG file in Uranium's 2.5 format.
    #
    #   Since the format may change, this is implemented for the 2.5 format only
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

    ##  Upgrades the preferences file from version 2.5 to 2.6.
    #
    #   \param serialised The serialised form of a preferences file.
    #   \param filename The name of the file to upgrade.
    def upgradePreferences(self, serialised, filename):
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialised)

        #Remove settings from the visible_settings.
        if parser.has_section("general") and "visible_settings" in parser["general"]:
            visible_settings = parser["general"]["visible_settings"].split(";")
            new_visible_settings = []
            for setting in visible_settings:
                if setting in _removed_settings:
                    continue #Skip.
                if setting in _split_settings:
                    for replaced_setting in _split_settings[setting]:
                        new_visible_settings.append(replaced_setting)
                    continue #Don't add the original.
                new_visible_settings.append(setting) #No special handling, so just add the original visible setting back.
            parser["general"]["visible_settings"] = ";".join(new_visible_settings)

        #Change the version number in the file.
        if parser.has_section("general"): #It better have!
            parser["general"]["version"] = "5"

        #Re-serialise the file.
        output = io.StringIO()
        parser.write(output)
        return [filename], [output.getvalue()]

    ##  Upgrades an instance container from version 2.5 to 2.6.
    #
    #   \param serialised The serialised form of a quality profile.
    #   \param filename The name of the file to upgrade.
    def upgradeInstanceContainer(self, serialised, filename):
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialised)

        #Remove settings from the [values] section.
        if parser.has_section("values"):
            for removed_setting in (_removed_settings & parser["values"].keys()): #Both in keys that need to be removed and in keys present in the file.
                del parser["values"][removed_setting]
            for replaced_setting in (_split_settings.keys() & parser["values"].keys()):
                for replacement in _split_settings[replaced_setting]:
                    parser["values"][replacement] = parser["values"][replaced_setting] #Copy to replacement before removing the original!
                del replaced_setting

        for each_section in ("general", "metadata"):
            if not parser.has_section(each_section):
                parser.add_section(each_section)

        # Change the version number in the file.
        parser["metadata"]["setting_version"] = str(CuraApplication.SettingVersion)

        # Update version
        parser["general"]["version"] = "2"

        #Re-serialise the file.
        output = io.StringIO()
        parser.write(output)
        return [filename], [output.getvalue()]
