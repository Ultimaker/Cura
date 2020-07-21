# Created by Jakub Wietrzyk <jakub@wietrzyk.com> https://github.com/jaaaco
# Based on https://github.com/asmaurya/Temperature-Tower-Plugin-for-Cura-4.-

from typing import List

from ..Script import Script
from UM.Application import Application

class TemperatureTower(Script):
    def getSettingDataString(self):
        return """{
            "name": "Temperature Tower",
            "key": "TemperatureTower",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "change_at":
                {
                    "label": "Change Temp at",
                    "description": "Whether to decrease temp at layer or height interval",
                    "type": "enum",
                    "options": {"height": "Height", "layer": "Layer No."},
                    "default_value": "layer"
                },
                "height_inc":
                {
                    "label": "Height Interval",
                    "description": "At the increase of how many mm height does the temp decreases",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 5.0,
                    "minimum_value": 0,
                    "enabled": "change_at == 'height'"
                },
                "layer_inc": 
                {
                    "label": "Layer Interval",
                    "description": "At the increase of how many layers does the temp decreases",
                    "type": "int",
                    "value": 1,
                    "minimum_value": 0,
                    "minimum_value_warning": "1",
                    "enabled": "change_at == 'layer'"
                },
                "layer_start": 
                {
                    "label": "Start Layer",
                    "description": "From which layer the temp decrease has to be started",
                    "type": "int",
                    "value": 1,
                    "minimum_value": 0,
                    "minimum_value_warning": "1",
                    "enabled": "change_at == 'layer'"
                },
                "height_start": 
                {
                    "label": "Start Height (mm)",
                    "description": "From which height the temp decrease has to be started",
                    "type": "float",
                    "value": 0.2,
                    "unit": "mm",
                    "minimum_value": 0.2,
                    "minimum_value_warning": "1",
                    "enabled": "change_at == 'height'"
                },
                "temperature_start":
                {
                    "label": "Start Temperature",
                    "description": "Initial temperature",
                    "unit": "°C",
                    "type": "int",
                    "default_value": 200
                },
                "temperature_dec":
                {
                    "label": "Temperature Decrement Step",
                    "description": "Decrease temperature by this much with each increment",
                    "unit": "°C",
                    "type": "int",
                    "default_value": 5
                }
            }
        }"""

    def execute(self, data: List[str]):
        new_temperature = self.getSettingValueByKey("temperature_start") + self.getSettingValueByKey("temperature_dec")
        comment = "  ; Added by Temperature Tower Post Processing Plugin \n"
        layer_height = Application.getInstance().getGlobalContainerStack().getProperty("layer_height", "value")
        if self.getSettingValueByKey("change_at") == "layer":
            for layer in range(self.getSettingValueByKey("layer_start"), len(data)-2, self.getSettingValueByKey("layer_inc")):
                new_temperature -= self.getSettingValueByKey("temperature_dec")
                if new_temperature < 0:
                    new_temperature = 0
                data[layer] = "\nM104 S" + str(new_temperature) + comment + data[layer]
        else:
            for layer in range(int(self.getSettingValueByKey("height_start") / layer_height), len(data)-2, int(self.getSettingValueByKey("height_inc") / layer_height)):
                new_temperature -= self.getSettingValueByKey("temperature_dec")
                if new_temperature < 0:
                    new_temperature = 0
                data[layer] = "\nM104 S" + str(new_temperature) + comment + data[layer]
        return data
