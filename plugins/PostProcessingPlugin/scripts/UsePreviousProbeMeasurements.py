# Cura PostProcessingPlugin
# Author:   Amanda de Castilho
# Date:     January 5,2019

# Description:  This plugin overrides probing command and inserts code to ensure
#               previous probe measurements are loaded and bed leveling enabled
#               (searches for G29 and replaces it with M501 & M420 S1)
#               *** Assumes G29 is in the start code, will do nothing if it isn't ***

from ..Script import Script

class UsePreviousProbeMeasurements(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Use Previous Probe Measurements",
            "key": "UsePreviousProbeMeasurements",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "use_previous_measurements":
                {
                    "label": "Use last measurement?",
                    "description": "Selecting this will remove the G29 probing command and instead ensure previous measurements are loaded and enabled",
                    "type": "bool",
                    "default_value": false
                }
            }
        }"""
    
    def execute(self, data):
        text = "M501 ;load bed level data\nM420 S1 ;enable bed leveling"
        if self.getSettingValueByKey("use_previous_measurements"):
            for layer in data:
                layer_index = data.index(layer)
                lines = layer.split("\n")
                for line in lines:
                    if line.startswith("G29"):
                        line_index = lines.index(line)
                        lines[line_index] = text
                final_lines = "\n".join(lines)
                data[layer_index] = final_lines
        return data
