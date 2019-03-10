# ColorMix script - 2-1 extruder color mix and blending
# This script is specific for the Geeetech A10M dual extruder but should work with other Marlin printers. 
# It runs with the PostProcessingPlugin which is released under the terms of the AGPLv3 or higher.
# This script is licensed under the Creative Commons - Attribution - Share Alike (CC BY-SA) terms

#Authors of the 2-1 ColorMix plug-in / script:
# Written by John Hryb - john.hryb.4@gmail.com

##history / change-log:
##V1.0.0

## Uses -
## M163 - Set Mix Factor 
## M164 - Save Mix - saves to T3 as a unique mix

import re #To perform the search and replace. 
from ..Script import Script

class ColorMix(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name":"ColorMix 2-1",
            "key":"ColorMix 2-1",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "measurement_units":
                {
                    "label": "Units of measurement",
                    "description": "Input value as mm or layer number.",
                    "type": "enum",
                    "options": {"mm":"mm","layer":"Layer"},
                    "default_value": "layer"
                },
                "start_height":
                {
                    "label": "Start Height",
                    "description": "Value to start at (mm or layer)",
                    "type": "float",
                    "default_value": 0,
                    "minimum_value": "0"
                },
                "behavior":
                {
                    "label": "Fixed or blend",
                    "description": "Select Fixed (set new mixture) or Blend mode (dynamic mix)",
                    "type": "enum",
                    "options": {"fixed_value":"Fixed","blend_value":"Blend"},
                    "default_value": "fixed_value"
                },
                "finish_height":
                {
                    "label": "Finish Height",
                    "description": "Value to stop at (mm or layer)",
                    "type": "float",
                    "default_value": 0,
                    "minimum_value": "0",
                    "minimum_value_warning": "0.1",
                    "enabled": "c_behavior == 'blend_value'" 
                },
                "mix_start_ratio":
                {
                    "label": "Start mix ratio",
                    "description": "First extruder percentage 0-100",
                    "type": "float",
                    "default_value": 100,
                    "minimum_value": "0",
                    "minimum_value_warning": "0",
                    "maximum_value_warning": "100"
                },
                "mix_finish_ratio":
                {
                    "label": "End mix ratio",
                    "description": "First extruder percentage 0-100 to finish blend",
                    "type": "float",
                    "default_value": 0,
                    "minimum_value": "0",
                    "minimum_value_warning": "0",
                    "maximum_value_warning": "100",
                    "enabled": "c_behavior == 'blend_value'"
                },
                "notes":
                {
                    "label": "Notes",
                    "description": "A spot to put a note",
                    "type": "str",
                    "default_value": ""
                }
            }
        }"""
    def getValue(self, line, key, default = None): #replace default getvalue due to comment-reading feature
        if not key in line or (";" in line and line.find(key) > line.find(";") and
                                   not ";ChangeAtZ" in key and not ";LAYER:" in key):
            return default
        subPart = line[line.find(key) + len(key):] #allows for string lengths larger than 1
        if ";ChangeAtZ" in key:
            m = re.search("^[0-4]", subPart)
        elif ";LAYER:" in key:
            m = re.search("^[+-]?[0-9]*", subPart)
        else:
            #the minus at the beginning allows for negative values, e.g. for delta printers
            m = re.search("^[-]?[0-9]*\.?[0-9]*", subPart)
        if m == None:
            return default
        try:
            return float(m.group(0))
        except:
            return default

    def execute(self, data):
        #get user variables
        firstHeight = 0.0
        secondHeight = 0.0
        firstMix = 0.0
        SecondMix = 0.0

        firstHeight = self.getSettingValueByKey("start_height")
        secondHeight = self.getSettingValueByKey("finish_height")
        firstMix = self.getSettingValueByKey("mix_start_ratio")
        SecondMix = self.getSettingValueByKey("mix_finish_ratio")

        #locals
        layer = 0

        #get layer height
        layerHeight = .2
        for active_layer in data:
            lines = active_layer.split("\n")
            for line in lines:
                if ";Layer height: " in line:
                    layerHeight = self.getValue(line, ";Layer height: ", layerHeight)
                    break
        #get layers to use
        startLayer = 0
        endLayer = 0
        if self.getSettingValueByKey("measurement_units") == "mm":
            if firstHeight == 0:
                startLayer = 0
            else:
                startLayer = firstHeight / layerHeight
            if secondHeight == 0:
                endLayer = 0
            else:
                endLayer = secondHeight / layerHeight
        else:  #layer height
            startLayer = firstHeight
            endLayer = secondHeight
        #see if one-shot
        if self.getSettingValueByKey("behavior") == "fixed_value":
            endLayer = startLayer
            firstExtruderIncrements = 0
        else:  #blend
            firstExtruderIncrements = (SecondMix - firstMix) / (endLayer - startLayer)
        firstExtruderValue = 0
        index = 0
        #start scanning
        for active_layer in data:
            modified_gcode = ""
            lineIndex = 0;
            lines = active_layer.split("\n")
            for line in lines:
                #dont leave blanks 
                if line != "":
                    modified_gcode += line + "\n"
                # find current layer
                if ";LAYER:" in line:
                    layer = self.getValue(line, ";LAYER:", layer)
                    if (layer >= startLayer) and (layer <= endLayer):  #find layers of interest
                        if lines[lineIndex + 4] == "T2":  #check if needing to delete old data
                            del lines[(lineIndex + 1):(lineIndex + 5)] 
                        firstExtruderValue = int(((layer - startLayer) * firstExtruderIncrements) + firstMix)
                        if firstExtruderValue == 100:
                            modified_gcode += "M163 S0 P1\n"
                            modified_gcode += "M163 S1 P0\n"
                        elif firstExtruderValue == 0:
                            modified_gcode += "M163 S0 P0\n"
                            modified_gcode += "M163 S1 P1\n"
                        else:
                            modified_gcode += "M163 S0 P0.{:02d}\n".format(firstExtruderValue)
                            modified_gcode += "M163 S1 P0.{:02d}\n".format(100 - firstExtruderValue)
                        modified_gcode += "M164 S2\n"
                        modified_gcode += "T2\n"
                lineIndex += 1  #for deleting index
            data[index] = modified_gcode
            index += 1
        return data
