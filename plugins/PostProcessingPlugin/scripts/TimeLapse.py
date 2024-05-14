# Copyright (c) 2020 Ultimaker B.V.
# Created by Wayne Porter
# Re-write April 15, 2024 by GregValiant (Greg Foresi)
# Changes:
#    Added insertion frequency
#    Added support for Relative Extrusion mode
#    Added support for Firmware Retraction
#    Changed Retract to a boolean and when True use the regular Cura retract settings.
#    Use the regular Cura settings for Travel Speed and Speed_Z instead of asking.
#    Added code to prevent retracts when parking if the filament was already retracted.

from ..Script import Script
from UM.Application import Application

class TimeLapse(Script):

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
                    "description": "G-code command used to trigger the camera.  The command will be inserted at the ends of layers.",
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
                    "label": "Wait for Camera",
                    "description": "How long to wait (in ms) after the camera was triggered before returning to the print.",
                    "type": "int",
                    "default_value": 700,
                    "minimum_value": 0,
                    "unit": "ms  "
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
                    "description": "What X location does the head move to for the photo.",
                    "unit": "mm  ",
                    "type": "float",
                    "default_value": 0,
                    "enabled": "park_print_head"
                },
                "head_park_y":
                {
                    "label": "Park Print Head Y",
                    "description": "What Y location does the head move to for the photo.",
                    "unit": "mm  ",
                    "type": "float",
                    "default_value": 0,
                    "enabled": "park_print_head"
                },
                "retract":
                {
                    "label": "Retract when required",
                    "description": "Retract if there is not already a retraction.  If unchecked then there will be no retraction even if there is none in the gcode.  If retractions are not enabled in Cura there won't be a retraction regardless of this setting.",
                    "type": "bool",
                    "default_value": true
                },
                "zhop":
                {
                    "label": "Z-Hop Height When Parking",
                    "description": "The height to lift the nozzle off the print before parking.",
                    "unit": "mm  ",
                    "type": "float",
                    "default_value": 2.0,
                    "minimum_value": 0.0
                },
                "ensure_final_image":
                {
                    "label": "Ensure Final Image",
                    "description": "Depending on how the layer numbers work out with the 'How Often' frequency there might not be an image taken at the end of the last layer.  This will ensure that one is taken.  There is no parking because the 'End Gcode' occurs immediately after.",
                    "type": "bool",
                    "default_value": false
                }
            }
        }"""

    def execute(self, data):
        # Get the settings and initialize some variables
        mycura = Application.getInstance().getGlobalContainerStack()
        relative_extrusion = bool(mycura.getProperty("relative_extrusion", "value"))
        extruder = mycura.extruderList
        retract_speed = int(extruder[0].getProperty("retraction_speed", "value"))*60
        retract_dist = int(extruder[0].getProperty("retraction_amount", "value"))
        retract_enabled = bool(extruder[0].getProperty("retraction_enable", "value"))        
        firmware_retraction = bool(mycura.getProperty("machine_firmware_retract", "value"))
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
        ensure_final_image = bool(self.getSettingValueByKey("ensure_final_image"))
        when_to_insert = self.getSettingValueByKey("insert_frequency")
        last_x = 0
        last_y = 0
        last_z = 0
        last_e = 0
        prev_e = 0
        is_retracted = False
        gcode_to_append = ""
        if park_print_head:
            gcode_to_append += f"G1 F{trav_speed} X{x_park} Y{y_park} ;Park print head\n"
        gcode_to_append += "M400 ;Wait for moves to finish\n"
        gcode_to_append += trigger_command + " ;Snap the Image\n"
        gcode_to_append += f"G4 P{pause_length} ;Wait for camera\n"
        match when_to_insert:
            case "every_layer":
                step_freq = 1
            case "every_2nd":
                step_freq = 2
            case "every_3rd":
                step_freq = 3
            case "every_5th":
                step_freq = 5
            case "every_10th":
                step_freq = 10
            case "every_25th":
                step_freq = 25
            case "every_50th":
                step_freq = 50
            case "every_100th":
                step_freq = 100
            case _:
                step_freq = 1
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
                    if self.getValue(line, "G") in {10, 11}:
                        if line.startswith("G10"):
                            is_retracted = True
                        if line.startswith("G11"):
                            is_retracted = False
                # Insert the code----------------------------------------------------
                lines = layer.split("\n")
                camera_code = ""
                for line in lines:
                    if ";LAYER:" in line:
                        # Retract unless already retracted
                        if retract and not is_retracted and retract_enabled:
                            camera_code += ";TYPE:CUSTOM-----------------TimeLapse Begin\n"
                            camera_code += "M83 ;Extrude Relative\n"
                            if not firmware_retraction:
                                camera_code += f"G1 F{retract_speed} E-{retract_dist} ;Retract filament\n"
                            else:
                                camera_code += "G10 ;Retract filament\n"
                        else:
                            camera_code += ";TYPE:CUSTOM-----------------TimeLapse Begin\n"
                        if zhop != 0:
                            camera_code += f"G1 F{speed_z} Z{last_z + zhop} ;Z-Hop\n"
                        camera_code += gcode_to_append
                        camera_code += self.putValue(G=0, F=trav_speed, X=last_x, Y=last_y) + " ;Restore XY position \n"
                        if zhop != 0:
                            camera_code += self.putValue(G=0, F=speed_z, Z=last_z) + "  ;Restore Z position \n"
                        if retract and not is_retracted and retract_enabled:
                            if not firmware_retraction:
                                camera_code += self.putValue(G=1, E=retract_dist, F=retract_speed) + "  ;Un-Retract filament\n"
                            else:
                                camera_code += "G11  ;Un-Retract filament\n"
                            camera_code += self.putValue(M=rel_cmd) + "          ;Extrude Mode\n"
                        camera_code += f";{'-' * 28}TimeLapse End"
                        # Format the camera code to be inserted
                        temp_lines = camera_code.split("\n")
                        for temp_index, temp_line in enumerate(temp_lines):
                            if ";" in temp_line and not temp_line.startswith(";"):
                                temp_lines[temp_index] = temp_line.replace(temp_line.split(";")[0], temp_line.split(";")[0] + str(" " * (29 - len(temp_line.split(";")[0]))),1)
                        temp_lines = "\n".join(temp_lines)
                        lines.insert(len(lines) - 2, temp_lines)
                        data[num] = "\n".join(lines)
                        break
            except:
                pass
        # Take a final image if there was no camera shot at the end of the last layer.
        if "TimeLapse Begin" not in data[len(data) - (3 if retract_enabled else 2)] and ensure_final_image:
            data[len(data)-1] = "M400    ; Wait for all moves to finish\n" + trigger_command + "    ;Snap the final Image\n" + f"G4 P{pause_length} ;Wait for camera\n" + data[len(data)-1]
        return data
