# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import configparser #To read config files.
import io #To output config files to string.

import UM.VersionUpgrade #To indicate that a file is of the wrong format.

##  Creates a new preferences instance by parsing a serialised preferences file
#   in version 1 of the file format.
#
#   \param serialised The serialised form of a preferences file in version 1.
#   \return A representation of those preferences, or None if the file format is
#   incorrect.
def importFrom(serialised):
    try:
        return Preferences(serialised)
    except (configparser.Error, UM.VersionUpgrade.FormatException, UM.VersionUpgrade.InvalidVersionException):
        return None

##  A representation of preferences files as intermediary form for conversion
#   from one format to the other.
class Preferences:
    ##  Reads version 2 of the preferences file format, storing it in memory.
    #
    #   \param serialised A serialised version 2 preferences file.
    def __init__(self, serialised):
        self._config = configparser.ConfigParser(interpolation = None)
        self._config.read_string(serialised)

        #Checking file correctness.
        if not self._config.has_section("general"):
            raise UM.VersionUpgrade.FormatException("No \"general\" section.")
        if not self._config.has_option("general", "version"):
            raise UM.VersionUpgrade.FormatException("No \"version\" in \"general\" section.")
        if int(self._config.get("general", "version")) != 2: # Explicitly hard-code version 2, since if this number changes the programmer MUST change this entire function.
            raise UM.VersionUpgrade.InvalidVersionException("The version of this preferences file is wrong. It must be 2.")

    ##  Serialises these preferences as a preferences file of version 3.
    #
    #   This is where the actual translation happens.
    #
    #   \return A serialised version of a preferences file in version 3.
    def export(self):
        #Reset the cura/categories_expanded property since it works differently now.
        if self._config.has_section("cura") and self._config.has_option("cura", "categories_expanded"):
            self._config.remove_option("cura", "categories_expanded")

        #Translate the setting names in the visible settings.
        if self._config.has_section("machines") and self._config.has_option("machines", "setting_visibility"):
            visible_settings = self._config.get("machines", "setting_visibility")
            visible_settings = visible_settings.split(",")
            import VersionUpgrade21to22 #Import here to prevent a circular dependency.
            VersionUpgrade21to22.VersionUpgrade21to22.VersionUpgrade21to22.translateSettingNames(visible_settings)
            visible_settings = visible_settings.join(",")
            self._config.set("machines", "setting_visibility", value = visible_settings)

        #Update the version number itself.
        self._config.set("general", "version", value = "3")

        #Output the result as a string.
        output = io.StringIO()
        self._config.write(output)
        return output.getvalue()