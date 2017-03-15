# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import configparser #To parse the files we need to upgrade and write the new files.
import io #To serialise configparser output to a string.

from UM.VersionUpgrade import VersionUpgrade

_removed_settings = { #Settings that were removed in 2.5.
    "start_layers_at_same_position"
}

##  A collection of functions that convert the configuration of the user in Cura
#   2.4 to a configuration for Cura 2.5.
#
#   All of these methods are essentially stateless.
class VersionUpgrade24to25(VersionUpgrade):
    ##  Gets the version number from a CFG file in Uranium's 2.4 format.
    #
    #   Since the format may change, this is implemented for the 2.4 format only
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
        return int(parser.get("general", "version")) #Explicitly give an exception when this fails. That means that the file format is not recognised.

    ##  Upgrades the preferences file from version 2.4 to 2.5.
    #
    #   \param serialised The serialised form of a preferences file.
    #   \param filename The name of the file to upgrade.
    def upgradePreferences(self, serialised, filename):
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialised)

        #Remove settings from the visible_settings.
        if parser.has_section("general") and "visible_settings" in parser["general"]:
            visible_settings = parser["general"]["visible_settings"].split(";")
            visible_settings = filter(lambda setting: setting not in _removed_settings, visible_settings)
            parser["general"]["visible_settings"] = ";".join(visible_settings)

        #Change the version number in the file.
        if parser.has_section("general"): #It better have!
            parser["general"]["version"] = "5"

        #Re-serialise the file.
        output = io.StringIO()
        parser.write(output)
        return [filename], [output.getvalue()]

    ##  Upgrades an instance container from version 2.4 to 2.5.
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

        #Change the version number in the file.
        if parser.has_section("general"):
            parser["general"]["version"] = "3"

        #Re-serialise the file.
        output = io.StringIO()
        parser.write(output)
        return [filename], [output.getvalue()]