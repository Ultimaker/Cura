# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
# Created by Wayne Porter
# Modified 5/15/2023 - Greg Valiant (Greg Foresi)
#    Added insertion frequency
#    Adjusted for use with Relative Extrusion
#    Changed Retract to a boolean and when true use the regular Cura retract settings.
#    Use the regular Cura settings for Travel Speed and Speed_Z instead of asking.
#    Added code to check the E location to prevent retracts if the filament was already retracted.

from ..Script import Script
from UM.Application import Application

class TimeLapse(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Time Lapse Camera",
            "key": "TimeLapse",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "trigger_command":
                {
                    "label": "Camera Trigger Command",
                    "description": "G-code command used to trigger the camera.",
                    "type": "str",
                    "default_value": "M240"
                },
                "insert_frequency":
                {
                    "label": "How often (layers)",
                    "description": "Every so many layers (always starts at the first layer whether it's the model or a raft).",
                    "type": "enum",
                    "options": {
                        "every_layer": "Every Layer",
                        "every_2nd": "Every 2nd",
                        "every_3rd": "Every 3rd",
                        "every_5th": "Every 5th",
                        "every_10th": "Every 10th",
                        "every_25th": "Every 25th",
                        "every_50th": "Every 50th",
                        "every_100th": "Every 100th"},
                    "default_value": "every_layer"
                },
                "pause_length":
                {
                    "label": "Pause length",
                    "description": "How long to wait (in ms) after camera was triggered.",
                    "type": "int",
                    "default_value": 700,
                    "minimum_value": 0,
                    "unit": "ms"
                },
                "park_print_head":
                {
                    "label": "Park Print Head",
                    "description": "Park the print head out of the way.",
                    "type": "bool",
                    "default_value": true
                },
                "head_park_x":
                {
                    "label": "Park Print Head X",
                    "description": "What X location does the head move to for photo.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0,
                    "enabled": "park_print_head"
                },
                "head_park_y":
                {
                    "label": "Park Print Head Y",
                    "description": "What Y location does the head move to for photo.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0,
                    "enabled": "park_print_head"
                },
                "retract":
                {
                    "label": "Retract when required",
                    "description": "Retract if there isn't already a retraction.  If unchecked then there will be no retraction even if there is none in the gcode.",
                    "type": "bool",
                    "default_value": true
                },
                "zhop":
                {
                    "label": "Z-Hop Height When Parking",
                    "description": "The height to lift the nozzle off the print before parking.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 2.0,
                    "minimum_value": 0.0
                }
            }
        }"""

    def execute(self, data):
        mycura = Application.getInstance().getGlobalContainerStack()
        relative_extrusion = bool(mycura.getProperty("relative_extrusion", "value"))
        extruder = mycura.extruderList
        retract_speed = int(extruder[0].getProperty("retraction_speed", "value"))*60
        retract_dist = int(extruder[0].getProperty("retraction_amount", "value"))
        speed_z = int(extruder[0].getProperty("speed_z_hop", "value"))*60
        if relative_extrusion:
            rel_cmd = 83
        else:
            rel_cmd = 82
        trav_speed = int(extruder[0].getProperty("speed_travel", "value"))*60
        park_print_head = self.getSettingValueByKey("park_print_head")
        x_park = self.getSettingValueByKey("head_park_x")
        y_park = self.getSettingValueByKey("head_park_y")
        trigger_command = self.getSettingValueByKey("trigger_command")
        pause_length = self.getSettingValueByKey("pause_length")
        retract = bool(self.getSettingValueByKey("retract"))
        zhop = self.getSettingValueByKey("zhop")
        when_to_insert = self.getSettingValueByKey("insert_frequency")
        last_x = 0
        last_y = 0
        last_z = 0
        last_e = 0
        prev_e = 0
        is_retracted = False
        gcode_to_append = ""
        if park_print_head:
            gcode_to_append += self.putValue(G=1, F=trav_speed,
                                             X=x_park, Y=y_park) + " ;Park print head\n"
        gcode_to_append += self.putValue(M=400) + "         ;Wait for moves to finish\n"
        gcode_to_append += trigger_command + "         ;Snap Photo\n"
        gcode_to_append += self.putValue(G=4, P=pause_length) + "      ;Wait for camera\n"
        if when_to_insert == "every_layer":
            step_freq = 1
        if when_to_insert == "every_2nd":
            step_freq = 2
        if when_to_insert == "every_3rd":
            step_freq = 3
        if when_to_insert == "every_5th":
            step_freq = 5
        if when_to_insert == "every_10th":
            step_freq = 10
        if when_to_insert == "every_25th":
            step_freq = 25
        if when_to_insert == "every_50th":
            step_freq = 50
        if when_to_insert == "every_100th":
            step_freq = 100
        # Use the step_freq to index through the layers----------------------------------------
        for num in range(2,len(data)-1,step_freq):
            layer = data[num]
            try:                
                # Track X,Y,Z location.--------------------------------------------------------
                for line in layer.split("\n"):
                    if self.getValue(line, "G") in {0, 1}:
                        last_x = self.getValue(line, "X", last_x)
                        last_y = self.getValue(line, "Y", last_y)
                        last_z = self.getValue(line, "Z", last_z)
                #Track the E location so that if there is already a retraction we don't double dip.        
                        if rel_cmd == 82:
                            if " E" in line:
                                last_e = line.split("E")[1]
                                if float(last_e) < float(prev_e):
                                    is_retracted = True
                                else:
                                    is_retracted = False
                                prev_e = last_e
                        elif rel_cmd == 83:
                            if " E" in line:
                                last_e = line.split("E")[1]
                                if float(last_e) < 0:
                                    is_retracted = True
                                else:
                                    is_retracted = False
                                prev_e = last_e
                lines = layer.split("\n")
                # Insert the code----------------------------------------------------
                for line in lines:
                    if ";LAYER:" in line:
                        if retract and not is_retracted: # Retract unless already retracted
                            layer += self.putValue(";  TimeLapse Begin\n")
                            layer += self.putValue(M=83) + "          ;Extrude Relative\n"
                            layer += self.putValue(G=1, E=-retract_dist, F=retract_speed) + " ;Retract filament\n"
                        else:
                            layer += self.putValue(";  TimeLapse Begin\n")
                        if zhop != 0:
                            layer += self.putValue(G=1, Z=last_z+zhop, F=speed_z) + " ;Z-Hop\n"
                        layer += gcode_to_append
                        layer += self.putValue(G=0, F=trav_speed, X=last_x, Y=last_y) + " ;Restore position \n"
                        if zhop != 0:
                            layer += self.putValue(G=0, F=speed_z, Z=last_z) + "  ;Restore Z position \n"
                        if retract and not is_retracted:
                            layer += self.putValue(G=1, E=retract_dist, F=retract_speed) + "  ;Un-Retract filament\n"
                            layer += self.putValue(M=rel_cmd) + "          ;Extrude Mode\n"
                        layer += self.putValue(";  TimeLapse End\n")
                        data[num] = layer
                        break
            except:
                all
        return data
