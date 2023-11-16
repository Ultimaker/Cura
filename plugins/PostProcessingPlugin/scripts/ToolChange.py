# Copyright (c) 2023 Jody Pearson.
# Released under the terms of the LGPLv3 or higher.

from typing import List
from ..Script import Script

class ToolChange(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Tool Change",
            "key": "ToolChange",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "enabled":
                {
                    "label": "Enable",
                    "description": "Uncheck to temporarily disable this feature.",
                    "type": "bool",
                    "default_value": true
                },
                "layer_number":
                {
                    "label": "Layer",
                    "description": "At what layer should color change occur. This will be before the layer starts printing. Specify multiple color changes with a comma.",
                    "unit": "",
                    "type": "str",
                    "default_value": "1",
                    "enabled": "enabled"
                },
                "new_tool":
                {
                    "label": "New tool number",
                    "description": "The tool number of the new tool",
                    "type": "enum",
                    "options":
                    {
                        "1": "1",
                        "2": "2",
                        "3": "3",
                        "4": "4",
                        "5": "5"
                    },
                    "default_value": "1",
                    "enabled": "enabled"
                },
                "new_temperature":
                {
                    "label": "Temperature",
                    "description": "At what temperature should the new tool start to print?",
                    "unit": "degrees",
                    "type": "str",
                    "default_value": "200",
                    "enabled": "enabled"
                },
                "enable_before_macro":
                {
                    "label": "Enable G-code Before",
                    "description": "Use this to insert a custom G-code macro before the tool change happens",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enabled"
                },
                "before_macro":
                {
                    "label": "G-code Before",
                    "description": "Any custom G-code to run before the tool change happens, for example, M300 S1000 P10000 for a long beep.",
                    "unit": "",
                    "type": "str",
                    "default_value": "M300 S1000 P10000",
                    "enabled": "enabled and enable_before_macro"
                },
                "enable_after_macro":
                {
                    "label": "Enable G-code After",
                    "description": "Use this to insert a custom G-code macro after the tool change",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enabled"
                },
                "after_macro":
                {
                    "label": "G-code After",
                    "description": "Any custom G-code to run after the tool has been changed right before continuing the print, for example, you can add a sequence to purge tool and wipe the nozzle.",
                    "unit": "",
                    "type": "str",
                    "default_value": "M300 S440 P500",
                    "enabled": "enabled and enable_after_macro"
                }
            }
        }"""

    def execute(self, data: List[str]):
        """Inserts the tool change g-code at specific layer numbers.

        :param data: A list of layers of g-code.
        :return: A similar list, with tool change commands inserted.
        """
        enabled = self.getSettingValueByKey("enabled")
        layer_nums = self.getSettingValueByKey("layer_number")
        new_tool = self.getSettingValueByKey("new_tool")
        new_temperature = self.getSettingValueByKey("new_temperature")
        enable_before_macro = self.getSettingValueByKey("enable_before_macro")
        before_macro = self.getSettingValueByKey("before_macro")
        enable_after_macro = self.getSettingValueByKey("enable_after_macro")
        after_macro = self.getSettingValueByKey("after_macro")

        if not enabled:
            return data

        tool_change = ";BEGIN Tool Change plugin\n"

        if enable_before_macro:
            tool_change = tool_change + before_macro + "\n"
        tool_change = tool_change + (
            f"G60 ; save current position\n"
            f"G0 X-50 ; move tool up and away\n"
            f"M104 S0 ; set the temp of the original tool to zero degrees (no waiting)\n"
            f"T{new_tool} ; change to new tool from original\n"
            f"M104 S{new_temperature}\n"
            f"M109 S{new_temperature} ; set the temp of the new tool to {new_temperature} degrees (and wait until it gets there)\n"
            f"G92 E0 ; reset extruder to zero\n"
            f"G61 ; move new tool to saved position\n"
        )
        if enable_after_macro:
            tool_change = tool_change + after_macro + "\n"
        tool_change = tool_change + ";END Tool Change plugin\n"

        layer_targets = layer_nums.split(",")
        if len(layer_targets) > 0:
            for layer_num in layer_targets:
                try:
                    layer_num = int(layer_num.strip()) + 1 #Needs +1 because the 1st layer is reserved for start g-code.
                except ValueError: #Layer number is not an integer.
                    continue
                if 0 < layer_num < len(data):
                    data[layer_num] = tool_change + data[layer_num]

        return data
