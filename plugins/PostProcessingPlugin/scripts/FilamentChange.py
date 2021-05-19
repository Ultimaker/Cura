# Copyright (c) 2019 Ultimaker B.V.
# The PostProcessingPlugin is released under the terms of the AGPLv3 or higher.

from typing import List
from ..Script import Script

class FilamentChange(Script):

    _layer_keyword = ";LAYER:"

    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name":"Filament Change",
            "key": "FilamentChange",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "layer_number":
                {
                    "label": "Layer",
                    "description": "At what layer should color change occur. This will be before the layer starts printing. Specify multiple color changes with a comma.",
                    "unit": "",
                    "type": "str",
                    "default_value": "1"
                },

                "initial_retract":
                {
                    "label": "Initial Retraction",
                    "description": "Initial filament retraction distance. The filament will be retracted with this amount before moving the nozzle away from the ongoing print.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 30.0
                },
                "later_retract":
                {
                    "label": "Later Retraction Distance",
                    "description": "Later filament retraction distance for removal. The filament will be retracted all the way out of the printer so that you can change the filament.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 300.0
                },
                "x_position":
                {
                    "label": "X Position",
                    "description": "Extruder X position. The print head will move here for filament change.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0
                },
                "y_position":
                {
                    "label": "Y Position",
                    "description": "Extruder Y position. The print head will move here for filament change.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0
                },
                "z_position":
                {
                    "label": "Z Position (relative)",
                    "description": "Extruder relative Z position. Move the print head up for filament change.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0,
                    "minimum_value": 0
                }
            }
        }"""

    def execute(self, data: List[str]):
        """Inserts the filament change g-code at specific layer numbers.

        :param data: A list of layers of g-code.
        :return: A similar list, with filament change commands inserted.
        """
        layer_nums = self.getSettingValueByKey("layer_number")
        initial_retract = self.getSettingValueByKey("initial_retract")
        later_retract = self.getSettingValueByKey("later_retract")
        x_pos = self.getSettingValueByKey("x_position")
        y_pos = self.getSettingValueByKey("y_position")
        z_pos = self.getSettingValueByKey("z_position")

        color_change = "M600"

        if initial_retract is not None and initial_retract > 0.:
            color_change = color_change + (" E%.2f" % initial_retract)

        if later_retract is not None and later_retract > 0.:
            color_change = color_change + (" L%.2f" % later_retract)

        if x_pos is not None:
            color_change = color_change + (" X%.2f" % x_pos)

        if y_pos is not None:
            color_change = color_change + (" Y%.2f" % y_pos)

        if z_pos is not None and z_pos > 0.:
            color_change = color_change + (" Z%.2f" % z_pos)

        color_change = color_change + " ; Generated by FilamentChange plugin\n"

        layer_targets = layer_nums.split(",")
        if len(layer_targets) > 0:
            for layer_num in layer_targets:
                try:
                    layer_num = int(layer_num.strip()) + 1 #Needs +1 because the 1st layer is reserved for start g-code.
                except ValueError: #Layer number is not an integer.
                    continue
                if 0 < layer_num < len(data):
                    data[layer_num] = color_change + data[layer_num]

        return data
