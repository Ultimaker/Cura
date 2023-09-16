# Copyright (c) 2023 GregValiant (Greg Foresi)
#   This PostProcessingPlugin is released under the terms of the AGPLv3 or higher.
#   This Wrapper is a collection of 8 occasionally useful Post Processors:
#     1) Remove Comments - Remove semi-colons and everything to the right of a semi-colon.  There are options.
#     2) Renumber Layers - For One-At-A-Time prints.  PauseAtHeight and Filament Change act differently.
#     3) Add Extruder End code - A bug fix - this adds any 'Extruder End Gcode' of the last extruder used to the end of the file.
#     4) Add Data Headers (a debugging utility) - Splits the gcode and adds comments between the data sections
#     5) Lift Head Parking - adds a park move to the "Lift Head" cooling option for small layers.  It uses the Min and Max XY numbers of the gcode, and determines the shortest distance required to move off the part.
#     6) Change Printer Settings - Max Feedrate, Max Accel, Home Offsets, Steps/mm.  (There is no Max for Jerk)
#     7) Very Cool FanPath - Raise 1mm and follow a zigzag path across the print with just the Layer Cooling Fan running.
#     8) Disable ABL for small prints.  The user defines 'small' and models that fall below that cause G29 and M420 to be commented out.

from ..Script import Script
from UM.Application import Application
from UM.Message import Message
import re
import os
import sys

