# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Mesh.MeshWriter import MeshWriter
from UM.Logger import Logger
from UM.Application import Application
import UM.Settings.ContainerRegistry

from cura.CuraApplication import CuraApplication
from cura.Settings.ExtruderManager import ExtruderManager

from UM.Settings.InstanceContainer import InstanceContainer

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

    ##  Create a new container with container 2 as base and container 1 written over it.
    def _createFlattenedContainerInstance(self, instance_container1, instance_container2):
        flat_container = InstanceContainer(instance_container2.getName())
        if instance_container1.getDefinition():
            flat_container.setDefinition(instance_container1.getDefinition())
        else:
            flat_container.setDefinition(instance_container2.getDefinition())
        flat_container.setMetaData(instance_container2.getMetaData())

        for key in instance_container2.getAllKeys():
            flat_container.setProperty(key, "value", instance_container2.getProperty(key, "value"))

        for key in instance_container1.getAllKeys():
            flat_container.setProperty(key, "value", instance_container1.getProperty(key, "value"))
        return flat_container


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

        container_with_profile = stack.findContainer({"type": "quality_changes"})
        if not container_with_profile:
            Logger.log("e", "No valid quality profile found, not writing settings to GCode!")
            return ""

        flat_global_container = self._createFlattenedContainerInstance(stack.getTop(), container_with_profile)
        serialized = flat_global_container.serialize()
        data = {"global_quality": serialized}

        for extruder in ExtruderManager.getInstance().getMachineExtruders(stack.getId()):
            extruder_quality = extruder.findContainer({"type": "quality_changes"})
            if not extruder_quality:
                Logger.log("w", "No extruder quality profile found, not writing quality for extruder %s to file!", extruder.getId())
                continue

            flat_extruder_quality = self._createFlattenedContainerInstance(extruder.getTop(), extruder_quality)

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
