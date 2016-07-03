# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import configparser #To get version numbers from config files.

from UM.VersionUpgrade import VersionUpgrade # Superclass of the plugin.

from . import MachineInstance # To upgrade machine instances.
from . import Preferences #To upgrade preferences.
from . import Profile # To upgrade profiles.

##  How to translate printer names from the old version to the new.
_printer_translation = {
    "ultimaker2plus": "ultimaker2_plus"
}

##  How to translate profile names from the old version to the new.
_profile_translation = {
    "PLA": "generic_pla",
    "ABS": "generic_abs",
    "CPE": "generic_cpe"
}

##  How to translate setting names from the old version to the new.
_setting_name_translation = {
    "speed_support_lines": "speed_support_infill"
}

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

    ##  Translates a printer name that might have changed since the last
    #   version.
    #
    #   \param printer A printer name in Cura 2.1.
    #   \return The name of the corresponding printer in Cura 2.2.
    @staticmethod
    def translatePrinter(printer):
        if printer in _printer_translation:
            return _printer_translation[printer]
        return printer #Doesn't need to be translated.

    ##  Translates a built-in profile name that might have changed since the
    #   last version.
    #
    #   \param profile A profile name in the old version.
    #   \return The corresponding profile name in the new version.
    @staticmethod
    def translateProfile(profile):
        if profile in _profile_translation:
            return _profile_translation[profile]
        return profile #Doesn't need to be translated.

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

    ##  Translates a setting name for the change from Cura 2.1 to 2.2.
    #
    #   \param setting The name of a setting in Cura 2.1.
    #   \return The name of the corresponding setting in Cura 2.2.
    @staticmethod
    def translateSettingName(setting):
        if setting in _setting_name_translation:
            return _setting_name_translation[setting]
        return setting #Doesn't need to be translated.