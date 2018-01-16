# Copyright (c) 2015 Jaime van Kessel, Ultimaker B.V.
# The PostProcessingPlugin is released under the terms of the AGPLv3 or higher.
from ..Script import Script

class ExampleScript(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name":"Example script",
            "key": "ExampleScript",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "test":
                {
                    "label": "Test",
                    "description": "None",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0.5,
                    "minimum_value": "0",
                    "minimum_value_warning": "0.1",
                    "maximum_value_warning": "1"
                },
                "derp":
                {
                    "label": "zomg",
                    "description": "afgasgfgasfgasf",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0.5,
                    "minimum_value": "0",
                    "minimum_value_warning": "0.1",
                    "maximum_value_warning": "1"
                }
            }
        }"""

    def execute(self, data):
        return data