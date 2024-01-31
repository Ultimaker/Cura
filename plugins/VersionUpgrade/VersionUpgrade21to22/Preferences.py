# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser # To read config files.
import io # To output config files to string.
from typing import List, Optional, Tuple

import UM.VersionUpgrade # To indicate that a file is of the wrong format.

##  Creates a new preferences instance by parsing a serialised preferences file
#   in version 1 of the file format.
#
#   \param serialised The serialised form of a preferences file in version 1.
#   \param filename The supposed filename of the preferences file, without
#   extension.
#   \return A representation of those preferences, or None if the file format is
#   incorrect.
def importFrom(serialised: str, filename: str) -> Optional["Preferences"]:
    try:
        return Preferences(serialised, filename)
    except (configparser.Error, UM.VersionUpgrade.FormatException, UM.VersionUpgrade.InvalidVersionException):
        return None

##  A representation of preferences files as intermediary form for conversion
#   from one format to the other.
class Preferences:
    ##  Reads version 2 of the preferences file format, storing it in memory.
    #
    #   \param serialised A serialised version 2 preferences file.
    #   \param filename The supposed filename of the preferences file, without
    #   extension.
    def __init__(self, serialised: str, filename: str) -> None:
        self._filename = filename

        self._config = configparser.ConfigParser(interpolation = None)
        self._config.read_string(serialised)

        #Checking file correctness.
        if not self._config.has_section("general"):
            raise UM.VersionUpgrade.FormatException("No \"general\" section.")
        if not self._config.has_option("general", "version"):
            raise UM.VersionUpgrade.FormatException("No \"version\" in \"general\" section.")
        if int(self._config.get("general", "version")) != 2: # Explicitly hard-code version 2, since if this number changes the programmer MUST change this entire function.
            raise UM.VersionUpgrade.InvalidVersionException("The version of this preferences file is wrong. It must be 2.")
        if self._config.has_option("general", "name"): #This is probably a machine instance.
            raise UM.VersionUpgrade.FormatException("There is a \"name\" field in this configuration file. I suspect it is not a preferences file.")

    ##  Serialises these preferences as a preferences file of version 3.
    #
    #   This is where the actual translation happens.
    #
    #   \return A tuple containing the new filename and a serialised version of
    #   a preferences file in version 3.
    def export(self) -> Tuple[List[str], List[str]]:
        #Reset the cura/categories_expanded property since it works differently now.
        if self._config.has_section("cura") and self._config.has_option("cura", "categories_expanded"):
            self._config.remove_option("cura", "categories_expanded")

        #Translate the setting names in the visible settings.
        if self._config.has_section("machines") and self._config.has_option("machines", "setting_visibility"):
            visible_settings = self._config.get("machines", "setting_visibility")
            visible_settings_list = visible_settings.split(",")
            import VersionUpgrade21to22 #Import here to prevent a circular dependency.
            visible_settings_list = [VersionUpgrade21to22.VersionUpgrade21to22.VersionUpgrade21to22.translateSettingName(setting_name)
                                for setting_name in visible_settings_list]
            visible_settings = ",".join(visible_settings_list)
            self._config.set("machines", "setting_visibility", value = visible_settings)

        #Translate the active_instance key.
        if self._config.has_section("machines") and self._config.has_option("machines", "active_instance"):
            active_machine = self._config.get("machines", "active_instance")
            self._config.remove_option("machines", "active_instance")
            self._config.set("cura", "active_machine", active_machine)

        #Update the version number itself.
        self._config.set("general", "version", value = "3")

        #Output the result as a string.
        output = io.StringIO()
        self._config.write(output)
        return [self._filename], [output.getvalue()]