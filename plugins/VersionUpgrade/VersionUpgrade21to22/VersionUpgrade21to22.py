# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import configparser #To get version numbers from config files.

from UM.VersionUpgrade import VersionUpgrade # Superclass of the plugin.

from . import MachineInstance # To upgrade machine instances.
from . import Preferences #To upgrade preferences.
from . import Profile # To upgrade profiles.

##  Converts configuration from Cura 2.1's file formats to Cura 2.2's.
#
#   It converts the machine instances and profiles.
class VersionUpgrade21to22(VersionUpgrade):
    ##  Gets the version number from a config file.
    #
    #   In all config files that concern this version upgrade, the version
    #   number is stored in general/version, so get the data from that key.
    #
    #   \param serialised The contents of a config file.
    #   \return \type{int} The version number of that config file.
    def getCfgVersion(self, serialised):
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialised)
        return int(parser.get("general", "version")) #Explicitly give an exception when this fails. That means that the file format is not recognised.

    ##  Converts machine instances from format version 1 to version 2.
    #
    #   \param serialised The serialised machine instance in version 1.
    #   \return The serialised machine instance in version 2, or None if the
    #   input was not of the correct format.
    def upgradeMachineInstance(self, serialised):
        machine_instance = MachineInstance.importFrom(serialised)
        if not machine_instance: #Invalid file format.
            return None
        return machine_instance.export()

    ##  Converts preferences from format version 2 to version 3.
    #
    #   \param serialised The serialised preferences file in version 2.
    #   \return The serialised preferences in version 3, or None if the input
    #   was not of the correct format.
    def upgradePreferences(self, serialised):
        preferences = Preferences.importFrom(serialised)
        if not preferences: #Invalid file format.
            return None
        return preferences.export()

    ##  Converts profiles from format version 1 to version 2.
    #
    #   \param serialised The serialised profile in version 1.
    #   \return The serialised profile in version 2, or None if the input was
    #   not of the correct format.
    def upgradeProfile(self, serialised):
        profile = Profile.importFrom(serialised)
        if not profile: # Invalid file format.
            return None
        return profile.export()

    @staticmethod
    def translatePrinters(printers):
        for index, printer in enumerate(printers):
            if printer == "ultimaker2plus":
                printers[index] = "ultimaker2_plus"

    ##  Updates settings for the change from Cura 2.1 to 2.2.
    #
    #   The keys and values of settings are changed to what they should be in
    #   the new version. Each setting is changed in-place in the provided
    #   dictionary. This changes the input parameter.
    #
    #   \param settings A dictionary of settings (as key-value pairs) to update.
    #   \return The same dictionary.
    @staticmethod
    def translateSettings(settings):
        for key, value in settings.items():
            if key == "speed_support_lines": # Setting key was changed for 2.2.
                del settings[key]
                settings["speed_support_infill"] = value
            if key == "retraction_combing": # Combing was made into an enum instead of a boolean.
                settings[key] = "off" if (value == "False") else "all"
        return settings

    ##  Translates setting names for the change from Cura 2.1 to 2.2.
    #
    #   The setting names are changed in-place in the provided list. This changes
    #   the input parameter.
    #
    #   \param settings A list of setting names to update.
    #   \return The same list.
    @staticmethod
    def translateSettingNames(settings):
        for i in range(0, len(settings)):
            if settings[i] == "speed_support_lines":
                settings[i] = "speed_support_infill"
        return settings