# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.PluginObject import PluginObject


# Exception when there is no profile to import from a given files.
# Note that this should not be treated as an exception but as an information instead.
class NoProfileException(Exception):
    pass


class ProfileReader(PluginObject):
    """A type of plug-ins that reads profiles from a file.
    
    The profile is then stored as instance container of the type user profile.
    """

    def __init__(self):
        super().__init__()

    def read(self, file_name):
        """Read profile data from a file and return a filled profile.
        
        :return: :type{Profile|Profile[]} The profile that was obtained from the file or a list of Profiles.
        """

        raise NotImplementedError("Profile reader plug-in was not correctly implemented. The read function was not implemented.")
