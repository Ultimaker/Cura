# Copyright (c) 2023 UltiMaker
#  Designed by GregValiant (Greg Foresi) 6-1-2023
#  Add temperature changes and/or Park and Wait for Bridges.
#  Adjusts the total print ";TIME:" and layer ";TIME_ELAPSED:" if M109 is used.

from ..Script import Script
import re
from UM.Application import Application
from UM.Message import Message
from typing import List, Tuple

class BridgeTemperatureAdjustment(Script):
    def __init__(self) -> None:
        super().__init__()

    def getSettingDataString(self) -> str:
        return """{
            "name": "Bridge Temperature Adjustment",
            "key": "BridgeTemperatureAdjustment",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "ignore_bridge_walls":
                {
                    "label": "Ignore Bridge Walls",
                    "description": "Most bridge walls are a single gcode line.  Waiting at each can greatly increased print time.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                },
                "bridge_temp_cmd":
                {
                    "label": "Bridge Temperature Cmd",
                    "description": "'M104 S' will allow the print to continue immediately.  'M109 R'' will park the print head and wait for the temperature to either rise or fall to the new set point and then resume the print.",
                    "type": "enum",
                    "options": {
                        "m109_cmd": "M109 R",
                        "m104_cmd": "M104 S"},
                    "default_value": "m109_cmd"
                },
                "bridge_temperature":
                {
                    "label": "Bridge Temperature",
                    "description": "The temperature you want the bridges to print at.",
                    "unit": "°C",
                    "type": "int",
                    "default_value": 0,
                    "enabled": true
                },
                "resume_temp_cmd":
                {
                    "label": "Resume Temperature Cmd",
                    "description": "'M104 S' will allow the print to continue immediately.  'M109 R'' will park the print head and wait for the temperature to either rise or fall to the new set point and then resume the print.",
                    "type": "enum",
                    "options": {
                        "m109_cmd": "M109 R",
                        "m104_cmd": "M104 S"},
                    "default_value": "m109_cmd"
                },
                "resume_temperature":
                {
                    "label": "Resume Print Temperature",
                    "description": "The 'go back to' temperature to continue at.  This is usually your Print Temperature.",
                    "unit": "°C",
                    "type": "int",
                    "default_value": 210,
                    "enabled": true
                },
                "park_position":
                {
                    "label": "Park the Head at the",
                    "description": "Where to park the head for oozing during the temperature wait.",
                    "type": "enum",
                    "options": {
                        "left_front": "Left Front",
                        "right_front": "Right Front",
                        "left_rear": "Left Rear",
                        "right_rear": "Right Rear",
                        "mid_plate": "Mid-Point"},
                    "default_value": "left_front"
                },
                "head_move_z":
                {
                    "label": "Z Lift Before Travel",
                    "description": "The Height to raise the Z-axis above the print before parking.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 3.0,
                    "enabled": true
                }
            }
        }"""

    def initialize(self) -> None:
        super().initialize()
        
        extruder = Application.getInstance().getGlobalContainerStack().extruderList
        print_temperature = str(extruder[0].getProperty("material_print_temperature", "value"))
        self._instance.setProperty("resume_temperature", "value", print_temperature)
        self._instance.setProperty("bridge_temperature", "value", int(print_temperature) - 10)

    # If AddCoolingProfile is ahead of BridgeTempAdjust then notify the user.
        scripts_list = Application.getInstance().getGlobalContainerStack().getMetaDataEntry("post_processing_scripts")
        for script_str in scripts_list.split("\n"):
            if "BridgeTemperatureAdjustment" in script_str:
                break
            if "AddCoolingProfile" in script_str:
                Message(text = "Bridge Temp Adjust: {}".format("The post processor exited because it must run ahead of Advanced Cooling Fan Control.")).show()
                return

    def execute(self, data: List[str]) -> List[str]:
        # If AddCoolingProfile is ahead of BridgeTempAdjust then don't run.
        scripts_list = Application.getInstance().getGlobalContainerStack().getMetaDataEntry("post_processing_scripts")
        for script_str in scripts_list.split("\n"):
            if "BridgeTemperatureAdjustment" in script_str:
                break
            if "AddCoolingProfile" in script_str:
                Message(text = "Bridge Temp Adjust: {}".format("The post processor exited because it must run ahead of Advanced Cooling Fan Control.")).show()
                return data
                
        # If bridge settings are disabled then exit.
        if not bool(Application.getInstance().getGlobalContainerStack().getProperty("bridge_settings_enabled", "value")):
            data[0] += ";  Wait for Bridge Temperature Change - did not run - Bridge settings are not enabled\n"
            Message(text = "Bridge Temp Adjust: {}".format("The post processor exited because Bridge Settings are not enabled in Cura.")).show()
            return data
            
        # Dependent on the firmware flavor; if Nozzle Temp Control is disabled then exit.
        if not bool(Application.getInstance().getGlobalContainerStack().getProperty("machine_nozzle_temp_enabled", "value")):
            data[0] += ";  Wait for Bridge Temperature Change did not run - Machine Nozzle Temp Control is disabled" + "\n"
            Message(text = "Bridge Temp Adjust: {}".format("The post processor exited because Nozzle Temperature Control is not enabled in Cura.")).show()
            return data
            
        # Get some settings from Cura    
        MyCura = Application.getInstance().getGlobalContainerStack()
        extruder = Application.getInstance().getGlobalContainerStack().extruderList
        print_temperature = str(extruder[0].getProperty("material_print_temperature", "value"))
        speed_z = "F" + str(int(extruder[0].getProperty("speed_z_hop", "value"))*60)
        speed_trav = "F" + str(int(extruder[0].getProperty("speed_travel", "value"))*60)
        speed_retract = "F" + str(int(extruder[0].getProperty("retraction_speed", "value"))*60)
        retract_dist = str(extruder[0].getProperty("retraction_amount", "value"))
        ignore_bridge_walls = bool(self.getSettingValueByKey("ignore_bridge_walls"))
        if ignore_bridge_walls:
            feature_type = ";TYPE:SKIN"
        else:
            feature_type = ";TYPE:"
        if bool(MyCura.getProperty("relative_extrusion", "value")):
            rel_ext_cmd = "M83"
        else:
            rel_ext_cmd = "M82"
        bridge_temp = self.getSettingValueByKey("bridge_temperature")
        resume_temperature = self.getSettingValueByKey("resume_temperature")
        
        # This SWAG keeps track of the time hit so the TIME and TIME_ELAPSED can be updated.
        temp_diff = bridge_temp - resume_temperature
        if temp_diff < 1: temp_diff *= -1
        time_add = (temp_diff * 2) + 9
        m109_count = 0
        
        # Set the temperature commands
        if str(self.getSettingValueByKey("bridge_temp_cmd")) == "m109_cmd":
            wait_cmd = "M109 R"
        else:
            wait_cmd = "M104 S"
        if str(self.getSettingValueByKey("resume_temp_cmd")) == "m109_cmd":
            resume_cmd = "M109 R"
        else:
            resume_cmd = "M104 S"
            
        # Set the Park Position
        center_is_zero = bool(MyCura.getProperty("machine_center_is_zero", "value"))
        bed_shape = str(MyCura.getProperty("machine_shape", "value"))
        bed_width = int(MyCura.getProperty("machine_width", "value"))
        bed_depth = int(MyCura.getProperty("machine_depth", "value"))
        park_position = str(self.getSettingValueByKey("park_position"))
        if park_position == "left_front":
            if not center_is_zero and bed_shape == "rectangular":
                park_x = 0
                park_y = 0
            elif center_is_zero and bed_shape == "rectangular":
                park_x = (int(MyCura.getProperty("machine_width", "value"))/2)*-1
                park_y = (int(MyCura.getProperty("machine_depth", "value"))/2)*-1
            elif center_is_zero and bed_shape == "elliptic":
                park_x = (int(MyCura.getProperty("machine_width", "value"))/2)*-0.7
                park_y = (int(MyCura.getProperty("machine_depth", "value"))/2)*-0.7
        elif park_position == "right_front":
            if not center_is_zero and bed_shape == "rectangular":
                park_x = bed_width
                park_y = 0
            elif center_is_zero and bed_shape == "rectangular":
                park_x = (int(MyCura.getProperty("machine_width", "value"))/2)
                park_y = (int(MyCura.getProperty("machine_depth", "value"))/2)*-1
            elif center_is_zero and bed_shape == "elliptic":
                park_x = (int(MyCura.getProperty("machine_width", "value"))/2)*0.7
                park_y = (int(MyCura.getProperty("machine_depth", "value"))/2)*-0.7
        elif park_position == "left_rear":
            if not center_is_zero and bed_shape == "rectangular":
                park_x = 0
                park_y = bed_depth
            elif center_is_zero and bed_shape == "rectangular":
                park_x = (int(MyCura.getProperty("machine_width", "value"))/2)*-1
                park_y = (int(MyCura.getProperty("machine_depth", "value"))/2)
            elif center_is_zero and bed_shape == "elliptic":
                park_x = (int(MyCura.getProperty("machine_width", "value"))/2)*-0.7
                park_y = (int(MyCura.getProperty("machine_depth", "value"))/2)*0.7
        elif park_position == "right_rear":
            if not center_is_zero and bed_shape == "rectangular":
                park_x = bed_width
                park_y = bed_depth
            elif center_is_zero and bed_shape == "rectangular":
                park_x = (int(MyCura.getProperty("machine_width", "value"))/2)
                park_y = (int(MyCura.getProperty("machine_depth", "value"))/2)
            elif center_is_zero and bed_shape == "elliptic":
                park_x = (int(MyCura.getProperty("machine_width", "value"))/2)*0.7
                park_y = (int(MyCura.getProperty("machine_depth", "value"))/2)*0.7
        elif park_position == "mid_plate":
            if not center_is_zero and bed_shape == "rectangular":
                park_x = bed_width/2
                park_y = bed_depth/2
            elif center_is_zero and bed_shape == "rectangular":
                park_x = 0
                park_y = 0
            elif center_is_zero and bed_shape == "elliptic":
                park_x = 0
                park_y = 0
                
        # Relative Travel Height and initialize variables
        move_z = self.getSettingValueByKey("head_move_z")
        current_z = 0
        current_e = 0
        previous_e = 0
        is_retracted = False        
        is_bridge = False
        
        for lay_index, layer in enumerate(data):
            # If there is no BRIDGE in the layer then skip it
            if not ";BRIDGE\n" in layer:
                continue
            lines = layer.split("\n")
            for index, line in enumerate(lines):
                # If a Z, XY, or E parameter is in the line then get the value
                if line.startswith("G0 ") or line.startswith("G1 ") or line.startswith("G2 ") or line.startswith("G3 "):
                    if self.getValue(line, "Z") is not None:
                        current_z = self.getValue(line, "Z")
                    if self.getValue(line, "X") is not None and self.getValue(line, "Y") is not None:
                        x = self.getValue(line, "X")
                        y = self.getValue(line, "Y")
                    if self.getValue(line, "E") is not None:
                        current_e = self.getValue(line, "E")
                        
                        # Track the retractions so we don't double dip if there already was one.
                        if current_e >= previous_e:
                            is_retracted = False
                        elif current_e < previous_e:
                            is_retracted = True
                        previous_e = current_e
                
                # Reverse the park and wait code to resume the print-------------------------
                if line.startswith(feature_type) and lines[index+1].startswith(";BRIDGE"):  
                    if wait_cmd == "M104 S":
                        lines.insert(index+2,wait_cmd + str(bridge_temp))
                        next_start = index+3
                    elif wait_cmd == "M109 R":
                        lines.insert(index+2, rel_ext_cmd)
                        lines.insert(index+2, "G90")
                        if not is_retracted:
                            lines.insert(index+2, "G1 " + speed_retract + " E" + str(retract_dist))
                        else:
                            lines.insert(index+2, ";Prime Not Required")                            
                        lines.insert(index+2, "G0 " + speed_z + " Z-" + str(move_z))
                        lines.insert(index+2, "G91")
                        lines.insert(index+2, "G0 " + speed_trav + " X" + str(x) + " Y" + str(y))
                        lines.insert(index+2, wait_cmd + str(bridge_temp))
                        lines.insert(index+2, "G0 " + speed_trav + " X" + str(park_x) + " Y" + str(park_y))
                        lines.insert(index+2, "G90")
                        lines.insert(index+2, "G0 " + speed_z + " Z" + str(move_z))
                        if not is_retracted:
                            lines.insert(index+2, "G1 " + speed_retract + " E-" + str(retract_dist))
                        else:
                            lines.insert(index+2, ";Retraction Not Required")
                        lines.insert(index+2, "M83")
                        lines.insert(index+2, "G91")
                        next_start = index+15
                        m109_count += 1
                        
                    # Track the XYZE while scrolling down to the next "TYPE" change
                    for num in range(next_start,len(lines),1):
                        if self.getValue(lines[num], "Z") is not None:
                            current_z = self.getValue(lines[num], "Z")
                        if self.getValue(lines[num], "X") is not None and self.getValue(lines[num], "Y") is not None:
                            x = self.getValue(lines[num], "X")
                            y = self.getValue(lines[num], "Y")
                        if self.getValue(lines[num], "E") is not None:
                            current_e = self.getValue(lines[num], "E")
                            if float(current_e) >= float(previous_e):
                                is_retracted = False
                            else:
                                is_retracted = True           
                            previous_e = current_e
                            
                        # Catch TYPE or MESH.  If M104 was chosen then there is no park and wait.  Resume temp code.
                        if lines[num].startswith(";TYPE") or lines[num].startswith(";MESH"):
                            if resume_cmd == "M104 S":
                                lines.insert(num+1,resume_cmd + str(resume_temperature))
                                break
                            elif resume_cmd == "M109 R":
                                lines.insert(num+1, rel_ext_cmd)
                                lines.insert(num+1, "G90")
                                if not is_retracted:
                                    lines.insert(num+1, "G1 " + speed_retract + " E" + str(retract_dist))
                                else:
                                    lines.insert(num+1, ";Prime Not Required")
                                lines.insert(num+1, "G0 " + speed_z + " Z-" + str(move_z))
                                lines.insert(num+1, "G91")
                                lines.insert(num+1, "G0 " + speed_trav + " X" + str(x) + " Y" + str(y))
                                lines.insert(num+1, resume_cmd + str(resume_temperature))
                                lines.insert(num+1, "G0 " + speed_trav + " X" + str(park_x) + " Y" + str(park_y))
                                lines.insert(num+1, "G90")
                                lines.insert(num+1, "G0 " + speed_z + " Z" + str(move_z))
                                if not is_retracted:
                                    lines.insert(num+1, "G1 " + speed_retract + " E-" + str(retract_dist))
                                else:
                                    lines.insert(num+1, ";Retraction Not Required")
                                lines.insert(num+1, "M83")
                                lines.insert(num+1, "G91")
                                m109_count += 1
                                break
                                
                # Adjust the elapsed time of a layer that has bridges and M109 is enabled.
                if line.startswith(";TIME_ELAPSED:"):
                    elapsed_time = float(line.split(":")[1])
                    elapsed_time += int(m109_count) * int(time_add)
                    lines[index] = ";TIME_ELAPSED:" + str(round(elapsed_time))
            data[lay_index] = "\n".join(lines)
        layer = data[0]
        
        # Adjust the print time at the start of the file
        t_str = layer.split(";TIME:")[1]
        t_str = int(t_str.split("\n")[0])
        t_str += int(m109_count) * int(time_add)
        data[0] = re.sub(";TIME:(\d*)",";TIME:" + str(t_str),data[0])
        return data