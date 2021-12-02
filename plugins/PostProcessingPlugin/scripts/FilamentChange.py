# Copyright (c) 2021 Ultimaker B.V.
# The PostProcessingPlugin is released under the terms of the AGPLv3 or higher.

# Modification 06.09.2020
# add checkbox, now you can choose and use configuration from the firmware itself.

from typing import List
from ..Script import Script

from UM.Application import Application #To get the current printer's settings.

class FilamentChange(Script):

    _layer_keyword = ";LAYER:"

    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Filament Change",
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
                "firmware_config":
                {
                    "label": "Use Firmware Configuration",
                    "description": "Use the settings in your firmware, or customise the parameters of the filament change here.",
                    "type": "bool",
                    "default_value": false
                },
                "initial_retract":
                {
                    "label": "Initial Retraction",
                    "description": "Initial filament retraction distance. The filament will be retracted with this amount before moving the nozzle away from the ongoing print.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 30.0,
                    "enabled": "not firmware_config"
                },
                "later_retract":
                {
                    "label": "Later Retraction Distance",
                    "description": "Later filament retraction distance for removal. The filament will be retracted all the way out of the printer so that you can change the filament.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 300.0,
                    "enabled": "not firmware_config"
                },
                "x_position":
                {
                    "label": "X Position",
                    "description": "Extruder X position. The print head will move here for filament change.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0,
                    "enabled": "not firmware_config"
                },
                "y_position":
                {
                    "label": "Y Position",
                    "description": "Extruder Y position. The print head will move here for filament change.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0,
                    "enabled": "not firmware_config"
                },
                "z_position":
                {
                    "label": "Z Position (relative)",
                    "description": "Extruder relative Z position. Move the print head up for filament change.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0,
                    "minimum_value": 0
                },
                "retract_method":
                {
                    "label": "Retract method",
                    "description": "The gcode variant to use for retract.",
                    "type": "enum",
                    "options": {"U": "Marlin (M600 U)", "L": "Reprap (M600 L)"},
                    "default_value": "U",
                    "value": "\\\"L\\\" if machine_gcode_flavor==\\\"RepRap (RepRap)\\\" else \\\"U\\\"",
                    "enabled": "not firmware_config"
                },                    
                "machine_gcode_flavor":
                {
                    "label": "G-code flavor",
                    "description": "The type of g-code to be generated. This setting is controlled by the script and will not be visible.",
                    "type": "enum",
                    "options":
                    {
                        "RepRap (Marlin/Sprinter)": "Marlin",
                        "RepRap (Volumetric)": "Marlin (Volumetric)",
                        "RepRap (RepRap)": "RepRap",
                        "UltiGCode": "Ultimaker 2",
                        "Griffin": "Griffin",
                        "Makerbot": "Makerbot",
                        "BFB": "Bits from Bytes",
                        "MACH3": "Mach3",
                        "Repetier": "Repetier"
                    },
                    "default_value": "RepRap (Marlin/Sprinter)",
                    "enabled": "false"
                }
            }
        }"""

    ##  Copy machine name and gcode flavor from global stack so we can use their value in the script stack
    def initialize(self) -> None:
        super().initialize()

        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack is None or self._instance is None:
            return

        for key in ["machine_gcode_flavor"]:
            self._instance.setProperty(key, "value", global_container_stack.getProperty(key, "value"))

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
        firmware_config = self.getSettingValueByKey("firmware_config")

        color_change = "M600"

        if not firmware_config:
            if initial_retract is not None and initial_retract > 0.:
                color_change = color_change + (" E%.2f" % initial_retract)

            if later_retract is not None and later_retract > 0.:
                # Reprap uses 'L': https://reprap.org/wiki/G-code#M600:_Filament_change_pause
                # Marlin uses 'U' https://marlinfw.org/docs/gcode/M600.html
                retract_method = self.getSettingValueByKey("retract_method")
                color_change = color_change + (" %s%.2f" % (retract_method, later_retract))

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
