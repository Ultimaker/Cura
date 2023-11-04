# Limit the X-Y Accel/Jerk:  Authored by: Greg Foresi (GregValiant)
# July 2023
# Sometimes bed-slinger printers need different Accel and Jerk values for the Y but Cura always makes them the same.
# This script changes the Accel and/or Jerk from the beginning of the 'Start Layer' to the end of the 'End Layer'.
# The existing M201 Max Accel will be changed to limit the Y (and/or X) accel at the printer.  If you have Accel enabled in Cura and the XY Accel is set to 3000 then setting the Y limit to 1000 will result in the printer limiting the Y to 1000.  This can keep tall skinny prints from breaking loose of the bed and failing.  The script was not tested with Junction Deviation.
# If enabled - the Jerk setting is changed line-by-line within the gcode as there is no "limit" on Jerk.
# If 'Immediate ACCEL change' is selected then an M201 line will be inserted at the Start Layer.  If an End Layer is named then the changes will revert back to the file setting at the end of that layer.  If the End Layer is ' -1 ' then the changes will continue to the end of the file.
# If 'Gradual ACCEL change' is enabled then the Accel is changed gradually from the Start to the End layer and that will then continue to the end of the file.  If 'Gradual' is enabled then the Jerk settings will always continue to be changed to the end of the file or (in one-at-a-time mode) to the next model where they are reset.
# This post is intended for printers with moving beds (bed slingers) so UltiMaker printers are excluded.
# When setting an accel limit on multi-extruder printers ALL extruders are effected.
# This post does not distinguish between Print Accel and Travel Accel.  The limit is the limit for all regardless.  Example: Skin Accel = 1000 and Outer Wall accel = 500.  If the limit is set to 300 then both Skin and Outer Wall will be Accel = 300.
# 9/15/2023 added support for RepRap M566 command for Jerk in mm/min
# 11/1/2023 added support for One-at-a-Time prints.

from ..Script import Script
from cura.CuraApplication import CuraApplication
import re
from UM.Message import Message

