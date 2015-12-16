# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Application import Application #To get the machine manager to create the new profile in.
from UM.Settings.Profile import Profile
from UM.Settings.ProfileReader import ProfileReader
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
        prefix = ";SETTING_" + str(version) + " "
        
        #Loading all settings from the file. They are all at the end, but Python has no reverse seek any more since Python3. TODO: Consider moving settings to the start?
        serialised = "" #Will be filled with the serialised profile.
        try:
            with open(file_name) as f:
                for line in f:
                    if line.startswith(prefix):
                        serialised += line[len(prefix):-1] #Remove the prefix and the newline from the line, and add it to the rest.
        except IOError as e:
            Logger.log("e", "Unable to open file %s for reading: %s", file_name, str(e))
            return None

        #Unescape the serialised profile.
        escape_characters = { #Which special characters (keys) are replaced by what escape character (values).
                              #Note: The keys are regex strings. Values are not.
            "\\\\": "\\", #The escape character.
            "\\n": "\n",  #Newlines. They break off the comment.
            "\\r": "\r"   #Carriage return. Windows users may need this for visualisation in their editors.
        }
        escape_characters = dict((re.escape(key), value) for key, value in escape_characters.items())
        pattern = re.compile("|".join(escape_characters.keys()))
        serialised = pattern.sub(lambda m: escape_characters[re.escape(m.group(0))], serialised) #Perform the replacement with a regular expression.
        
        #Apply the changes to the current profile.
        profile = Profile(machine_manager = Application.getInstance().getMachineManager(), read_only = False)
        try:
            profile.unserialise(serialised)
        except Exception as e: #Not a valid g-code file.
            return None
        return profile