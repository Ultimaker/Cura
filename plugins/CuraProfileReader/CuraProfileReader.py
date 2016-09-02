# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import os.path

from UM.Logger import Logger
from UM.Settings.InstanceContainer import InstanceContainer  # The new profile to make.
from cura.ProfileReader import ProfileReader

import zipfile

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
        try:
            archive = zipfile.ZipFile(file_name, "r")
        except Exception:
            # zipfile doesn't give proper exceptions, so we can only catch broad ones
            return []
        results = []
        for profile_id in archive.namelist():
            # Create an empty profile.
            profile = InstanceContainer(profile_id)
            profile.addMetaDataEntry("type", "quality_changes")
            serialized = ""
            with archive.open(profile_id) as f:
                serialized = f.read()
            try:
                profile.deserialize(serialized.decode("utf-8") )
            except Exception as e:  # Parsing error. This is not a (valid) Cura profile then.
                Logger.log("e", "Error while trying to parse profile: %s", str(e))
                continue
            results.append(profile)
        return results