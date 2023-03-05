# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
# Created by Wayne Porter

from ..Script import Script

class InsertAtLayerChange(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Insert at layer change",
            "key": "InsertAtLayerChange",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "insert_location":
                {
                    "label": "When to insert",
                    "description": "Whether to insert code before or after layer change.",
                    "type": "enum",
                    "options": {"before": "Before", "after": "After"},
                    "default_value": "before"
                },
                "gcode_to_add":
                {
                    "label": "G-code to insert",
                    "description": "G-code to add before or after layer change.",
                    "type": "str",
                    "default_value": ""
                },
                "skip_layers":
                {
                    "label": "Skip layers",
                    "description": "Number of layers to skip between insertions (0 for every layer).",
                    "type": "int",
                    "default_value": 0,
                    "minimum_value": 0
                }
            }
        }"""

    def execute(self, data):
        gcode_to_add = self.getSettingValueByKey("gcode_to_add") + "\n"
        skip_layers = self.getSettingValueByKey("skip_layers")
        count = 0
        for layer in data:
            # Check that a layer is being printed
            lines = layer.split("\n")
            for line in lines:
                if ";LAYER:" in line:
                    index = data.index(layer)
                    if count == 0:
                        if self.getSettingValueByKey("insert_location") == "before":
                            layer = gcode_to_add + layer
                        else:
                            layer = layer + gcode_to_add

                        data[index] = layer

                    count = (count + 1) % (skip_layers + 1)
                    break
        return data
