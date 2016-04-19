# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.VersionUpgrade import VersionUpgrade #Superclass of the plugin.

from . import MachineInstance #To upgrade machine instances.
from . import Preferences #To upgrade preferences.
from . import Profile #To upgrade profiles.

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
        if not profile: #Invalid file format.
            return None
        return profile.exportVersion2()