# Cura PostProcessingPlugin
# Author:   Amanda de Castilho
# Date:     August 28, 2018

# Description:  This plugin inserts a line at the start of each layer,
#               M117 displays the filename and layer height to the LCD
#               ** user must enter 'filename'
#               ** future update: include actual filename

from ..Script import Script

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
                    "label": "filename",
                    "description": "Enter filename",
                    "type": "str",
                    "default_value": "default"
                }
            }
        }"""
    
    def execute(self, data):
        name = self.getSettingValueByKey("name")
        lcd_text = "M117 " + name + " layer: "
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
