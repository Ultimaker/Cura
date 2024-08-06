#------------------------------------------------------------------------------------------------------------------------------------
#
# Cura PostProcessing Script
# Author:   Ricardo Ortega Magaña
# Date:     August 06, 2024
#
# Description:  Modify M190 line
#               
#
#------------------------------------------------------------------------------------------------------------------------------------
#   
#   Version 1.2 08/06/2024 Continue heating bed after waiting.
#   Version 1.1 08/03/2024 Default percentage is now 80%
#   Version 1.0 01/03/2024 Change the M190 temperature to a percentage to start heating the nozzle
#   
#------------------------------------------------------------------------------------------------------------------------------------

from ..Script import Script
from UM.Logger import Logger
from UM.Application import Application

from enum import Enum

__version__ = '1.2'

class startHeatingAtPercentage(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "startHeatingAtPercentage",
            "key": "startHeatingAtPercentage",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "bedTempPercentage":
                {
                    "label": "Bed temperature percentage to start heating the nozzle",
                    "description": "What is the percentage of bed heating to start heating the nozzle.",
                    "type": "float",
                    "unit": "%",
                    "default_value": 80,
                    "minimum_value": "50",
                    "maximum_value": "100"
                }                     
            }
        }"""

    def execute(self, data):

        bedTempPercentage = float(self.getSettingValueByKey("bedTempPercentage")) 
        OnlyFirst=True
        for layer in data:
            layer_index = data.index(layer)
            lines = layer.split("\n")
            resLines=[]
            for line in lines:                  
               
                if ("M190" in line) and OnlyFirst:
                    temp=line.split("S")
                    if(len(temp)==2):
                        percTemp=int((float(temp[1])*bedTempPercentage)/100)
                        resLines.append(f"M190 S{percTemp}")
                        resLines.append(f"M140 S{temp[1]}")
                        OnlyFirst=False
                else:
                    resLines.append(line)
            result = "\n".join(resLines)
            data[layer_index] = result

        return data
