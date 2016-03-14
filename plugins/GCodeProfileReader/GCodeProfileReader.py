# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Application import Application #To get the machine manager to create the new profile in.
from UM.Settings.Profile import Profile
from UM.Settings.ProfileReader import ProfileReader
from UM.Logger import Logger
import re #Regular expressions for parsing escape characters in the settings.

##  A class that reads profile data from g-code files.
#
#   It reads the profile data from g-code files and stores it in a new profile.
#   This class currently does not process the rest of the g-code in any way.
class GCodeProfileReader(ProfileReader):
    ##  The file format version of the serialised g-code.
    #
    #   It can only read settings with the same version as the version it was
    #   written with. If the file format is changed in a way that breaks reverse
    #   compatibility, increment this version number!
    version = 1
    
    ##  Dictionary that defines how characters are escaped when embedded in
    #   g-code.
    #
    #   Note that the keys of this dictionary are regex strings. The values are
    #   not.
    escape_characters = {
        re.escape("\\\\"): "\\", #The escape character.
        re.escape("\\n"): "\n",  #Newlines. They break off the comment.
        re.escape("\\r"): "\r"   #Carriage return. Windows users may need this for visualisation in their editors.
    }

    ##  Initialises the g-code reader as a profile reader.
    def __init__(self):
        super().__init__()

    ##  Reads a g-code file, loading the profile from it.
    #
    #   \param file_name The name of the file to read the profile from.
    #   \return The profile that was in the specified file, if any. If the
    #   specified file was no g-code or contained no parsable profile, \code
    #   None \endcode is returned.
    def read(self, file_name):
        if file_name.split(".")[-1] != "gcode":
            return None

        prefix = ";SETTING_" + str(GCodeProfileReader.version) + " "
        prefix_length = len(prefix)

        #Loading all settings from the file. They are all at the end, but Python has no reverse seek any more since Python3. TODO: Consider moving settings to the start?
        serialised = "" #Will be filled with the serialised profile.
        try:
            with open(file_name) as f:
                for line in f:
                    if line.startswith(prefix):
                        serialised += line[prefix_length : -1] #Remove the prefix and the newline from the line, and add it to the rest.
        except IOError as e:
            Logger.log("e", "Unable to open file %s for reading: %s", file_name, str(e))
            return None

        #Unescape the serialised profile.
        pattern = re.compile("|".join(GCodeProfileReader.escape_characters.keys()))
        serialised = pattern.sub(lambda m: GCodeProfileReader.escape_characters[re.escape(m.group(0))], serialised) #Perform the replacement with a regular expression.

        #Apply the changes to the current profile.
        profile = Profile(machine_manager = Application.getInstance().getMachineManager(), read_only = False)
        try:
            profile.unserialise(serialised)
            profile.setType(None) #Force type to none so it's correctly added.
            profile.setReadOnly(False)
            profile.setDirty(True)
        except Exception as e: #Not a valid g-code file.
            Logger.log("e", "Unable to serialise the profile: %s", str(e))
            return None
        return profile