# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Mesh.MeshWriter import MeshWriter
from UM.Logger import Logger
from UM.Application import Application
import re #For escaping characters in the settings.


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
        re.escape("\\"): "\\\\",  # The escape character.
        re.escape("\n"): "\\n",   # Newlines. They break off the comment.
        re.escape("\r"): "\\r"    # Carriage return. Windows users may need this for visualisation in their editors.
    }

    def __init__(self):
        super().__init__()

    def write(self, stream, node, mode = MeshWriter.OutputMode.TextMode):
        if mode != MeshWriter.OutputMode.TextMode:
            Logger.log("e", "GCode Writer does not support non-text mode.")
            return False

        scene = Application.getInstance().getController().getScene()
        gcode_list = getattr(scene, "gcode_list")
        if gcode_list:
            for gcode in gcode_list:
                stream.write(gcode)
            # Serialise the current container stack and put it at the end of the file.
            settings = self._serialiseSettings(Application.getInstance().getGlobalContainerStack())
            stream.write(settings)
            return True

        return False

    ##  Serialises a container stack to prepare it for writing at the end of the
    #   g-code.
    #
    #   The settings are serialised, and special characters (including newline)
    #   are escaped.
    #
    #   \param settings A container stack to serialise.
    #   \return A serialised string of the settings.
    def _serialiseSettings(self, settings):
        prefix = ";SETTING_" + str(GCodeWriter.version) + " "  # The prefix to put before each line.
        prefix_length = len(prefix)

        #TODO: This just serialises the container stack, which only indicates the IDs of the containers in that stack, not the settings themselves, making this about 9001x as useless as the fax functionality in Adobe Acrobat.
        serialised = settings.serialize()

        # Escape characters that have a special meaning in g-code comments.
        pattern = re.compile("|".join(GCodeWriter.escape_characters.keys()))
        # Perform the replacement with a regular expression.
        serialised = pattern.sub(lambda m: GCodeWriter.escape_characters[re.escape(m.group(0))], serialised)

        # Introduce line breaks so that each comment is no longer than 80 characters. Prepend each line with the prefix.
        result = ""

        # Lines have 80 characters, so the payload of each line is 80 - prefix.
        for pos in range(0, len(serialised), 80 - prefix_length):
            result += prefix + serialised[pos : pos + 80 - prefix_length] + "\n"
        serialised = result

        return serialised