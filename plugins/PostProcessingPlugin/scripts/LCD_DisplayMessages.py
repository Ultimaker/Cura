# Copyright (c) 2019 Chris Simon
# The LCD_DisplayMessages postprocessing script is released under the terms of the AGPLv3 or higher.

from ..Script import Script
from UM.Logger import Logger

##  Performs a search-and-replace on all g-code.
#
#   Due to technical limitations, the search can't cross the border between
#   layers.
class LCD_DisplayMessages(Script):
    _search_layer_count_str = ";LAYER_COUNT:"
    _search_layer_str = ";LAYER:"

    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "LCD Display Messages",
            "key": "LCD_DisplayMessages",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "layer":
                {
                    "label": "Print layer height",
                    "description": "This will print the layer height on layer change including the totalnumber of layers.",
                    "type": "bool",
                    "default_value": true
                },
                "percentage":
                {
                    "label": "Print percentage",
                    "description": "This will print the percentage of the print job based on the number of lines in the gcode. NOT IMPLEMENTED YET!!",
                    "type": "bool",
                    "default_value": false
                }
			}
        }"""

    def execute(self, data):
        if self.getSettingValueByKey("layer"):
            for layer in data:
                lines = layer.split("\n")
                for line in lines:
                    if line.startswith(self._search_layer_count_str):
                        layer_count = line[len(self._search_layer_count_str):]
                        Logger.log("d", "Layer Count: " + layer_count)
                        break
            for layer in data:
                layer_index = data.index(layer)
                lines = layer.split("\n")
                for line in lines:
                    if line.startswith(self._search_layer_str):
                        current_layer_number = line[len(self._search_layer_str):]
                        line_index = lines.index(line)
                        lines.insert(line_index + 1, "M117 Printing layer " + current_layer_number + " of " + layer_count)
                final_lines = "\n".join(lines)
                data[layer_index] = final_lines

        return data