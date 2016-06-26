# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import os.path

from UM.Application import Application #To get the machine manager to create the new profile in.
from UM.Logger import Logger
from UM.Settings.InstanceContainer import InstanceContainer #The new profile to make.
from cura.ProfileReader import ProfileReader

##  A plugin that reads profile data from Cura profile files.
#
#   It reads a profile from a .curaprofile file, and returns it as a profile
#   instance.
class CuraProfileReader(ProfileReader):
    ##  Initialises the cura profile reader.
    #   This does nothing since the only other function is basically stateless.
    def __init__(self):
        super().__init__()

    ##  Reads a cura profile from a file and returns it.
    #
    #   \param file_name The file to read the cura profile from.
    #   \return The cura profile that was in the file, if any. If the file could
    #   not be read or didn't contain a valid profile, \code None \endcode is
    #   returned.
    def read(self, file_name):
        # Create an empty profile.
        profile = InstanceContainer(os.path.basename(os.path.splitext(file_name)[0]))
        profile.addMetaDataEntry("type", "quality")
        try:
            with open(file_name) as f:  # Open file for reading.
                serialized = f.read()
        except IOError as e:
            Logger.log("e", "Unable to open file %s for reading: %s", file_name, str(e))
            return None
        
        try:
            profile.deserialize(serialized)
        except Exception as e:  # Parsing error. This is not a (valid) Cura profile then.
            Logger.log("e", "Error while trying to parse profile: %s", str(e))
            return None
        return profile