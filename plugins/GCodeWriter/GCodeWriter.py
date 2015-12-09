# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Mesh.MeshWriter import MeshWriter
from UM.Logger import Logger
from UM.Application import Application
import io
import re #For escaping characters in the settings.


class GCodeWriter(MeshWriter):
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
            profile = self._serialiseProfile(Application.getInstance().getMachineManager().getActiveProfile()) #Serialise the profile and put them at the end of the file.
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
        serialised = profile.serialise()
        
        #Escape characters that have a special meaning in g-code comments.
        escape_characters = { #Which special characters (keys) are replaced by what escape character (values).
                              #Note: The keys are regex strings. Values are not.
            "\\": "\\\\", #The escape character.
            "\n": "\\n",  #Newlines. They break off the comment.
            "\r": "\\r",  #Carriage return. Windows users may need this for visualisation in their editors.
        }
        pattern = re.compile("|".join(escape_characters.keys()))
        serialised = pattern.sub(lambda m: escape_characters[m.group(0)], serialised) #Perform the replacement with a regular expression.
        
        #TODO: Introduce line breaks so that each comment is no longer than 80 characters.
        #TODO: Prepend a prefix that includes the keyword "SETTING" and a serialised version number.
        
        return ";" + serialised