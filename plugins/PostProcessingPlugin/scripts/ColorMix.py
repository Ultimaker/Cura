# ColorMix script - 2-1 extruder color mix and blending
# This script is specific for the Geeetech A10M dual extruder but should work with other Marlin printers. 
# It runs with the PostProcessingPlugin which is released under the terms of the AGPLv3 or higher.
# This script is licensed under the Creative Commons - Attribution - Share Alike (CC BY-SA) terms

#Authors of the 2-1 ColorMix plug-in / script:
# Written by John Hryb - john.hryb.4@gmail.com

#history / change-log:
#V1.0.0 - Initial
#V1.1.0 - 
    # additions:
        #Object number - To select individual models or all when using "one at a time" print sequence
#V1.2.0
    # fixed layer heights Cura starts at 1 while G-code starts at 0
    # removed notes
    # changed Units of measurement to Units
#V1.2.1
    # Fixed mm bug when not in multiples of layer height
# Uses -
# M163 - Set Mix Factor 
# M164 - Save Mix - saves to T2 as a unique mix
    
import re #To perform the search and replace.
from ..Script import Script

class ColorMix(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name":"ColorMix 2-1 V1.2.1",
            "key":"ColorMix 2-1",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "units_of_measurement":
                {
                    "label": "Units",
                    "description": "Input value as mm or layer number.",
                    "type": "enum",
                    "options": {"mm":"mm","layer":"Layer"},
                    "default_value": "layer"
                },
                "object_number":
                {
                    "label": "Object Number",
                    "description": "Select model to apply to for print one at a time print sequence. 0 = everything",
                    "type": "int",
                    "default_value": 0,
                    "minimum_value": "0"
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
                    "minimum_value_warning": "start_height",
                    "enabled": "behavior == 'blend_value'" 
                },
                "mix_start":
                {
                    "label": "Start mix ratio",
                    "description": "First extruder percentage 0-100",
                    "type": "float",
                    "default_value": 100,
                    "minimum_value": "0",
                    "minimum_value_warning": "0",
                    "maximum_value_warning": "100"
                },
                "mix_finish":
                {
                    "label": "End mix ratio",
                    "description": "First extruder percentage 0-100 to finish blend",
                    "type": "float",
                    "default_value": 0,
                    "minimum_value": "0",
                    "minimum_value_warning": "0",
                    "maximum_value_warning": "100",
                    "enabled": "behavior == 'blend_value'"
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

        firstHeight = self.getSettingValueByKey("start_height")
        secondHeight = self.getSettingValueByKey("finish_height")
        firstMix = self.getSettingValueByKey("mix_start")
        secondMix = self.getSettingValueByKey("mix_finish")
        modelOfInterest = self.getSettingValueByKey("object_number")
        
        #get layer height
        layerHeight = 0
        for active_layer in data:
            lines = active_layer.split("\n")
            for line in lines:
                if ";Layer height: " in line:
                    layerHeight = self.getValue(line, ";Layer height: ", layerHeight)
                    break
            if layerHeight != 0:
                break
        
        #default layerHeight if not found
        if layerHeight == 0:
            layerHeight = .2
            
        #get layers to use
        startLayer = 0
        endLayer = 0
        if self.getSettingValueByKey("units_of_measurement") == "mm":
            startLayer = round(firstHeight / layerHeight)
            endLayer = round(secondHeight / layerHeight)
        else:  #layer height shifts down by one for g-code
            if firstHeight <= 0:
                firstHeight = 1
            if secondHeight <= 0:
                secondHeight = 1   
            startLayer = firstHeight - 1
            endLayer = secondHeight - 1
        #see if one-shot
        if self.getSettingValueByKey("behavior") == "fixed_value":
            endLayer = startLayer
            firstExtruderIncrements = 0
        else:  #blend
            firstExtruderIncrements = (secondMix - firstMix) / (endLayer - startLayer)
        firstExtruderValue = 0
        index = 0

        #start scanning
        layer = -1
        modelNumber = 0
        for active_layer in data:
            modified_gcode = ""
            lineIndex = 0
            lines = active_layer.split("\n")
            for line in lines:
                #dont leave blanks 
                if line != "":
                    modified_gcode += line + "\n"
                # find current layer
                if ";LAYER:" in line:
                    layer = self.getValue(line, ";LAYER:", layer)
                    #get model number by layer 0 repeats
                    if layer == 0:
                        modelNumber = modelNumber + 1
                    #search for layers to manipulate
                    if (layer >= startLayer) and (layer <= endLayer):
                        #make sure correct model is selected
                        if (modelOfInterest == 0) or (modelOfInterest == modelNumber):
                            #Delete old data if required
                            if lines[lineIndex + 4] == "T2":  
                                del lines[(lineIndex + 1):(lineIndex + 5)]
                            #add mixing commands
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