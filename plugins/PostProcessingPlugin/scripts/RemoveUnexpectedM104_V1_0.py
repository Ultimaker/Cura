# Color switching Tower Genaration
# This script is specific for the ZONESTAR M3 and M4 3d printer 
# It runs with the PostProcessingPlugin which is released under the terms of the AGPLv3 or higher.
# This script is licensed under the Creative Commons - Attribution - Share Alike (CC BY-SA) terms

# Authors of the Color switching Tower Genaration plug-in / script:
# Written by Hally.Zhong - hally@zonestar3d.com

#history / change-log:
#V1.0.1 - Initial

import re
from ..Script import Script

class RemoveUnexpectedM104_V1_0(Script):
    def __init__(self):
        super().__init__()
        
    def getSettingDataString(self):
        return """{
            "name": "Remove Unexpected M104M109 V1.0",
            "key": "RemoveUnexpectedM104_V1_0",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "remove_M104":
                {
                    "label": "Remove Unexpected M104",
                    "description": "Remove redundant temperature setting instructions",
                    "type": "bool",
                    "default_value": true
                }
            }
        }"""
        
    def execute(self, data):
    		#logo_file = open(output.gcode, "w+")
        #logo_file.write(";;; This file is created by ZONESTAR Color Switch Tower Genaration V1.0.1b\n")
        #logo_file.write(";;; Website: https://zonestar3d.com\n")
        #logo_file.write(";\n")
        
        bFindM109 = 0
        bFindM104 = 0
        
        oldlayer = 0
        curlayer = -1
        totallayers = 99999
      
        index = 0;
        for layer in data:
            lines = layer.split("\n")
            for line in lines:
                line = line.strip()                
                if len(line) == 0:
                    continue
                    
                #logo_file.write(line+"\n")
                if ";Layer height:" in line:
                    substr = line[line.find(";Layer height:") + len(";Layer height:"):]
                    layerheight = round(float(substr),2)
                    addtion_gcode = ";Layer height={:.2f}\n".format(layerheight)
                    data[index] += addtion_gcode
                    #logo_file.write(";got total_layers = {:d}\n".format(totallayers))
                    continue
                    
                # find total layers
                if ";LAYER_COUNT:" in line:
                    substr = line[line.find(";LAYER_COUNT:") + len(";LAYER_COUNT:"):]
                    totallayers = int(substr)
                    #logo_file.write(";got total_layers = {:d}\n".format(totallayers))
                    continue
                #   
                #M109?
                #set flag when find the first M109, and remove others M109
                if line.startswith("M") and "M109" in line:
                    if bFindM109 == 1 and totallayers - curlayer > 1:
                       #not the first M109 command
                       if self.getSettingValueByKey("remove_M104"):
                           #remove this line
                           data[index] = ";removed by script " + line + "\n"
                           #logo_file.write(";remove a M109\n")
                    bFindM109 = 1
                    continue
                    
                #M104?
                #set flag when find the first M104, and remove others M104
                if line.startswith("M") and "M104" in line and (totallayers - curlayer > 1):
                    if bFindM104 == 1 or bFindM109 == 1:
                        #not the first M104 command                        
                        if self.getSettingValueByKey("remove_M104"):
                            #remove this line
                            data[index] = ";removed by script " + line+ "\n"
                            #logo_file.write(";remove a M104\n")
                    bFindM104 = 1
                    continue      
            #for line
            index += 1
        #for layer
        #logo_file.close()
        return data
