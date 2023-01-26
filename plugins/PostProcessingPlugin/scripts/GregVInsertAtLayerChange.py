# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
# Created by Wayne Porter.
# altered January of 2023 by GregValiant

from ..Script import Script

class InsertAtLayerChange(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Insert at layer change",
            "key": "InsertAtLayerChange",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "insert_location":
                {
                    "label": "When to insert",
                    "description": "Whether to insert code at the beginning or end of a layer.",
                    "type": "enum",
                    "options": {
                        "before": "Beginning",
                        "after": "End"},
                    "default_value": "before"
                },
                "insert_frequency":
                {
                    "label": "How often to insert",
                    "description": "Every so many layers starting with the Start Layer.",
                    "type": "enum",
                    "options": {
                        "once_only": "One insertion only",
                        "every_layer": "Every Layer",
                        "every_second": "Every 2nd",
                        "every_third": "Every 3rd",
                        "every_fifth": "Every 5th",
                        "every_tenth": "Every 10th",
                        "every_XXV": "Every 25th",
                        "every_L": "Every 50th",
                        "every_C": "Every 100th"},
                    "default_value": "every_layer"
                },
                "start_layer":
                {
                    "label": "Starting Layer",
                    "description": "Layer to start the insertion at.",
                    "type": "int",
                    "default_value": 0,
                    "minimum_value": 0,
                    "enabled": "insert_frequency != 'once_only'"
                },
                "end_layer_enabled":
                {
                    "label": "Enable End Layer",
                    "description": "Check to use an ending layer for the insertion.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "insert_frequency != 'once_only'"
                },
                "end_layer":
                {
                    "label": "Ending Layer",
                    "description": "Layer to end the insertion at. Enter 'End' for entire file (or disable this setting).",
                    "type": "str",
                    "default_value": "End",
                    "enabled": "end_layer_enabled and insert_frequency != 'once_only'"
                },
                "single_end_layer":
                {
                    "label": "Layer # for Single Insertion",
                    "description": "Layer for a single insertion of the Gcode.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "insert_frequency == 'once_only'"
                },
                "gcode_to_add":
                {
                    "label": "G-code to insert.",
                    "description": "G-code to add before or after layer change. Use a comma to delimit multi-line commands. EX: G28 X Y,M220 S100,M117 HELL0.  Note that all commands will be converted to upper-case.",
                    "type": "str",
                    "default_value": ""
                }
            }
        }"""

    def execute(self, data):
        mycode = self.getSettingValueByKey("gcode_to_add").upper()
        the_start_layer = self.getSettingValueByKey("start_layer")
        the_end_layer = self.getSettingValueByKey("end_layer")
        the_end_is_enabled = self.getSettingValueByKey("end_layer_enabled")
        when_to_insert = self.getSettingValueByKey("insert_frequency")
        start_here = False
        real_num = 0
        
        if the_end_layer == "End" or not the_end_is_enabled:
            the_end_layer = "9999999999"
        
        if "," in mycode:
            gc = mycode.split(",")
            gcode_to_add = ""
            for g_code in gc:
                gcode_to_add += g_code + "\n"
        
        else:
            gcode_to_add = mycode + "\n"
            
        if when_to_insert == "every_layer":
            freq = 1
        
        if when_to_insert == "every_second":
            freq = 2
            
        if when_to_insert == "every_third":
            freq = 3
            
        if when_to_insert == "every_fifth":
            freq = 5
            
        if when_to_insert == "every_tenth":
            freq = 10 
            
        if when_to_insert == "every_XXV":
            freq = 25
            
        if when_to_insert == "every_L":
            freq = 50
            
        if when_to_insert == "every_C":
            freq = 100
            
        if when_to_insert == "once_only":
            the_search_layer = self.getSettingValueByKey("single_end_layer")
        
        index = 0
        if when_to_insert == "once_only":
            for layer in data:
                lines = layer.split("\n")
                for line in lines:
                    if ";LAYER:" in line:
                        layer_number = int(line.split(":")[1])
                        if layer_number == int(the_search_layer):
                            index = data.index(layer)
                            if self.getSettingValueByKey("insert_location") == "before":
                                layer = gcode_to_add + layer
                            else:
                                layer = layer + gcode_to_add

                            data[index] = layer
                            break    

        if when_to_insert != "once_only":
            for layer in data:
                lines = layer.split("\n")                
                for line in lines:
                    if ";LAYER:" in line:
                        layer_number = int(line.split(":")[1])
                        if layer_number >= int(the_start_layer) and layer_number <= int(the_end_layer):
                            index = data.index(layer)
                            real_num = layer_number - int(the_start_layer)
                            if int(real_num / freq) - (real_num / freq) == 0:
                                if self.getSettingValueByKey("insert_location") == "before":
                                    layer = gcode_to_add + layer
                                else:
                                    layer = layer + gcode_to_add
                                        
                                data[index] = layer
                                break
        
        return data
