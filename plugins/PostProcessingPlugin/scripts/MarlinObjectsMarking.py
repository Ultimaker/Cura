# Cura PostProcessingPlugin
# Author:   Kirill Shashlov
# Date:     October, 2019

# Licence: AGPLv3 or higher

from ..Script import Script
from UM.Application import Application
from UM.Logger import Logger

class MarlinObjectsMarking(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Mark different objects (meshes) with Marlin firmware rules",
            "key": "MarlinObjectsMarking",
            "metadata": {},
            "version": 2,
            "settings": {}
        }"""

    def execute(self, data):
        obj_dict = {}
        for layer in data:
            lay_idx = data.index(layer)
            layerCommandLines = layer.split("\n")
            for commandLine in layerCommandLines:
                if not commandLine.startswith(";"):
                    continue

                command_idx = layerCommandLines.index(commandLine)

                if commandLine.startswith(";TYPE:SKIRT") or \
                   commandLine.startswith(";MESH:NONMESH"):
                    layerCommandLines.insert(command_idx + 1, self.putValue("", M=486, S=-1))
                    continue

                if commandLine.startswith(";MESH:"):
                    obj_name = commandLine.split(":")[1]
                    obj_index = obj_dict.setdefault(obj_name, len(obj_dict.keys()))
                    layerCommandLines.insert(command_idx + 1, self.putValue("", M=486, S=obj_index))

            data[lay_idx] = "\n".join(layerCommandLines)
        return data