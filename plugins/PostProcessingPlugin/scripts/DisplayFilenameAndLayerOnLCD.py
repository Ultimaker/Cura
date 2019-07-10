# Cura PostProcessingPlugin
# Author:   Amanda de Castilho
# Date:     August 28, 2018

# Description:  This plugin inserts a line at the start of each layer,
#               M117 - displays the filename and layer height to the LCD
#               Alternatively, user can override the filename to display alt text + layer height

from ..Script import Script
from UM.Application import Application

class DisplayFilenameAndLayerOnLCD(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Display filename and layer on LCD",
            "key": "DisplayFilenameAndLayerOnLCD",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "name":
                {
                    "label": "text to display:",
                    "description": "By default the current filename will be displayed on the LCD. Enter text here to override the filename and display something else.",
                    "type": "str",
                    "default_value": ""
                }
            }
        }"""
    
    def execute(self, data):
        if self.getSettingValueByKey("name") != "":
            name = self.getSettingValueByKey("name")
        else:
            name = Application.getInstance().getPrintInformation().jobName       
        lcd_text = "M117 " + name + " layer "
        i = 0
        for layer in data:
            display_text = lcd_text + str(i)
            layer_index = data.index(layer)
            lines = layer.split("\n")
            for line in lines:
                if line.startswith(";LAYER:"):
                    line_index = lines.index(line)
                    lines.insert(line_index + 1, display_text)
                    i += 1
            final_lines = "\n".join(lines)
            data[layer_index] = final_lines
            
        return data
