# Copyright (c) 2015 Ultimaker B.V.
# Copyright (c) 2013 David Braam
# Uranium is released under the terms of the AGPLv3 or higher.

from UM.Settings.Profile import Profile
from UM.Settings.ProfileWriter import ProfileWriter

##  Writes profiles to Cura's own profile format with config files.
class CuraProfileWriter(ProfileWriter):
    ##  Writes a profile to the specified stream.
    #
    #   \param stream \type{IOStream} The stream to write the profile to.
    #   \param profile \type{Profile} The profile to write to that stream.
    #   \return \code True \endcode if the writing was successful, or \code
    #   False \endcode if it wasn't.
    def write(self, stream, profile):
        serialised = profile.serialise()
        stream.write(serialised)
        return True
