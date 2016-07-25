# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import configparser #To get version numbers from config files.

from UM.VersionUpgrade import VersionUpgrade # Superclass of the plugin.

from . import MachineInstance # To upgrade machine instances.
from . import Preferences #To upgrade preferences.
from . import Profile # To upgrade profiles.

##  How to translate printer names from the old version to the new.
_printer_translations = {
    "ultimaker2plus": "ultimaker2_plus"
}

##  How to translate profile names from the old version to the new.
_profile_translations = {
    "PLA": "generic_pla",
    "ABS": "generic_abs",
    "CPE": "generic_cpe",
    "Low Quality": "low",
    "Normal Quality": "normal",
    "High Quality": "high",
    "Ulti Quality": "high" #This one doesn't have an equivalent. Map it to high.
}

##  How to translate setting names from the old version to the new.
_setting_name_translations = {
    "remove_overlapping_walls_0_enabled": "travel_compensate_overlapping_walls_0_enabled",
    "remove_overlapping_walls_enabled": "travel_compensate_overlapping_walls_enabled",
    "remove_overlapping_walls_x_enabled": "travel_compensate_overlapping_walls_x_enabled",
    "retraction_hop": "retraction_hop_enabled",
    "skirt_line_width": "skirt_brim_line_width",
    "skirt_minimal_length": "skirt_brim_minimal_length",
    "skirt_speed": "skirt_brim_speed",
    "speed_support_lines": "speed_support_infill"
}

##  How to translate variants of specific machines from the old version to the
#   new.
_variant_translations = {
    "ultimaker2_plus": {
        "0.25 mm": "ultimaker2_plus_0.25",
        "0.4 mm": "ultimaker2_plus_0.4",
        "0.6 mm": "ultimaker2_plus_0.6",
        "0.8 mm": "ultimaker2_plus_0.8"
    },
    "ultimaker2_extended_plus": {
        "0.25 mm": "ultimaker2_extended_plus_0.25",
        "0.4 mm": "ultimaker2_extended_plus_0.4",
        "0.6 mm": "ultimaker2_extended_plus_0.6",
        "0.8 mm": "ultimaker2_extended_plus_0.8"
    }
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
    #   \param filename The supposed file name of the machine instance, without
    #   extension.
    #   \return A tuple containing the new filename and the serialised machine
    #   instance in version 2, or None if the input was not of the correct
    #   format.
    def upgradeMachineInstance(self, serialised, filename):
        machine_instance = MachineInstance.importFrom(serialised, filename)
        if not machine_instance: #Invalid file format.
            return filename, None
        return machine_instance.export()

    ##  Converts preferences from format version 2 to version 3.
    #
    #   \param serialised The serialised preferences file in version 2.
    #   \param filename THe supposed file name of the preferences file, without
    #   extension.
    #   \return A tuple containing the new filename and the serialised
    #   preferences in version 3, or None if the input was not of the correct
    #   format.
    def upgradePreferences(self, serialised, filename):
        preferences = Preferences.importFrom(serialised, filename)
        if not preferences: #Invalid file format.
            return filename, None
        return preferences.export()

    ##  Converts profiles from format version 1 to version 2.
    #
    #   \param serialised The serialised profile in version 1.
    #   \param filename The supposed file name of the profile, without
    #   extension.
    #   \return A tuple containing the new filename and the serialised profile
    #   in version 2, or None if the input was not of the correct format.
    def upgradeProfile(self, serialised, filename):
        profile = Profile.importFrom(serialised, filename)
        if not profile: # Invalid file format.
            return filename, None
        return profile.export()

    ##  Translates a printer name that might have changed since the last
    #   version.
    #
    #   \param printer A printer name in Cura 2.1.
    #   \return The name of the corresponding printer in Cura 2.2.
    @staticmethod
    def translatePrinter(printer):
        if printer in _printer_translations:
            return _printer_translations[printer]
        return printer #Doesn't need to be translated.

    ##  Translates a built-in profile name that might have changed since the
    #   last version.
    #
    #   \param profile A profile name in the old version.
    #   \return The corresponding profile name in the new version.
    @staticmethod
    def translateProfile(profile):
        if profile in _profile_translations:
            return _profile_translations[profile]
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
            if key == "fill_perimeter_gaps": #Setting is removed.
                del settings[key]
            elif key == "remove_overlapping_walls_0_enabled": #Setting is functionally replaced.
                del settings[key]
                settings["travel_compensate_overlapping_walls_0_enabled"] = value
            elif key == "remove_overlapping_walls_enabled": #Setting is functionally replaced.
                del settings[key]
                settings["travel_compensate_overlapping_walls_enabled"] = value
            elif key == "remove_overlapping_walls_x_enabled": #Setting is functionally replaced.
                del settings[key]
                settings["travel_compensate_overlapping_walls_x_enabled"] = value
            elif key == "retraction_combing": #Combing was made into an enum instead of a boolean.
                settings[key] = "off" if (value == "False") else "all"
            elif key == "retraction_hop": #Setting key was changed.
                del settings[key]
                settings["retraction_hop_enabled"] = value
            elif key == "skirt_minimal_length": #Setting key was changed.
                del settings[key]
                settings["skirt_brim_minimal_length"] = value
            elif key == "skirt_line_width": #Setting key was changed.
                del settings[key]
                settings["skirt_brim_line_width"] = value
            elif key == "skirt_speed": #Setting key was changed.
                del settings[key]
                settings["skirt_brim_speed"] = value
            elif key == "speed_support_lines": #Setting key was changed.
                del settings[key]
                settings["speed_support_infill"] = value
        return settings

    ##  Translates a setting name for the change from Cura 2.1 to 2.2.
    #
    #   \param setting The name of a setting in Cura 2.1.
    #   \return The name of the corresponding setting in Cura 2.2.
    @staticmethod
    def translateSettingName(setting):
        if setting in _setting_name_translations:
            return _setting_name_translations[setting]
        return setting #Doesn't need to be translated.

    ##  Translates a variant name for the change from Cura 2.1 to 2.2
    #
    #   \param variant The name of a variant in Cura 2.1.
    #   \param machine The name of the machine this variant is part of in Cura
    #   2.2's naming.
    #   \return The name of the corresponding variant in Cura 2.2.
    @staticmethod
    def translateVariant(variant, machine):
        if machine in _variant_translations and variant in _variant_translations[machine]:
            return _variant_translations[machine][variant]
        return variant