# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Application import Application #To get the machine manager to create the new profile in.
from UM.Logger import Logger
from UM.Settings.Profile import Profile
from UM.Settings.ProfileReader import ProfileReader

##  A plugin that reads profile data from Cura profile files.
#
#   It reads a profile from a .curaprofile file, and returns it as a profile
#   instance.
class CuraProfileReader(ProfileReader):
    ##  Initialises the cura profile reader.
    #
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
        profile = Profile(machine_manager = Application.getInstance().getMachineManager(), read_only = False) #Create an empty profile.
        serialised = ""
        try:
            with open(file_name) as f: #Open file for reading.
                serialised = f.read()
        except IOError as e:
            Logger.log("e", "Unable to open file %s for reading: %s", file_name, str(e))
            return None
        
        try:
            profile.unserialise(serialised)
        except Exception as e: #Parsing error. This is not a (valid) Cura profile then.
            return None
        return profile