class LittleUtilities(Script):

    def initialize(self) -> None:
        super().initialize()
        # Get the Max Feedrate and Max Accel from Cura Printer Settings (may be different than what the printer has)
        mycura = Application.getInstance().getGlobalContainerStack()
        extruder = Application.getInstance().getGlobalContainerStack().extruderList
        self._instance.setProperty("change_feedrate_X", "value", mycura.getProperty("machine_max_feedrate_x", "value"))
        self._instance.setProperty("change_feedrate_Y", "value", mycura.getProperty("machine_max_feedrate_y", "value"))
        self._instance.setProperty("change_feedrate_Z", "value", mycura.getProperty("machine_max_feedrate_z", "value"))
        self._instance.setProperty("change_feedrate_E", "value", mycura.getProperty("machine_max_feedrate_e", "value"))
        self._instance.setProperty("change_accel_X", "value", mycura.getProperty("machine_max_acceleration_x", "value"))
        self._instance.setProperty("change_accel_Y", "value", mycura.getProperty("machine_max_acceleration_y", "default_value"))
        self._instance.setProperty("change_steps_X", "value", str(extruder[0].getProperty("machine_steps_per_mm_x", "value")))
        self._instance.setProperty("change_steps_Y", "value", str(extruder[0].getProperty("machine_steps_per_mm_y", "value")))
        self._instance.setProperty("change_steps_Z", "value", str(extruder[0].getProperty("machine_steps_per_mm_z", "value")))
        self._instance.setProperty("change_steps_E", "value", str(extruder[0].getProperty("machine_steps_per_mm_e", "value")))
        self._instance.setProperty("very_cool_feed", "value", str(round(int(extruder[0].getProperty("speed_travel", "value"))/4,0)))

    def getSettingDataString(self):
        return """{
            "name": "Little Utilities",
            "key": "LittleUtilities",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "pick_a_post":
                {
                    "label": "Pick a Post Processor",
                    "description": "<Remove Comments> will remove the semi-colon and all text to the right.    <Add Extruder End Gcode> will put any Extruder End Gcode of the last extruder used at the beginning of the Ending Gcode in the file.    <Add Data Headers> will split the gcode into sections in the manner it is received from Cura.    <Lift Head Parking> will add a move to get the nozzle away from the print so any oozing doesn't drop on the print.  The move is to the edge of the skirt/brim/raft via the shortest distance.  <Fan-Only Toolpath> runs a zigzag toolpath 1mm above the print with just the fan on.    <Disable ABL> will comment out G29 and M420 lines from the StartUp if the print area is below a user specified footprint.",
                    "type": "enum",
                    "options": {
                        "remove_comments": "Remove Comments",
                        "renumber_layers": "Renumber or Revert layer numbers",
                        "add_extruder_end": "Add Extruder End Gcode",
                        "add_data_header": "Add Data Headers",
                        "lift_head_park": "Lift Head Parking",
                        "change_printer_settings": "Change Printer Settings",
                        "very_cool": "Very Cool Fanpath",
                        "disable_ABL": "Disable ABL"},
                    "default_value": "remove_comments"
                },
                "inc_opening":
                {
                    "label": "Include opening paragraph:",
                    "description": "The opening generally consists of comments only and includes from 'Flavor' to 'MAXZ'.  (The 'POSTPROCESSED' line is added after the scripts have all run.)",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "pick_a_post == 'remove_comments'"
                },
                "inc_startup":
                {
                    "label": "Include StartUp Gcode:",
                    "description": "The StartUp section is from 'generated with...' to ';LAYER_COUNT:'.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "pick_a_post == 'remove_comments'"
                },
                "leave_layer":
                {
                    "label": "Remove ';LAYER:' lines:",
                    "description": "If unchecked then the ';LAYER:' lines will be left in.  That makes searching the gcode easier.  Post processors that run after this one may require the Layer lines.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "pick_a_post == 'remove_comments'"
                },
                "inc_ending":
                {
                    "label": "Include Ending Gcode:",
                    "description": "The Ending Gcode may have comments.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "pick_a_post == 'remove_comments'"
                },
                "renum_layers":
                {
                    "label": "Renumber or UN-Renumber:",
                    "description": "For use with One-At-A-Time prints.  Re-numbering the layer from 0 to Top Layer will cause Pause At Height or Filament Change to act differently.  After re-numbering you might wish to set it back to affect any additional following post-processors.",
                    "type": "enum",
                    "options": {
                        "renum": "Renumber>AllAtOnce",
                        "un_renum": "Revert>OneAtATime"},
                    "default_value": "renum",
                    "enabled": "pick_a_post == 'renumber_layers'"
                },
                "change_feedrate":
                {
                    "label": "Change Printer Max Speeds",
                    "description": "Change the max feedrate for any axes. Blank entries mean No Change.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "pick_a_post == 'change_printer_settings'"
                },
                "change_feedrate_X":
                {
                    "label": "    Max X Feedrate",
                    "description": "Change the Max X feedrate.",
                    "type": "str",
                    "default_value": "",
                    "unit": "mm/sec  ",
                    "enabled": "pick_a_post == 'change_printer_settings' and change_feedrate"
                },
                "change_feedrate_Y":
                {
                    "label": "    Max Y Feedrate",
                    "description": "Change the Max Y feedrate.",
                    "type": "str",
                    "default_value": "",
                    "unit": "mm/sec  ",
                    "enabled": "pick_a_post == 'change_printer_settings' and change_feedrate"
                },
                "change_feedrate_Z":
                {
                    "label": "    Max Z Feedrate",
                    "description": "Change the Max Z feedrate.",
                    "type": "str",
                    "default_value": "",
                    "unit": "mm/sec  ",
                    "enabled": "pick_a_post == 'change_printer_settings' and change_feedrate"
                },
                "change_feedrate_E":
                {
                    "label": "    Max E Feedrate",
                    "description": "Change the Max E feedrate.",
                    "type": "str",
                    "default_value": "",
                    "unit": "mm/sec  ",
                    "enabled": "pick_a_post == 'change_printer_settings' and change_feedrate"
                },
                "change_XYaccel":
                {
                    "label": "Change Max X-Y Acceleration",
                    "description": "Change the Max Accel for the X and/or Y axes. They can be unequal.  Blank entries mean No Change.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "pick_a_post == 'change_printer_settings'"
                },
                "change_accel_X":
                {
                    "label": "    Max X Acceleration",
                    "description": "Change the Max X Acceleration.",
                    "type": "str",
                    "default_value": "",
                    "unit": "mm/sec²  ",
                    "enabled": "pick_a_post == 'change_printer_settings' and change_XYaccel"
                },
                "change_accel_Y":
                {
                    "label": "    Max Y Acceleration",
                    "description": "Change the Max Y Acceleration.",
                    "type": "str",
                    "default_value": "",
                    "unit": "mm/sec²  ",
                    "enabled": "pick_a_post == 'change_printer_settings' and change_XYaccel"
                },
                "change_home_offset":
                {
                    "label": "Change Home Offsets",
                    "description": "Change the Home Offsets. Blank entries mean No Change.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "pick_a_post == 'change_printer_settings'"
                },
                "change_home_X":
                {
                    "label": "    Home Offset X",
                    "description": "Change the X home offset.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "pick_a_post == 'change_printer_settings' and change_home_offset"
                },
                "change_home_Y":
                {
                    "label": "    Home Offset Y",
                    "description": "Change the Y home offset.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "pick_a_post == 'change_printer_settings' and change_home_offset"
                },
                "change_home_Z":
                {
                    "label": "    Home Offset Z",
                    "description": "Change the Z home offset.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "pick_a_post == 'change_printer_settings' and change_home_offset"
                },
                "change_steps":
                {
                    "label": "Change Steps/MM",
                    "description": "Change the Steps/MM for the XYZE axes. Blank entries mean No Change.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "pick_a_post == 'change_printer_settings'"
                },
                "change_steps_X":
                {
                    "label": "    X Steps/MM",
                    "description": "Change the X Steps.",
                    "type": "str",
                    "default_value": "",
                    "unit": "steps/mm  ",
                    "enabled": "pick_a_post == 'change_printer_settings' and change_steps"
                },
                "change_steps_Y":
                {
                    "label": "    Y Steps/MM",
                    "description": "Change the Y Steps.",
                    "type": "str",
                    "default_value": "",
                    "unit": "steps/mm  ",
                    "enabled": "pick_a_post == 'change_printer_settings' and change_steps"
                },
                "change_steps_Z":
                {
                    "label": "    Z Steps/MM",
                    "description": "Change the Z Steps.",
                    "type": "str",
                    "default_value": "",
                    "unit": "steps/mm  ",
                    "enabled": "pick_a_post == 'change_printer_settings' and change_steps"
                },
                "change_steps_E":
                {
                    "label": "    E Steps/MM",
                    "description": "Change the E Steps.",
                    "type": "str",
                    "default_value": "",
                    "unit": "steps/mm  ",
                    "enabled": "pick_a_post == 'change_printer_settings' and change_steps"
                },
                "save_changes":
                {
                    "label": "Save all changes (M500)",
                    "description": "Save the changes to the printer EEPROM or memory. If you don't save then any changes will expire when the printer is turned off.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "pick_a_post == 'change_printer_settings' and (change_home_offset or change_XYaccel or change_feedrate or change_steps)"
                },
                "very_cool_layer":
                {
                    "label": "End of which layer(s)?",
                    "description": "Pick the layer(s) from the Cura preview.  The printhead will move in a grid toolpath 1.0mm above the current Z (no extrusions) with the Layer Cooling Fan speed at the percent you enter here.  For multiple layers delimit with a comma (',') and delimit ranges of layers with a dash ('-') do not add spaces.  Ex: 5,6,12-25,30,45-55 or 200-225",
                    "type": "str",
                    "default_value": "1-227",
                    "unit": "Lay num  ",
                    "enabled": "pick_a_post == 'very_cool'"
                },
                "very_cool_feed":
                {
                    "label": "ToolPath Speed mm/sec",
                    "description": "The Speed to run the printhead along the cooling fan path.",
                    "type": "int",
                    "default_value": 50,
                    "minimum_value": 7,
                    "minimum_value_warning": 10,
                    "maximum_value": 400,
                    "unit": "mm/sec  ",
                    "enabled": "pick_a_post == 'very_cool'"
                },
                "very_cool_fan":
                {
                    "label": "FanPath Cooling Fan %",
                    "description": "The % of the Fan Speed to apply to the cooling runs.",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": 25,
                    "maximum_value": 100,
                    "unit": "%  ",
                    "enabled": "pick_a_post == 'very_cool'"
                },
                "very_cool_y_index":
                {
                    "label": "Add Y zigzag path",
                    "description": "The toolpath is an X zigzag. Enabling the Y will create a grid toolpath. That doubles the cooling effect and takes twice as long.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "pick_a_post == 'very_cool'"
                },
                "disable_ABL_min_footprint":
                {
                    "label": "Minimum Footprint for ABL",
                    "description": "FOR SINGLE MODELS ONLY - this disables the StartUp ABL commands for small prints.  Enter the minimum size of the print in square mm's (any skirt/brim/raft will be ignored).  Models that take up less space than this will NOT USE the ABL.  Both G29 and M420 lines would be commented out of the StartUp Gcode for this slice only.",
                    "type": "int",
                    "default_value": 900,
                    "minimum_value": 4,
                    "unit": "mm²  ",
                    "enabled": "pick_a_post == 'disable_ABL'"
                }
            }
        }"""

    def execute(self, data):
        pick_a_post = self.getSettingValueByKey("pick_a_post")
        if  pick_a_post == "add_extruder_end":
            self._add_extruder_end(data)
        elif pick_a_post == "add_data_header":
            self._add_data_header(data)
        elif pick_a_post == "remove_comments":
            self._remove_comments(data)
        elif pick_a_post == "renumber_layers":
            self._renumber_layers(data)
        elif pick_a_post == "lift_head_park":
            self._lift_head_park(data)
        elif pick_a_post == "change_printer_settings":
            self._change_printer_settings(data)
        elif pick_a_post == "very_cool":
            self._very_cool(data)
        elif pick_a_post == "disable_ABL":
            self._disable_ABL(data)
        return data

    # Add Extruder Ending Gcode-------------------------------------------
    def _add_extruder_end(self, data:str)->str:
        T_nr = 0
        try:
            for num in range(1,len(data)-2):
                lines = data[num].split("\n")
                for line in lines:
                    if re.match("T(\d*)",line):
                        T_nr = self.getValue(line, "T")
            end_gcode = Application.getInstance().getGlobalContainerStack().extruderList[T_nr].getProperty("machine_extruder_end_code","value")
        except:
            end_gcode = Application.getInstance().getGlobalContainerStack().extruderList[0].getProperty("machine_extruder_end_code","value")
        if end_gcode != "":
            data[len(data)-2] += ";\n" + end_gcode + "\n;\n"
        return

    # Add data headers to each data section.  Add 'Total Cmd Lines' to data[0]
    def _add_data_header(self, data:str)->str:
        for num in range(0,len(data)-1):
            data[num] = ";>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>Start of DATA[" + str(num) + "]<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<\n" + data[num]
        data[len(data)-1] += ";>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>Start of DATA[" + str(num+1) + "]<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<\n"
        tot_lines = 2
        comments = 0
        for num in range(0,len(data)):
            tot_lines += data[num].count("\n")
            comments += data[num].count(";")
        tot_lines -= comments
        data[0] += ";  Command Lines: " + str(tot_lines) + " | Comments: " + str(comments) + "\n"
        return

    # Remove Comments-----------------------------------------------------
    def _remove_comments(self, data:str)->str:
        me_opening = bool(self.getSettingValueByKey("inc_opening"))
        me_startup = bool(self.getSettingValueByKey("inc_startup"))
        me_ending = bool(self.getSettingValueByKey("inc_ending"))
        me_layerlines = bool(self.getSettingValueByKey("leave_layer"))

        # Start with the opening data paragraph if enabled----------------
        if me_opening:
            layer = data[0]
            lines = layer.split("\n")
            modified_data = ""
            for line in lines:
                if line.startswith(";"):
                    line = ""
                    continue
                if ";" in line:
                    line = line.split(";")[0]
                modified_data += line + "\n"
            data[0] = modified_data[0:-1]

        # the StartUp Gcode section if enabled----------------------------
        if me_startup:
            layer = data[1]
            lines = layer.split("\n")
            modified_data = ""
            for line in lines:
                if line.startswith(";"):
                    line = ""
                    continue
                if ";" in line:
                    line = line.split(";")[0]
                modified_data += line + "\n"
            data[1] = modified_data[0:-1]
        stop_at = len(data)
        if me_ending:
            stop_at = len(data)
        else:
            stop_at = len(data)-1

        # Remove comments from the Layers and (if enabled) from the Ending Gcode
        for num in range(2,stop_at,1):
            layer = data[num]
            lines = layer.split("\n")
            modified_data = ""
            for line in lines:
                # Leave the Layer Lines unless removal is enabled---------
                if line.startswith(";LAYER:") and not me_layerlines:
                    modified_data += line + "\n"
                    continue
                if line.startswith(";"):
                    line = ""
                    continue
                if ";" in line:
                    line = line.split(";")[0]
                modified_data += line + "\n"
            data[num] = modified_data[0:-1]
        return

    # Renumber Layers-----------------------------------------------------
    def _renumber_layers(self, data:str)->str:
        renum_layers = str(self.getSettingValueByKey("renum_layers"))
        one_at_a_time = Application.getInstance().getGlobalContainerStack().getProperty("print_sequence", "value")

        #If the project was sliced 'All at Once' then Exit----------------
        if one_at_a_time == "all_at_once":
            data[0] += ";  [Little Utilities] (Renumber Layers did not run because the Print Sequence is All-At-Once)\n"
            Message(title = "[Little Utilities] Renumber Layers", text = "Did not run because the Print Sequence is All-At-Once.").show()
            return data

        # Count the layers because "LAYER_COUNT" can be theoretical-------
        raft_lay_count = 0
        lay_count = 0
        layer_0_index = 2
        for num in range(1,len(data)-1,1):
            layer = data[num]
            if ";LAYER:0" in layer:
                layer0_index = num
                break

        # Renumber the layers---------------------------------------------
        if renum_layers == "renum":
            lay_num = 0
            for num in range(layer0_index,len(data)-1,1):
                layer = data[num]
                if layer.startswith(";LAYER:") and not layer.startswith(";LAYER:-"):
                    temp = layer.split("\n")
                    data[num] = layer.replace(temp[0],";LAYER:" + str(lay_num))
                    lay_num += 1
            layer = data[layer0_index - 1]
        elif renum_layers == "un_renum":

        # Revert the numbering to OneAtATime if enabled-------------------
            lay_num = 0
            for num in range(layer0_index,len(data)-1,1):
                layer = data[num]
                if layer.startswith(";LAYER:") and not layer.startswith(";LAYER:-"):
                    temp = layer.split("\n")
                    data[num] = layer.replace(temp[0],";LAYER:" + str(lay_num))
                    lay_num += 1
                if ";LAYER_COUNT:" in layer:
                    lay_num = 0
            layer = data[layer0_index - 1]

        # Move the 'Time_Elapsed' and 'Layer_Count' lines to the end of their data sections in case of a PauseAtHeight
        modified_data = ""
        for num in range(2,len(data)-2,1):
            layer = data[num]
            lines = layer.split("\n")
            modified_data = ""
            time_line = ""
            for line in lines:
                if line.startswith(";TIME_ELAPSED:") or line.startswith(";LAYER_COUNT:"):
                    time_line += line + "\n"
                    line = ""
                if line != "":
                    modified_data += line + "\n"
            data[num] = modified_data + time_line

        # Change each Layer_Count line to reflect the new total layers
        if renum_layers == "renum":
            for num in range(1,len(data)-1,1):
                layer = data[num]
                data[num] = re.sub(";LAYER_COUNT:(\d*)",";LAYER_COUNT:" + str(len(data) - 3),layer)

        # If reverting to one-at-a-time then change the LAYER_COUNT back to per model
        elif renum_layers == "un_renum":
            model_lay_count = 0
            for num in range(len(data)-1,1,-1):
                if ";LAYER:" in data[num]:
                    model_lay_count += 1
                if ";LAYER:0" in data[num]:
                    data[num-1] = re.sub(";LAYER_COUNT:(\d*)",";LAYER_COUNT:" + str(model_lay_count), data[num-1])
                    model_lay_count = 0
        return

    # Lift Head Parking---------------------------------------------------
    def _lift_head_park(self, data:str)->str:
        extruder = Application.getInstance().getGlobalContainerStack().extruderList
        # Send a message and exit if Lift Head is not enabled-------------
        if not bool(extruder[0].getProperty("cool_lift_head", "value")):
            Message(title = "[Little Utilities] LiftHead Parking", text = "Did not run because 'Lift Head' is not enabled.").show()
            return data
        travel_speed = int(extruder[0].getProperty("speed_travel", "value"))*60

        # Get the footprint size of the print on the build plate----------
        lines = data[0].split("\n")
        for line in lines:
            if line.startswith(";MINX:"):
                X_min = float(line.split(":")[1])
            if line.startswith(";MINY:"):
                Y_min = float(line.split(":")[1])
            if line.startswith(";MAXX:"):
                X_max = float(line.split(":")[1])
            if line.startswith(";MAXY:"):
                Y_max = float(line.split(":")[1])

        # Get the XY origin of the print----------------------------------
        mesh_X_origin = round(X_max - ((X_max - X_min)/2),2)
        mesh_Y_origin = round(Y_max - ((Y_max - Y_min)/2),2)

        # Find the lines that start with "Small layer"--------------------
        for lay_num in range(2, len(data)-1,1):
            layer = data[lay_num]
            lines = layer.split("\n")
            for index, line in enumerate(lines):
                if not line.startswith(";Small layer"):
                    continue
                else:
                # Get the "Return to" location and calculate the shortest move off the print
                    X_park = 0
                    Y_park = 0
                    for xy_index in range(index-1, 0,-1):
                        if " X" in lines[xy_index] and " Y" in lines[xy_index]:
                            X_loc = self.getValue(lines[xy_index], "X")
                            Y_loc = self.getValue(lines[xy_index], "Y")
                            if X_loc <= mesh_X_origin:
                                X_park = X_min
                                X_delta = X_loc - X_min
                            elif X_loc > mesh_X_origin:
                                X_park = X_max
                                X_delta = X_max - X_loc
                            if Y_loc <= mesh_Y_origin:
                                Y_park = Y_min
                                Y_delta = Y_loc - Y_min
                            elif Y_loc > mesh_Y_origin:
                                Y_park = Y_max
                                Y_delta = Y_max - Y_loc
                            break
                    if float(X_delta) >= float(Y_delta):
                        park_line = f"G0 F{travel_speed} Y{Y_park}"
                    else:
                        park_line = f"G0 F{travel_speed} X{X_park}"

                    # Insert the move and return lines--------------------
                    if self.getValue(lines[index+1], "E") is not None:
                        lines.insert(index + 3, park_line)
                        lines.insert(index + 5, f"G0 F{travel_speed} X{X_loc} Y{Y_loc}")
                    else:
                        lines.insert(index + 2, park_line)
                        lines.insert(index + 4, f"G0 F{travel_speed} X{X_loc} Y{Y_loc}")
                    break
            data[lay_num] = "\n".join(lines)
        return

    # Change printer settings---------------------------------------------
    def _change_printer_settings(self, data:str)->str:
        change_feed_string = ""
        change_accel_string = ""
        change_home_string = ""
        change_steps_string = ""
        save_string = ""

        # If there are Feed Rate changes----------------------------------
        if bool(self.getSettingValueByKey("change_feedrate")):
            X_feedrate = str(self.getSettingValueByKey("change_feedrate_X"))
            Y_feedrate = str(self.getSettingValueByKey("change_feedrate_Y"))
            Z_feedrate = str(self.getSettingValueByKey("change_feedrate_Z"))
            E_feedrate = str(self.getSettingValueByKey("change_feedrate_E"))
            if X_feedrate != "" or Y_feedrate != "" or Z_feedrate != "" or E_feedrate != "":
                change_feed_string += "M203"
                if X_feedrate != "":
                    change_feed_string += f" X{X_feedrate}"
                if Y_feedrate != "":
                    change_feed_string += f" Y{Y_feedrate}"
                if Z_feedrate != "":
                    change_feed_string += f" Z{Z_feedrate}"
                if E_feedrate != "":
                    change_feed_string += f" E{E_feedrate}"
                change_feed_string += " ;Change Max Feed Rate\n"

        # If there are Accel changes--------------------------------------
        if bool(self.getSettingValueByKey("change_XYaccel")):
            X_accel = str(self.getSettingValueByKey("change_accel_X"))
            Y_accel = str(self.getSettingValueByKey("change_accel_Y"))
            if X_accel != "" or Y_accel != "":
                change_accel_string += "M201"
                if X_accel != "":
                    change_accel_string += f" X{X_accel}"
                if Y_accel != "":
                    change_accel_string += f" Y{Y_accel}"
                change_accel_string += " ;Change Max Accel\n"

        # If there are Home Offset changes--------------------------------
        if bool(self.getSettingValueByKey("change_home_offset")):
            X_home = str(self.getSettingValueByKey("change_home_X"))
            Y_home = str(self.getSettingValueByKey("change_home_Y"))
            Z_home = str(self.getSettingValueByKey("change_home_Z"))
            if X_home != "" or Y_home != "" or Z_home != "":
                change_home_string += "M206"
                if X_home != "":
                    change_home_string += f" X{X_home}"
                if Y_home != "":
                    change_home_string += f" Y{Y_home}"
                if Z_home != "":
                    change_home_string += f" Z{Z_home}"
                change_home_string += " ;Change Home Offset\n"

        # If there are Steps/MM changes-----------------------------------
        if bool(self.getSettingValueByKey("change_steps")):
            X_steps = str(self.getSettingValueByKey("change_steps_X"))
            Y_steps = str(self.getSettingValueByKey("change_steps_Y"))
            Z_steps = str(self.getSettingValueByKey("change_steps_Z"))
            E_steps = str(self.getSettingValueByKey("change_steps_E"))
            if X_steps != "" or Y_steps != "" or Z_steps != "" or E_steps != "":
                change_steps_string += "M92"
                if X_steps != "":
                    change_steps_string += f" X{X_steps}"
                if Y_steps != "":
                    change_steps_string += f" Y{Y_steps}"
                if Z_steps != "":
                    change_steps_string += f" Z{Z_steps}"
                if E_steps != "":
                    change_steps_string += f" E{E_steps}"
                change_steps_string += " ;Change Steps/MM\n"

        # Allow the user to save the changes to the printer and alter Cura Printer Settings
        if bool(self.getSettingValueByKey("save_changes")) and (bool(self.getSettingValueByKey("change_home_offset")) or bool(self.getSettingValueByKey("change_XYaccel")) or bool(self.getSettingValueByKey("change_feedrate")) or bool(self.getSettingValueByKey("change_steps"))):
            save_string = "M500 ;Save changes to printer\nG4 P500 ;Pause for save\n"
            if bool(self.getSettingValueByKey("change_XYaccel")):
                if X_accel != "":
                    Application.getInstance().getGlobalContainerStack().setProperty("machine_max_acceleration_x", "value", int(X_accel))
                if Y_accel != "":
                    Application.getInstance().getGlobalContainerStack().setProperty("machine_max_acceleration_y", "value", int(Y_accel))
            if bool(self.getSettingValueByKey("change_feedrate")):
                if X_feedrate != "":
                    Application.getInstance().getGlobalContainerStack().setProperty("machine_max_feedrate_x", "value", int(X_feedrate))
                if Y_feedrate != "":
                    Application.getInstance().getGlobalContainerStack().setProperty("machine_max_feedrate_y", "value", int(Y_feedrate))
                if Z_feedrate != "":
                    Application.getInstance().getGlobalContainerStack().setProperty("machine_max_feedrate_z", "value", int(Z_feedrate))
                if E_feedrate != "":
                    Application.getInstance().getGlobalContainerStack().setProperty("machine_max_feedrate_e", "value", int(E_feedrate))
            if bool(self.getSettingValueByKey("change_steps")):
                mycura = Application.getInstance().getGlobalContainerStack()
                extruder = mycura.extruderList
                if X_steps != "":
                    mycura.setProperty("machine_steps_per_mm_x", "value", X_steps)
                    extruder[0].setProperty("machine_steps_per_mm_x", "value", X_steps)
                if Y_steps != "":
                    mycura.setProperty("machine_steps_per_mm_y", "value", Y_steps)
                    extruder[0].setProperty("machine_steps_per_mm_y", "value", Y_steps)
                if Z_steps != "":
                    mycura.setProperty("machine_steps_per_mm_z", "value", Z_steps)
                    extruder[0].setProperty("machine_steps_per_mm_z", "value", Z_steps)
                if E_steps != "":
                    mycura.setProperty("machine_steps_per_mm_e", "value", E_steps)
                    extruder[0].setProperty("machine_steps_per_mm_e", "value", E_steps)

        # Add the changes to the gcode at the end of the StartUp Gcode
        data[1] += change_feed_string + change_accel_string + change_home_string + change_steps_string + save_string
        data[1] = data[1][0:-1]
        lines = data[1].split("\n")

        # Reformat data[1] so ";LAYER_COUNT:xxx" is the last line
        for index, line in enumerate(lines):
            if line.startswith(";LAYER_COUNT"):
                layer_count = line
                lines.remove(layer_count)
                lines.append(layer_count)
                data[1] = "\n".join(lines) + "\n"
        return

    # Very_cool cooling------------------------------------------------
    def _very_cool(self, data:str)->str:
        all_layers = self.getSettingValueByKey("very_cool_layer")
        add_layers = ""
        numstart = 0
        numend = 0
        very_cool_layers = []
        if "," in all_layers:
            new_layers = all_layers.split(",")
            for index, n in enumerate(new_layers):
                if "-" in str(n):
                    numstart = str(n.split("-")[0])
                    numend = str(n.split("-")[1])
                    for m in range(int(numend),int(numstart)-1,-1):
                        new_layers.insert(index+1,m)
                    new_layers.pop(index)
            very_cool_layers = new_layers
        elif not "," in all_layers and "-" in all_layers:
            new_layers = []
            numstart = str(all_layers.split("-")[0])
            numend = str(all_layers.split("-")[1])
            for m in range(int(numstart),int(numend)+1,1):
                new_layers.append(m)
            very_cool_layers = new_layers
        else:
            very_cool_layers.append(all_layers)
        very_cool_y_index = bool(self.getSettingValueByKey("very_cool_y_index"))
        extruder = Application.getInstance().getGlobalContainerStack().extruderList
        travel_speed = str(int(extruder[0].getProperty("speed_travel", "value"))*60)
        zhop_speed = str(int(extruder[0].getProperty("speed_z_hop", "value"))*60)
        retr_enabled = bool(extruder[0].getProperty("retraction_enable", "value"))
        retr_dist = str(extruder[0].getProperty("retraction_amount", "value"))
        retr_speed = str(extruder[0].getProperty("retraction_speed", "value")*60)
        bed_width = int(Application.getInstance().getGlobalContainerStack().getProperty("machine_width", "value"))
        bed_depth = int(Application.getInstance().getGlobalContainerStack().getProperty("machine_depth", "value"))
        fan_percent = self.getSettingValueByKey("very_cool_fan") /100
        fan_speed = 0
        # Check if the fan scale is RepRap 0-1----------------------------
        fan_scale = bool(extruder[0].getProperty("machine_scale_fan_speed_zero_to_one", "value"))
        if not fan_scale:
            very_cool_fan_speed = round(255 * fan_percent)
        else:
            very_cool_fan_speed = round(fan_percent,1)

        # Get the travel speed percentage---------------------------------
        travel_rate = int(self.getSettingValueByKey("very_cool_feed")) * 60
        lines = data[0].split("\n")

        # The Mins and Maxes become the frame for the cooling movement grid
        for line in lines:
            if line.startswith(";MINX:"):
                min_x = line.split(":")[1]
            if line.startswith(";MINY:"):
                min_y = line.split(":")[1]
            if line.startswith(";MAXX:"):
                max_x = line.split(":")[1]
            if line.startswith(";MAXY:"):
                max_y = line.split(":")[1]

        # Track the fan speed---------------------------------------------
        for lay in very_cool_layers:
            cur_layer = int(lay)-1
            for num in range(2,len(data)-2,1):
                layer = data[num]
                if "M106 S" in layer:
                    rev_lines = layer.split("\n")
                    rev_lines.reverse()
                    for line in rev_lines:
                        if line.startswith("M106"):
                            fan_speed = str(self.getValue(line, "S"))
                            break
                        if line.startswith("M107"):
                            fan_speed = 0
                            break

                # Get the return-to X Y-----------------------------------
                if ";LAYER:" + str(cur_layer) + "\n" in layer:
                    prev_layer = data[num].split("\n")
                    prev_layer.reverse()
                    for prev_line in prev_layer:
                        if " X" in prev_line and " Y" in prev_line:
                            ret_x = self.getValue(prev_line, "X")
                            ret_y = self.getValue(prev_line, "Y")
                            break

                    # Check for a retraction------------------------------
                    for prev_line in prev_layer:
                        if " E" in prev_line:
                            ret_e = self.getValue(prev_line, "E")
                            my_match = re.search(" F(\d*) E[-(\d.*)]", prev_line)
                            if my_match is not None:
                                retracted = True
                            else:
                                retracted = False
                            break

                    # Final Z of the layer--------------------------------
                    for prev_line in prev_layer:
                        if " Z" in prev_line:
                            ret_z = self.getValue(prev_line, "Z")
                            lift_z = round(ret_z + 1,2)
                            break

                    # Put the travel string together----------------------
                    lines = []
                    lines.append(";TYPE:CUSTOM [Little Utilities] Very Cool FanPath")
                    lines.append(f"G0 F{zhop_speed} Z{lift_z}")
                    if not retracted and retr_enabled:
                        lines.append(f"G1 F{retr_speed} E{round(ret_e - float(retr_dist),5)}")
                    lines.append(f"M106 S{very_cool_fan_speed}")
                    x_index = float(min_x)
                    lines.append(f"G0 F{travel_rate} X{min_x} Y{min_y}")
                    while x_index < float(max_x):
                        lines.append(f"G0 X{round(x_index,2)} Y{max_y}")
                        if x_index + 10 > bed_width:
                            break
                        lines.append(f"G0 X{round(x_index + 10.0,2)} Y{max_y}")
                        lines.append(f"G0 X{round(x_index + 10.0,2)} Y{min_y}")
                        # Break out of the loop if the move will be beyond the bed width
                        if x_index + 20 > bed_width:
                            break
                        lines.append(f"G0 X{round(x_index + 20.0,2)} Y{min_y}")
                        x_index = x_index + 20.0
                    if very_cool_y_index:
                        y_index = float(min_y)
                        #lines.append("G0 F" + str(travel_rate) + " X" + max_x + " Y" + min_y)
                        while y_index < float(max_y):
                            lines.append(f"G0 X{max_x} Y{round(y_index,2)}")
                            if y_index + 10 > bed_depth:
                                break
                            lines.append(f"G0 X{max_x} Y{round(y_index + 10.0,2)}")
                            lines.append(f"G0 X{min_x} Y{round(y_index + 10.0,2)}")
                            # Break out of the loop if the move will be beyond the bed width
                            if y_index + 20 > bed_depth:
                                break
                            lines.append(f"G0 X{min_x} Y{round(y_index + 20.0,2)}")
                            y_index = y_index + 20.0
                    lines.append(f"M106 S{fan_speed}")
                    lines.append(f"G0 F{travel_speed} X{ret_x} Y{ret_y}")
                    lines.append(f"G0 F{zhop_speed} Z{ret_z}")
                    if not retracted and retr_enabled:
                        lines.append(f"G1 F{retr_speed} E{ret_e}")
                    lines.append(f"G0 F{travel_speed} ;CUSTOM END")
                    fan_layer = "\n".join(lines)
                    time_line = re.search(";TIME_ELAPSED:(\d.*)", data[num])
                    data[num] = re.sub(";TIME_ELAPSED:(\d.*)", fan_layer  + "\n" + time_line[0], data[num])
        return

    # Disable ABL for small prints----------------------------------------
    def _disable_ABL(self, data:str)->str:
        min_footprint = int(self.getSettingValueByKey("disable_ABL_min_footprint"))
        mycura = Application.getInstance().getGlobalContainerStack()
        extruder = mycura.extruderList
        adhesion_extruder_nr = int(mycura.getProperty("adhesion_extruder_nr", "value"))
        if adhesion_extruder_nr == -1: adhesion_extruder_nr = 0
        adhesion_type = str(mycura.getProperty("adhesion_type", "value"))
        skirt_gap = int(extruder[adhesion_extruder_nr].getProperty("skirt_gap", "value")) * 2
        skirt_line_count = int(extruder[adhesion_extruder_nr].getProperty("skirt_line_count", "value"))
        brim_width = int(extruder[adhesion_extruder_nr].getProperty("brim_width", "value")) * 2
        raft_margin = int(extruder[adhesion_extruder_nr].getProperty("raft_margin", "value")) * 2
        adhesion_line_width = float(extruder[adhesion_extruder_nr].getProperty("skirt_brim_line_width", "value"))
        raft_base_line_width = float(extruder[adhesion_extruder_nr].getProperty("raft_base_line_width", "value"))
        # Calculate the skirt/brim/raft width to subtract from the footprint
        if adhesion_type == "brim":
            subtract_dim = brim_width - adhesion_line_width*2
        elif adhesion_type == "skirt":
            if skirt_line_count > 0:
                subtract_dim = skirt_gap + (adhesion_line_width * (skirt_line_count - .5) * 2)
            else:
                subtract_dim = 0.0
        elif adhesion_type == "raft":
            subtract_dim = raft_margin - raft_base_line_width
        else:
            subtract_dim = adhesion_line_width * -1
        # Get the size of the footprint on the build plate
        layer = data[0]
        lines = layer.split("\n")
        for line in lines:
            if line.startswith(";MINX:"):
                min_x = float(line.split(":")[1])
            if line.startswith(";MINY:"):
                min_y = float(line.split(":")[1])
            if line.startswith(";MAXX:"):
                max_x = float(line.split(":")[1])
            if line.startswith(";MAXY:"):
                max_y = float(line.split(":")[1])
        # Determine the actual area of the model
        x_dim = max_x - min_x - subtract_dim
        y_dim = max_y - min_y - subtract_dim
        print_area = round(x_dim * y_dim, 2)
        # Return if the model is over the "min footprint"
        if print_area > min_footprint:
            Message(title = "[Little Utilities] Disable ABL", text = "The 'FootPrint' of the model is " + str(round(print_area,0)) + "mm² so ABL <IS ENABLED>.").show()
            return
        else:
            lines = data[1].split("\n")
            for index, line in enumerate(lines):
                if line.startswith("G29") or line.startswith("M420"):
                    lines[index] = ";" + line
            data[1] = "\n".join(lines)
            Message(title = "[Little Utilities] Disable ABL", text = "The 'FootPrint' of the model is " + str(round(print_area,0)) + "mm² so ABL <IS DISABLED> for this print.").show()
        return