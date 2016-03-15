# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Mesh.MeshWriter import MeshWriter
from UM.Logger import Logger
from UM.Application import Application
import re #For escaping characters in the settings.
import copy


class GCodeWriter(MeshWriter):
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
        re.escape("\\"): "\\\\", #The escape character.
        re.escape("\n"): "\\n",  #Newlines. They break off the comment.
        re.escape("\r"): "\\r"   #Carriage return. Windows users may need this for visualisation in their editors.
    }

    def __init__(self):
        super().__init__()

    def write(self, stream, node, mode = MeshWriter.OutputMode.TextMode):
        if mode != MeshWriter.OutputMode.TextMode:
            Logger.log("e", "GCode Writer does not support non-text mode")
            return False

        scene = Application.getInstance().getController().getScene()
        gcode_list = getattr(scene, "gcode_list")
        if gcode_list:
            for gcode in gcode_list:
                stream.write(gcode)
            profile = self._serialiseProfile(Application.getInstance().getMachineManager().getWorkingProfile()) #Serialise the profile and put them at the end of the file.
            stream.write(profile)
            return True

        return False

    ##  Serialises the profile to prepare it for saving in the g-code.
    #
    #   The profile are serialised, and special characters (including newline)
    #   are escaped.
    #
    #   \param profile The profile to serialise.
    #   \return A serialised string of the profile.
    def _serialiseProfile(self, profile):
        prefix = ";SETTING_" + str(GCodeWriter.version) + " " #The prefix to put before each line.
        prefix_length = len(prefix)

        #Serialise a deepcopy to remove the defaults from the profile
        serialised = copy.deepcopy(profile).serialise()

        #Escape characters that have a special meaning in g-code comments.
        pattern = re.compile("|".join(GCodeWriter.escape_characters.keys()))
        serialised = pattern.sub(lambda m: GCodeWriter.escape_characters[re.escape(m.group(0))], serialised) #Perform the replacement with a regular expression.

        #Introduce line breaks so that each comment is no longer than 80 characters. Prepend each line with the prefix.
        result = ""
        for pos in range(0, len(serialised), 80 - prefix_length): #Lines have 80 characters, so the payload of each line is 80 - prefix.
            result += prefix + serialised[pos : pos + 80 - prefix_length] + "\n"
        serialised = result

        return serialised