class LimitXYAccelJerk(Script):

    def initialize(self) -> None:
        super().initialize()
        # Get the Accel and Jerk and set the values in the setting boxes--
        mycura = CuraApplication.getInstance().getGlobalContainerStack()
        extruder = mycura.extruderList
        accel_print = extruder[0].getProperty("acceleration_print", "value")
        accel_travel = extruder[0].getProperty("acceleration_travel", "value")
        jerk_print_old = extruder[0].getProperty("jerk_print", "value")
        jerk_travel_old = extruder[0].getProperty("jerk_travel", "value")
        self._instance.setProperty("x_accel_limit", "value", round(accel_print))
        self._instance.setProperty("y_accel_limit", "value", round(accel_print))
        self._instance.setProperty("x_jerk", "value", jerk_print_old)
        self._instance.setProperty("y_jerk", "value", jerk_print_old)
        ext_count = int(mycura.getProperty("machine_extruder_count", "value"))
        machine_name = str(mycura.getProperty("machine_name", "value"))
        self._firmware_flavor = str(mycura.getProperty("machine_gcode_flavor", "value"))
        if self._firmware_flavor == "RepRap (RepRap)":
            self._instance.setProperty("jerk_cmd", "value", "reprap_flavor")
        else:
            self._instance.setProperty("jerk_cmd", "value", "marlin_flavor")

        # Warn the user if the printer is an Ultimaker-------------------------
        if "Ultimaker" in machine_name or "UltiGCode" in self._firmware_flavor or "Griffin" in self._firmware_flavor:
            Message(title = "[Limit the X-Y Accel/Jerk]", text = "<NOTICE> The script WILL NOT RUN because Ultimaker printers don't have sliding beds.").show()

        # Warn the user if the printer is multi-extruder------------------
        if ext_count > 1:
            Message(title = "[Limit the X-Y Accel/Jerk]", text = "<NOTICE> The post processor treats all extruders the same.  If you have multiple extruders they will all be subject to the same Accel and Jerk limits imposed.  If you have different Travel and Print Accel they will also be subject to the same limits.  If that is not acceptable then you should not use this Post Processor.").show()

    def getSettingDataString(self):
            return """{
            "name": "Limit the X-Y Accel/Jerk (all extruders equal)",
            "key": "LimitXYAccelJerk",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "type_of_change":
                {
                    "label": "Immediate or Gradual change",
                    "description": "An 'Immediate' change will insert the new numbers immediately at the Start Layer.  A 'Gradual' change will transition from the starting Accel to the new Accel limit across a range of layers.",
                    "type": "enum",
                    "options": {
                        "immediate_change": "Immediate",
                        "gradual_change": "Gradual"},
                    "default_value": "immediate_change"
                },
                "x_accel_limit":
                {
                    "label": "X MAX Acceleration",
                    "description": "If this number is lower than the 'X Print Accel' in Cura then this will limit the Accel on the X axis.  Enter the Maximum Acceleration value for the X axis.  This will affect both Print and Travel Accel.  If you enable an End Layer then at the end of that layer the Accel Limit will be reset (unless you choose 'Gradual' in which case the new limit goes to the top layer).",
                    "type": "int",
                    "enabled": true,
                    "minimum_value": 50,
                    "unit": "mm/sec² ",
                    "default_value": 500
                },
                "y_accel_limit":
                {
                    "label": "Y MAX Acceleration",
                    "description": "If this number is lower than the Y accel in Cura then this will limit the Accel on the Y axis.  Enter the Maximum Acceleration value for the Y axis.  This will affect both Print and Travel Accel.  If you enable an End Layer then at the end of that layer the Accel Limit will be reset (unless you choose 'Gradual' in which case the new limit goes to the top layer).",
                    "type": "int",
                    "enabled": true,
                    "minimum_value": 50,
                    "unit": "mm/sec² ",
                    "default_value": 500
                },
                "start_layer":
                {
                    "label": "    Changes Start Layer:",
                    "description": "Use the Cura Preview numbers. Enter the Layer to start the changes at. The minimum is Layer 1.",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": 10,
                    "unit": "Lay# ",
                    "enabled": "type_of_change == 'immediate_change'"
                },
                "end_layer":
                {
                    "label": "     Changes End at Layer",
                    "description": "Use the Cura Preview numbers. Enter '-1' for the entire file or enter a layer number.  All Accel and/or Jerk changes will end at your 'End Layer' and revert back to the original numbers.",
                    "type": "int",
                    "default_value": -1,
                    "minimum_value": -1,
                    "unit": "Lay# ",
                    "enabled": "type_of_change == 'immediate_change'"
                },
                "gradient_start_layer":
                {
                    "label": "     Alter Accel From Layer",
                    "description": "Enter the Layer to Gradually start changing the accel at. Use the Cura Preview numbers. The minimum is Layer 1.",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": 1,
                    "unit": "Lay# ",
                    "enabled": "type_of_change == 'gradual_change'"
                },
                "gradient_end_layer":
                {
                    "label": "     Alter Accel To Layer",
                    "description": "The Accel will be adjusted gradually between the 'From layer' and the 'To layer'.  Unlike 'Immediate', the final acceleration change and any Jerk changes will always continue to the end of the file.  Use the Cura Preview layer numbers. Enter '-1' for the top layer or enter a layer number.",
                    "type": "int",
                    "default_value": -1,
                    "minimum_value": -1,
                    "unit": "Lay# ",
                    "enabled": "type_of_change == 'gradual_change'"
                },
                "jerk_enable":
                {
                    "label": "Change the Jerk",
                    "description": "Whether to change the Jerk values.",
                    "type": "bool",
                    "enabled": true,
                    "default_value": false
                },
                "jerk_cmd":
                {
                    "label": "G-Code Jerk Command",
                    "description": "Marlin uses M205 in mm/sec.  RepRap uses M566 in mm/min.",
                    "type": "enum",
                    "options": {
                        "marlin_flavor": "M205",
                        "reprap_flavor": "M566"},
                    "default_value": "marlin_flavor",
                    "enabled":  "jerk_enable"
                },
                "x_jerk":
                {
                    "label": "    X jerk",
                    "description": "Enter the Jerk value for the X axis in mm/sec.  This setting will affect both the Print and Travel jerk.  If M566 is used the value will be converted to mm/min.",
                    "type": "int",
                    "enabled": "jerk_enable",
                    "unit": "mm/sec ",
                    "default_value": 8,
                    "minimum_value": 4,
                    "minimum_value_warning": 6    
                },
                "y_jerk":
                {
                    "label": "    Y jerk",
                    "description": "Enter the Jerk value for the Y axis in mm/sec.  This setting will affect both the Print and Travel jerk.  If M566 is used the value will be converted to mm/min.",
                    "type": "int",
                    "enabled": "jerk_enable",
                    "unit": "mm/sec ",
                    "default_value": 8,
                    "minimum_value": 4,
                    "minimum_value_warning": 6                    
                }
            }
        }"""

    def execute(self, data):
        mycura = CuraApplication.getInstance().getGlobalContainerStack()
        extruder = mycura.extruderList
        machine_name = str(mycura.getProperty("machine_name", "value"))
        print_sequence = str(mycura.getProperty("print_sequence", "value"))

        # Exit if the printer is an Ultimaker------------------------------------------------------
        if "Ultimaker" in machine_name or "UltiGCode" in self._firmware_flavor or "Griffin" in self._firmware_flavor:
            Message(title = "[Limit the X-Y Accel/Jerk]", text = "<NOTICE> The script DID NOT RUN.  This post processor is for bed slinger printers only.").show()
            data[0] += ";  [LimitXYAccelJerk] DID NOT RUN because the printer doesn't have a sliding bed.\n"
            return data

        type_of_change = str(self.getSettingValueByKey("type_of_change"))
        accel_print_enabled = bool(extruder[0].getProperty("acceleration_enabled", "value"))
        accel_travel_enabled = bool(extruder[0].getProperty("acceleration_travel_enabled", "value"))
        accel_print = extruder[0].getProperty("acceleration_print", "value")
        accel_travel = extruder[0].getProperty("acceleration_travel", "value")
        jerk_print_enabled = str(extruder[0].getProperty("jerk_enabled", "value"))
        jerk_travel_enabled = str(extruder[0].getProperty("jerk_travel_enabled", "value"))
        jerk_print_old = extruder[0].getProperty("jerk_print", "value")
        jerk_travel_old = extruder[0].getProperty("jerk_travel", "value")
        accel_reset_x = mycura.getProperty("machine_max_acceleration_x", "value")
        accel_reset_y = mycura.getProperty("machine_max_acceleration_y", "value")

        if int(accel_print) >= int(accel_travel):
            accel_old = accel_print
        else:
            accel_old = accel_travel
        if accel_old > accel_reset_x: accel_reset_x = accel_old
        if accel_old > accel_reset_y: accel_reset_y = accel_old

        jerk_travel = str(extruder[0].getProperty("jerk_travel", "value"))
        if int(jerk_print_old) >= int(jerk_travel_old):
            jerk_old = jerk_print_old
        else:
            jerk_old = jerk_travel_old

        #Set the new Accel and Jerk values---------------------------------------------------------
        x_accel = str(self.getSettingValueByKey("x_accel_limit"))
        y_accel = str(self.getSettingValueByKey("y_accel_limit"))
        x_jerk = int(self.getSettingValueByKey("x_jerk"))
        y_jerk = int(self.getSettingValueByKey("y_jerk"))
        if str(self.getSettingValueByKey("jerk_cmd")) == "reprap_flavor":
            jerk_cmd = "M566"
            x_jerk *= 60
            y_jerk *= 60
            jerk_old *= 60
        else:
            jerk_cmd = "M205"

        # Put the strings together-----------------------------------------------------------------
        m201_limit_new = f"M201 X{x_accel} Y{y_accel}"
        m201_limit_old = f"M201 X{round(accel_old)} Y{round(accel_old)}"
        m205_jerk_pattern = jerk_cmd + " X(\d*) Y(\d*)"
        m205_jerk_new = jerk_cmd + f" X{x_jerk} Y{y_jerk}"
        m205_jerk_old = jerk_cmd + f" X{jerk_old} Y{jerk_old}"

        #Get the indexes of the start and end layers for all-at-once ------------------------------
        start_list = []
        end_list = []
        jerk_end_list = []
        if type_of_change == 'immediate_change':
            start_layer = int(self.getSettingValueByKey("start_layer"))-1
            end_layer = int(self.getSettingValueByKey("end_layer"))
        else:
            start_layer = int(self.getSettingValueByKey("gradient_start_layer"))-1
            end_layer = int(self.getSettingValueByKey("gradient_end_layer"))
        start_index = 2
        end_index = len(data)-2
        for num in range(2,len(data)-1):
            if ";LAYER:" + str(start_layer) + "\n" in data[num]:
                start_index = num
                break
        if int(end_layer) > 0:
            for num in range(3,len(data)-1):
                try:
                    if ";LAYER:" + str(end_layer) + "\n" in data[num]:
                        end_index = num
                        break
                except:
                    end_index = len(data)-2
        start_list.append(start_index)
        end_list.append(end_index)
        if end_layer > -1 and type_of_change == "immediate_change":
            jerk_end_list.append(end_index)
        else:
            jerk_end_list.append(len(data)-1)

        #Get the indexes of the start and end layers if in one-at-a-time mode----------------------
        if print_sequence == "one_at_a_time":
            start_list = []
            end_list = []
            jerk_end_list = []
            # Starts
            for num in range(start_index, len(data)):
                if ";LAYER:" + str(start_layer) + "\n" in data[num]:
                    start_list.append(num)
            # End and Jerk end
            for num in range(start_index + 1, len(data)):
                if end_layer > -1:
                    if ";LAYER:" + str(end_layer) + "\n" in data[num]:
                        end_list.append(num)
                if end_layer == -1:
                    if ";LAYER:0" in data[num]:
                        end_list.append(num)
                if ";LAYER:0" in data[num]:
                    jerk_end_list.append(num)
            end_list.append(len(data)-1)
            jerk_end_list.append(len(data)-1)

        # If 'immediate_change' Add the Accel limit and new Jerk at start layer--------------------
        if type_of_change == "immediate_change":
            for st_index in range(0,len(start_list)):
                layer = data[start_list[st_index]]
                lines = layer.split("\n")
                for index, line in enumerate(lines):
                    if lines[index].startswith(";LAYER:"):
                        lines.insert(index + 1,m201_limit_new)
                        if self.getSettingValueByKey("jerk_enable"):
                            lines.insert(index + 2,m205_jerk_new)
                        data[start_list[st_index]] = "\n".join(lines)
                # Reset at the End layer-----------------------------------------------------------
                layer_e = data[end_list[st_index]]
                lines_e = layer_e.split("\n")
                for index, line in enumerate(lines_e):
                    if lines_e[index].startswith(";LAYER:"):
                        lines_e.insert(index + 1,m201_limit_old)
                        if self.getSettingValueByKey("jerk_enable"):
                            lines_e.insert(index + 2,m205_jerk_old)
                        data[end_list[st_index]] = "\n".join(lines_e)
                #Alter any existing jerk lines to the End Layer------------------------------------
                for num in range(start_list[st_index],end_list[st_index],1):
                    layer_j = data[num]
                    lines_j = layer_j.split("\n")
                    for index, line in enumerate(lines_j):
                        if line.startswith("M205") or line.startswith("M566"):
                            lines_j[index] = re.sub(m205_jerk_pattern, m205_jerk_new, line)
                    data[num] = "\n".join(lines_j)
            # If print sequence is One at a Time then reset at every Layer:0-----------------------
            if print_sequence == "one_at_a_time":
                for num in range(start_index + 1, len(data)-1):
                    if ";LAYER:0\n" in data[num]:
                        lines = data[num].split("\n")
                        # This prevents a double entry---------------------------------------------
                        if not lines[1].startswith("M201"):
                            lines.insert(1,m201_limit_old)
                        data[num] = "\n".join(lines)
            # At the end of the print reset Accel and Jerk to defaults-----------------------------
            data[len(data)-1] = re.sub(";End of Gcode", f"M201 X{accel_reset_x} Y{accel_reset_y}\n{m205_jerk_old}\n;End of Gcode", data[len(data)-1])
            return data
            
        # Gradual Accel change---------------------------------------------------------------------
        elif type_of_change == "gradual_change":
            for st_index in range(0,len(start_list)):
                layer_spread = end_list[st_index] - start_list[st_index]
                if accel_old >= int(x_accel):
                    x_accel_hyst = (accel_old - int(x_accel)) / layer_spread
                else:
                    x_accel_hyst = (int(x_accel) - accel_old) / layer_spread
                if accel_old >= int(y_accel):
                    y_accel_hyst = (accel_old - int(y_accel)) / layer_spread
                else:
                    y_accel_hyst = (int(y_accel) - accel_old) / layer_spread
                if accel_old >= int(x_accel):
                    x_accel_start = round(round((accel_old - x_accel_hyst)/10)*10)
                else:
                    x_accel_start = round(round((x_accel_hyst + accel_old)/10)*10)
                if accel_old >= int(y_accel):
                    y_accel_start = round(round((accel_old - y_accel_hyst)/10)*10)
                else:
                    y_accel_start = round(round((y_accel_hyst + accel_old)/10)*10)
                m201_limit_new = f"M201 X{x_accel_start} Y{y_accel_start}"
                
                #Add Accel limit and new Jerk at start layer---------------------------------------
                layer = data[start_list[st_index]]
                lines = layer.split("\n")
                for index, line in enumerate(lines):
                    if lines[index].startswith(";LAYER:"):
                        lines.insert(index+1,m201_limit_new)
                        if self.getSettingValueByKey("jerk_enable"):
                            lines.insert(index+2,m205_jerk_new)
                        data[start_list[st_index]] = "\n".join(lines)
                for num in range(start_list[st_index] + 1, end_list[st_index],1):
                    layer = data[num]
                    lines = layer.split("\n")
                    if accel_old >= int(x_accel):
                        x_accel_start -= x_accel_hyst
                        if x_accel_start < int(x_accel): x_accel_start = int(x_accel)
                    else:
                        x_accel_start += x_accel_hyst
                        if x_accel_start > int(x_accel): x_accel_start = int(x_accel)
                    if accel_old >= int(y_accel):
                        y_accel_start -= y_accel_hyst
                        if y_accel_start < int(y_accel): y_accel_start = int(y_accel)
                    else:
                        y_accel_start += y_accel_hyst
                        if y_accel_start > int(y_accel): y_accel_start = int(y_accel)
                    m201_limit_new = f"M201 X{(round(round(x_accel_start/10)*10))} Y{(round(round(y_accel_start/10)*10))}"
                    for index, line in enumerate(lines):
                        if line.startswith(";LAYER:"):
                            lines.insert(index+1, m201_limit_new)
                    data[num] = "\n".join(lines)
                #Alter any existing jerk lines-----------------------------------------------------
                if self.getSettingValueByKey("jerk_enable"):
                    for num in range(start_list[st_index],jerk_end_list[st_index],1):
                        layer = data[num]
                        lines = layer.split("\n")
                        for index, line in enumerate(lines):
                            if line.startswith("M205") or line.startswith("M566"):
                                lines[index] = re.sub(m205_jerk_pattern, m205_jerk_new, line)
                        data[num] = "\n".join(lines)
            # Reset the Accel at the start of each model-------------------------------------------
            if print_sequence == "one_at_a_time":
                for num in range(start_index + 1, len(data)-1):
                    if ";LAYER:0\n" in data[num]:
                        lines = data[num].split("\n")
                        if not lines[1].startswith("M201"):
                            lines.insert(1,m201_limit_old)
                        data[num] = "\n".join(lines)
            # At the end of the print reset Accel and Jerk to defaults-----------------------------
            data[len(data)-1] = re.sub(";End of Gcode", f"M201 X{accel_reset_x} Y{accel_reset_y}\n{m205_jerk_old}\n;End of Gcode", data[len(data)-1])
            return data