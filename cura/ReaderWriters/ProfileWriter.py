# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the LGPLv3 or higher.

from UM.PluginObject import PluginObject


class ProfileWriter(PluginObject):
    """Base class for profile writer plugins.

    This class defines a write() function to write profiles to files with.
    """

    def __init__(self):
        """Initialises the profile writer.

        This currently doesn't do anything since the writer is basically static.
        """

        super().__init__()

    def write(self, path, profiles):
        """Writes a profile to the specified file path.

        The profile writer may write its own file format to the specified file.

        :param path: :type{string} The file to output to.
        :param profiles: :type{Profile} or :type{List} The profile(s) to write to the file.
        :return: True if the writing was successful, or False  if it wasn't.
        """

        raise NotImplementedError("Profile writer plugin was not correctly implemented. No write was specified.")
