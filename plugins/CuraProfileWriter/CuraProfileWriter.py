# Copyright (c) 2015 Ultimaker B.V.
# Copyright (c) 2013 David Braam
# Uranium is released under the terms of the LGPLv3 or higher.

from UM.Logger import Logger
from cura.ReaderWriters.ProfileWriter import ProfileWriter
import zipfile

##  Writes profiles to Cura's own profile format with config files.
class CuraProfileWriter(ProfileWriter):
    ##  Writes a profile to the specified file path.
    #
    #   \param path \type{string} The file to output to.
    #   \param profiles \type{Profile} \type{List} The profile(s) to write to that file.
    #   \return \code True \endcode if the writing was successful, or \code
    #   False \endcode if it wasn't.
    def write(self, path, profiles):
        if type(profiles) != list:
            profiles = [profiles]

        stream = open(path, "wb")  # Open file for writing in binary.
        archive = zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED)
        try:
            # Open the specified file.
            for profile in profiles:
                serialized = profile.serialize()
                profile_file = zipfile.ZipInfo(profile.getId())
                archive.writestr(profile_file, serialized)
        except Exception as e:
            Logger.log("e", "Failed to write profile to %s: %s", path, str(e))
            return False
        finally:
            archive.close()
        return True
