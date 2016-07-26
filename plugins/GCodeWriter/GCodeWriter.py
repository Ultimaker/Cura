# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Mesh.MeshWriter import MeshWriter
from UM.Logger import Logger
from UM.Application import Application
import UM.Settings.ContainerRegistry

from cura.CuraApplication import CuraApplication
from cura.Settings.ExtruderManager import ExtruderManager

import re #For escaping characters in the settings.
import json

##  Writes g-code to a file.
#
#   While this poses as a mesh writer, what this really does is take the g-code
#   in the entire scene and write it to an output device. Since the g-code of a
#   single mesh isn't separable from the rest what with rafts and travel moves
#   and all, it doesn't make sense to write just a single mesh.
#
#   So this plug-in takes the g-code that is stored in the root of the scene
#   node tree, adds a bit of extra information about the profiles and writes
#   that to the output device.
class GCodeWriter(MeshWriter):
    ##  The file format version of the serialised g-code.
    #
    #   It can only read settings with the same version as the version it was
    #   written with. If the file format is changed in a way that breaks reverse
    #   compatibility, increment this version number!
    version = 3

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
    def _serialiseSettings(self, stack):
        prefix = ";SETTING_" + str(GCodeWriter.version) + " "  # The prefix to put before each line.
        prefix_length = len(prefix)

        container_with_profile = stack.findContainer({"type": "quality"})
        machine_manager = CuraApplication.getInstance().getMachineManager()

        # Duplicate the current quality profile and update it with any user settings.
        flat_quality_id = machine_manager.duplicateContainer(container_with_profile.getId())

        flat_quality = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id = flat_quality_id)[0]
        flat_quality._dirty = False
        user_settings = stack.getTop()

        # We don't want to send out any signals, so disconnect them.
        flat_quality.propertyChanged.disconnectAll()

        for key in user_settings.getAllKeys():
            flat_quality.setProperty(key, "value", user_settings.getProperty(key, "value"))

        serialized = flat_quality.serialize()

        data = {"global_quality": serialized}
        manager = ExtruderManager.getInstance()
        for extruder in manager.getMachineExtruders(stack.getId()):
            extruder_quality = extruder.findContainer({"type": "quality"})

            flat_extruder_quality_id = machine_manager.duplicateContainer(extruder_quality.getId())
            flat_extruder_quality = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id=flat_extruder_quality_id)[0]
            flat_extruder_quality._dirty = False
            extruder_user_settings = extruder.getTop()

            # We don't want to send out any signals, so disconnect them.
            flat_extruder_quality.propertyChanged.disconnectAll()

            for key in extruder_user_settings.getAllKeys():
                flat_extruder_quality.setProperty(key, "value", extruder_user_settings.getProperty(key, "value"))

            extruder_serialized = flat_extruder_quality.serialize()
            data.setdefault("extruder_quality", []).append(extruder_serialized)

        json_string = json.dumps(data)

        # Escape characters that have a special meaning in g-code comments.
        pattern = re.compile("|".join(GCodeWriter.escape_characters.keys()))

        # Perform the replacement with a regular expression.
        escaped_string = pattern.sub(lambda m: GCodeWriter.escape_characters[re.escape(m.group(0))], json_string)

        # Introduce line breaks so that each comment is no longer than 80 characters. Prepend each line with the prefix.
        result = ""

        # Lines have 80 characters, so the payload of each line is 80 - prefix.
        for pos in range(0, len(escaped_string), 80 - prefix_length):
            result += prefix + escaped_string[pos : pos + 80 - prefix_length] + "\n"
        return result
