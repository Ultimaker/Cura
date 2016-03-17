# Copyright (c) 2015 Ultimaker B.V.
# Copyright (c) 2013 David Braam
# Uranium is released under the terms of the AGPLv3 or higher.

from UM.Logger import Logger
from UM.SaveFile import SaveFile
from UM.Settings.ProfileWriter import ProfileWriter

##  Writes profiles to Cura's own profile format with config files.
class CuraProfileWriter(ProfileWriter):
    ##  Writes a profile to the specified file path.
    #
    #   \param path \type{string} The file to output to.
    #   \param profile \type{Profile} The profile to write to that file.
    #   \return \code True \endcode if the writing was successful, or \code
    #   False \endcode if it wasn't.
    def write(self, path, profile):
        serialised = profile.serialise()
        try:
            with SaveFile(path, "wt", -1, "utf-8") as f: #Open the specified file.
                f.write(serialised)
        except Exception as e:
            Logger.log("e", "Failed to write profile to %s: %s", path, str(e))
            return False
        return True
