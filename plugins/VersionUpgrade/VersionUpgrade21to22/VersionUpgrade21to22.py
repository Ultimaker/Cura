# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.VersionUpgrade import VersionUpgrade # Superclass of the plugin.

from . import MachineInstance # To upgrade machine instances.
from . import Profile # To upgrade profiles.

##  Converts configuration from Cura 2.1's file formats to Cura 2.2's.
#
#   It converts the machine instances and profiles.
class VersionUpgrade21to22(VersionUpgrade):
    ##  Converts machine instances from format version 1 to version 2.
    #
    #   \param serialised The serialised machine instance in version 1.
    #   \return The serialised machine instance in version 2, or None if the
    #   input was not of the correct format.
    def upgradeMachineInstance(self, serialised):
        machine_instance = MachineInstance.importVersion1(serialised)
        if not machine_instance: #Invalid file format.
            return None
        return machine_instance.exportVersion2()

    ##  Converts profiles from format version 1 to version 2.
    #
    #   \param serialised The serialised profile in version 1.
    #   \return The serialised profile in version 2, or None if the input was
    #   not of the correct format.
    def upgradeProfile(self, serialised):
        profile = Profile.importVersion1(serialised)
        if not profile: # Invalid file format.
            return None
        return profile.exportVersion2()

    ##  Translates settings for the change from Cura 2.1 to 2.2.
    #
    #   Each setting is changed in-place in the provided dictionary. This
    #   changes the input parameter.
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