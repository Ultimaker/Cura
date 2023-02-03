# January 2023 by GregValiant (Greg Foresi) with help from 5axes.
#Functions:
#    Remove all existing M106 lines from the file.
#    Enter new M106 lines "By Layer" or "By Feature" (at ;TYPE:WALL-OUTER, etc.).
#    A Starting layer and/or an Ending layer can be defined.
#    Fan speeds are scaled PWM (0 - 255) or RepRap (0 - 1) depending on {machine_scale_fan_speed_zero_to_one}.
#    The minimum fan speed is enforced at 15% to insure that fans start to spin.

from ..Script import Script
from UM.Logger import Logger
from UM.Application import Application
import re

class AddCoolingProfile(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Add a Cooling Profile",
            "key": "AddCoolingProfile",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "fan_layer_or_feature":
                {
                    "label": "Cooling Profile by:",
                    "description": "'By Layer' (gcode starts with 0) or 'By Feature' (Walls, Skins, Support, etc.).  A fan percentage of '0' turns the fan off.  A minimum Fan Percentage is enforced at 15% when the fan is on.  If ''By Layer'' then the last layer entry will continue to the end of the Gcode",
                    "type": "enum",
                    "options": {
                        "by_layer": "Layer Numbers",
                        "by_feature": "Feature Type"},
                    "default_value": "by_layer"
                },
                "fan_start_layer":
                {
                    "label": "Starting Layer",
                    "description": "Layer to start the insertion at.",
                    "type": "int",
                    "default_value": 5,
                    "minimum_value": 0,
                    "minimum_value_warning": 0,
                    "enabled": "fan_layer_or_feature == 'by_feature'"
                },
                "fan_end_layer":
                {
                    "label": "Ending Layer",
                    "description": "Layer to complete the insertion at.  Enter -1 for the entire file or enter a layer number.  Insertions will stop at the END of this layer.  If you set an End Layer then you must set the Final % that will finish the file",
                    "type": "str",
                    "default_value": -1,
                    "minimum_value": -1,
                    "enabled": "fan_layer_or_feature == 'by_feature'"
                },
                "fan_1st":
                {
                    "label": "Layer/Percent #1",
                    "description": "Enter as: 'LAYER / Percent' Ex: 57/100 with the layer first, then a '/' to delimit, and then the fan percentage.",
                    "type": "str",
                    "default_value": "5/30",
                    "enabled": "fan_layer_or_feature == 'by_layer'"
                },
                "fan_2nd":
                {
                    "label": "Layer/Percent #2",
                    "description": "Enter as: 'LAYER / Percent' Ex: 57/100 with the layer first, then a '/' to delimit, and then the fan percentage.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "fan_layer_or_feature == 'by_layer'"
                },
                "fan_3rd":
                {
                    "label": "Layer/Percent #3",
                    "description": "Enter as: 'LAYER / Percent' Ex: 57/100 with the layer first, then a '/' to delimit, and then the fan percentage.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "fan_layer_or_feature == 'by_layer'"
                },
                "fan_4th":
                {
                    "label": "Layer/Percent #4",
                    "description": "Enter as: 'LAYER / Percent' Ex: 57/100 with the layer first, then a '/' to delimit, and then the fan percentage.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "fan_layer_or_feature == 'by_layer'"
                },
                "fan_5th":
                {
                    "label": "Layer/Percent #5",
                    "description": "Enter as: 'LAYER / Percent' Ex: 57/100 with the layer first, then a '/' to delimit, and then the fan percentage.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "fan_layer_or_feature == 'by_layer'"
                },
                "fan_6th":
                {
                    "label": "Layer/Percent #6",
                    "description": "Enter as: 'LAYER / Percent' Ex: 57/100 with the layer first, then a '/' to delimit, and then the fan percentage.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "fan_layer_or_feature == 'by_layer'"
                },
                "fan_7th":
                {
                    "label": "Layer/Percent #7",
                    "description": "Enter as: 'LAYER / Percent' Ex: 57/100 with the layer first, then a '/' to delimit, and then the fan percentage.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "fan_layer_or_feature == 'by_layer'"
                },
                "fan_8th":
                {
                    "label": "Layer/Percent #8",
                    "description": "Enter as: 'LAYER / Percent' Ex: 57/100 with the layer first, then a '/' to delimit, and then the fan percentage.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "fan_layer_or_feature == 'by_layer'"
                },
                "fan_9th":
                {
                    "label": "Layer/Percent #9",
                    "description": "Enter as: 'LAYER / Percent' Ex: 57/100 with the layer first, then a '/' to delimit, and then the fan percentage.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "fan_layer_or_feature == 'by_layer'"
                },
                "fan_10th":
                {
                    "label": "Layer/Percent #10",
                    "description": "Enter as: 'LAYER / Percent' Ex: 57/100 with the layer first, then a '/' to delimit, and then the fan percentage.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "fan_layer_or_feature == 'by_layer'"
                },
                "fan_11th":
                {
                    "label": "Layer/Percent #11",
                    "description": "Enter as: 'LAYER / Percent' Ex: 57/100 with the layer first, then a '/' to delimit, and then the fan percentage.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "fan_layer_or_feature == 'by_layer'"
                },
                "fan_12th":
                {
                    "label": "Layer/Percent #12",
                    "description": "Enter as: 'LAYER / Percent' Ex: 57/100 with the layer first, then a '/' to delimit, and then the fan percentage.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "fan_layer_or_feature == 'by_layer'"
                },
                "fan_13th":
                {
                    "label": "Layer/Percent #13",
                    "description": "Enter as: 'LAYER / Percent' Ex: 57/100 with the layer first, then a '/' to delimit, and then the fan percentage.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "fan_layer_or_feature == 'by_layer'"
                },
                "fan_14th":
                {
                    "label": "Layer/Percent #14",
                    "description": "Enter as: 'LAYER / Percent' Ex: 57/100 with the layer first, then a '/' to delimit, and then the fan percentage.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "fan_layer_or_feature == 'by_layer'"
                },
                "fan_15th":
                {
                    "label": "Layer/Percent #15",
                    "description": "Enter as: 'LAYER / Percent' Ex: 57/100 with the layer first, then a '/' to delimit, and then the fan percentage.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "fan_layer_or_feature == 'by_layer'"
                },
                "fan_16th":
                {
                    "label": "Layer/Percent #16",
                    "description": "Enter as: 'LAYER / Percent' Ex: 57/100 with the layer first, then a '/' to delimit, and then the fan percentage.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "fan_layer_or_feature == 'by_layer'"
                },
                "fan_skirt":
                {
                    "label": "Skirt/Brim %",
                    "description": "Enter the fan percentage for skirt/brim.",
                    "type": "int",
                    "default_value": 0,
                    "minimum_value": 0,
                    "maximum_value": 100,
                    "enabled": "fan_layer_or_feature == 'by_feature'"
                },
                "fan_wall_inner":
                {
                    "label": "Inner Walls %",
                    "description": "Enter the fan percentage for the Wall-Inner.",
                    "type": "int",
                    "default_value": 35,
                    "minimum_value": 0,
                    "maximum_value": 100,
                    "enabled": "fan_layer_or_feature == 'by_feature'"
                },
                "fan_wall_outer":
                {
                    "label": "Outer Walls %",
                    "description": "Enter the fan percentage for the Wall-Outer.",
                    "type": "int",
                    "default_value": 75,
                    "minimum_value": 0,
                    "maximum_value": 100,
                    "enabled": "fan_layer_or_feature == 'by_feature'"
                },
                "fan_fill":
                {
                    "label": "Infill %",
                    "description": "Enter the fan percentage for the Infill.",
                    "type": "int",
                    "default_value": 35,
                    "minimum_value": 0,
                    "maximum_value": 100,
                    "enabled": "fan_layer_or_feature == 'by_feature'"
                },
                "fan_skin":
                {
                    "label": "Top/Bottom (Skin) %",
                    "description": "Enter the fan percentage for the Skins.",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": 0,
                    "maximum_value": 100,
                    "enabled": "fan_layer_or_feature == 'by_feature'"
                },
                "fan_support":
                {
                    "label": "Support %",
                    "description": "Enter the fan percentage for the Supports.",
                    "type": "int",
                    "default_value": 35,
                    "minimum_value": 0,
                    "maximum_value": 100,
                    "enabled": "fan_layer_or_feature == 'by_feature'"
                },
                "fan_support_interface":
                {
                    "label": "Support Interface %",
                    "description": "Enter the fan percentage for the Support Interface.",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": 0,
                    "maximum_value": 100,
                    "enabled": "fan_layer_or_feature == 'by_feature'"
                },
                "fan_prime_tower":
                {
                    "label": "Prime Tower %",
                    "description": "Enter the fan percentage for the Prime Tower.",
                    "type": "int",
                    "default_value": 35,
                    "minimum_value": 0,
                    "maximum_value": 100,
                    "enabled": "fan_layer_or_feature == 'by_feature'"
                },
                "fan_bridge":
                {
                    "label": "Bridge %",
                    "description": "Enter the fan percentage for the Bridges.",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": 0,
                    "maximum_value": 100,
                    "enabled": "fan_layer_or_feature == 'by_feature'"
                },
                "fan_combing":
                {
                    "label": "Fan 'OFF' during Combing:",
                    "description": "When checked will set the fan to 0% for end-of-layer combing moves. When un-checked the fan speed during combing is whatever the previous speed is set to.",
                    "type": "bool",
                    "enabled": "fan_layer_or_feature == 'by_feature'",
                    "default_value": true
                },
                "fan_feature_final":
                {
                    "label": "Final %",
                    "description": "If you choose an 'End Layer' then this is the fan speed that will carry through to the end of the gcode file.  It will go into effect at the 'END' of your end layer.",
                    "type": "int",
                    "default_value": 35,
                    "minimum_value": 0,
                    "maximum_value": 100,
                    "enabled": "(int(fan_end_layer) != -1) and (fan_layer_or_feature == 'by_feature')"
                }
            }
        }"""
#Initialize variables
    def execute(self, data):
        fan_1st_l = "0"; fan_1st_p = "0"; fan_2nd_l = "0"; fan_2nd_p = "0"
        fan_3rd_l = "0"; fan_3rd_p = "0"; fan_4th_l = "0"; fan_4th_p = "0"
        fan_5th_l = "0"; fan_5th_p = "0"; fan_6th_l = "0"; fan_6th_p = "0"
        fan_7th_l = "0"; fan_7th_p = "0"; fan_8th_l = "0"; fan_8th_p = "0"
        fan_9th_l = "0"; fan_9th_p = "0"; fan_10th_l = "0"; fan_10th_p = "0"
        fan_11th_l = "0"; fan_11th_p = "0"; fan_12th_l = "0"; fan_12th_p = "0"
        fan_13th_l = "0"; fan_13th_p = "0"; fan_14th_l = "0"; fan_14th_p = "0"
        fan_15th_l = "0"; fan_15th_p = "0"; fan_16th_l = "0"; fan_16th_p = "0"
#Get the {machine_scale_fan_speed_zero_to_one} setting from Cura.
        fan_mode = True
        extrud = Application.getInstance().getGlobalContainerStack().extruderList 
        fan_mode = not bool(extrud[0].getProperty("machine_scale_fan_speed_zero_to_one", "value"))
#Initialize the fan command list.
        fan_array = []
        for q in range(0,32,1):
            fan_array.append("mt")
#Assign the variable values if "By Layer".
        by_layer_or_feature = self.getSettingValueByKey("fan_layer_or_feature")
        if  by_layer_or_feature == "by_layer":
            fan_1st = self.getSettingValueByKey("fan_1st")
            if "/" in fan_1st:
                fan_array[0] = check_line.line_checker(fan_1st, "l", fan_mode)
                fan_array[1] = check_line.line_checker(fan_1st, "p", fan_mode)
            else:
                fan_array[0] = "999999999"
                fan_array[1] = "M106 S0"

            fan_2nd = self.getSettingValueByKey("fan_2nd")
            if "/" in fan_2nd:
                fan_array[2] = check_line.line_checker(fan_2nd, "l", fan_mode)
                fan_array[3] = check_line.line_checker(fan_2nd, "p", fan_mode)
            else:
                fan_array[2] = "999999999"
                fan_array[3] = "M106 S0"

            fan_3rd = self.getSettingValueByKey("fan_3rd")
            if "/" in fan_3rd:
                fan_array[4] = check_line.line_checker(fan_3rd, "l", fan_mode)
                fan_array[5] = check_line.line_checker(fan_3rd, "p", fan_mode)
            else:
                fan_array[4] = "999999999"
                fan_array[5] = "M106 S0"

            fan_4th = self.getSettingValueByKey("fan_4th")
            if "/" in fan_4th:
                fan_array[6] = check_line.line_checker(fan_4th, "l", fan_mode)
                fan_array[7] = check_line.line_checker(fan_4th, "p", fan_mode)
            else:
                fan_array[6] = "999999999"
                fan_array[7] = "M106 S0"

            fan_5th = self.getSettingValueByKey("fan_5th")
            if "/" in fan_5th:
                fan_array[8] = check_line.line_checker(fan_5th, "l", fan_mode)
                fan_array[9] = check_line.line_checker(fan_5th, "p", fan_mode)
            else:
                fan_array[8] = "999999999"
                fan_array[9] = "M106 S0"

            fan_6th = self.getSettingValueByKey("fan_6th")
            if "/" in fan_6th:
                fan_array[10] = check_line.line_checker(fan_6th, "l", fan_mode)
                fan_array[11] = check_line.line_checker(fan_6th, "p", fan_mode)
            else:
                fan_array[10] = "999999999"
                fan_array[11] = "M106 S0"

            fan_7th = self.getSettingValueByKey("fan_7th")
            if "/" in fan_7th:
                fan_array[12] = check_line.line_checker(fan_7th, "l", fan_mode)
                fan_array[13] = check_line.line_checker(fan_7th, "p", fan_mode)
            else:
                fan_array[12] = "999999999"
                fan_array[13] = "M106 S0"

            fan_8th = self.getSettingValueByKey("fan_8th")
            if "/" in fan_8th:
                fan_array[14] = check_line.line_checker(fan_8th, "l", fan_mode)
                fan_array[15] = check_line.line_checker(fan_8th, "p", fan_mode)
            else:
                fan_array[14] = "999999999"
                fan_array[15] = "M106 S0"

            fan_9th = self.getSettingValueByKey("fan_9th")
            if "/" in fan_9th:
                fan_array[16] = check_line.line_checker(fan_9th, "l", fan_mode)
                fan_array[17] = check_line.line_checker(fan_9th, "p", fan_mode)
            else:
                fan_array[16] = "999999999"
                fan_array[17] = "M106 S0"

            fan_10th = self.getSettingValueByKey("fan_10th")
            if "/" in fan_10th:
                fan_array[18] = check_line.line_checker(fan_10th, "l", fan_mode)
                fan_array[19] = check_line.line_checker(fan_10th, "p", fan_mode)
            else:
                fan_array[18] = "999999999"
                fan_array[19] = "M106 S0"

            fan_11th = self.getSettingValueByKey("fan_11th")
            if "/" in fan_11th:
                fan_array[20] = check_line.line_checker(fan_11th, "l", fan_mode)
                fan_array[21] = check_line.line_checker(fan_11th, "p", fan_mode)
            else:
                fan_array[20] = "999999999"
                fan_array[21] = "M106 S0"

            fan_12th = self.getSettingValueByKey("fan_12th")
            if "/" in fan_12th:
                fan_array[22] = check_line.line_checker(fan_12th, "l", fan_mode)
                fan_array[23] = check_line.line_checker(fan_12th, "p", fan_mode)
            else:
                fan_array[22] = "999999999"
                fan_array[23] = "M106 S0"

            fan_13th = self.getSettingValueByKey("fan_13th")
            if "/" in fan_13th:
                fan_array[24] = check_line.line_checker(fan_13th, "l", fan_mode)
                fan_array[25] = check_line.line_checker(fan_13th, "p", fan_mode)
            else:
                fan_array[24] = "999999999"
                fan_array[25] = "M106 S0"

            fan_14th = self.getSettingValueByKey("fan_14th")
            if "/" in fan_14th:
                fan_array[26] = check_line.line_checker(fan_14th, "l", fan_mode)
                fan_array[27] = check_line.line_checker(fan_14th, "p", fan_mode)
            else:
                fan_array[26] = "999999999"
                fan_array[27] = "M106 S0"

            fan_15th = self.getSettingValueByKey("fan_15th")
            if "/" in fan_15th:
                fan_array[28] = check_line.line_checker(fan_15th, "l", fan_mode)
                fan_array[29] = check_line.line_checker(fan_15th, "p", fan_mode)
            else:
                fan_array[28] = "999999999"
                fan_array[29] = "M106 S0"

            fan_16th = self.getSettingValueByKey("fan_16th")
            if "/" in fan_16th:
                fan_array[30] = check_line.line_checker(fan_16th, "l", fan_mode)
                fan_array[31] = check_line.line_checker(fan_16th, "p", fan_mode)
            else:
                fan_array[30] = "999999999"
                fan_array[31] = "M106 S0"
#Assign the variable values if "By Feature".
        elif by_layer_or_feature == "by_feature":    #Get the variables for the feature speeds and the start and the end layers
            the_start_layer = self.getSettingValueByKey("fan_start_layer")
            the_end_layer = self.getSettingValueByKey("fan_end_layer")
            fan_sp_skirt = check_feature.feat_checker(self.getSettingValueByKey("fan_skirt"), fan_mode)
            fan_sp_wall_inner = check_feature.feat_checker(self.getSettingValueByKey("fan_wall_inner"), fan_mode)
            fan_sp_wall_outer = check_feature.feat_checker(self.getSettingValueByKey("fan_wall_outer"), fan_mode)
            fan_sp_fill = check_feature.feat_checker(self.getSettingValueByKey("fan_fill"), fan_mode)
            fan_sp_skin = check_feature.feat_checker(self.getSettingValueByKey("fan_skin"), fan_mode)
            fan_sp_support = check_feature.feat_checker(self.getSettingValueByKey("fan_support"), fan_mode)
            fan_sp_support_interface = check_feature.feat_checker(self.getSettingValueByKey("fan_support_interface"), fan_mode)
            fan_sp_prime_tower = check_feature.feat_checker(self.getSettingValueByKey("fan_support_interface"), fan_mode)
            fan_sp_bridge = check_feature.feat_checker(self.getSettingValueByKey("fan_bridge"), fan_mode)
            fan_sp_feature_final = check_feature.feat_checker(self.getSettingValueByKey("fan_bridge"), fan_mode)
            fan_combing = self.getSettingValueByKey("fan_combing")
            if int(the_end_layer) > int("-1") and by_layer_or_feature == "by_feature":
                the_end_is_enabled = True
            else:
                the_end_is_enabled = False
            if int(the_end_layer) == int("-1") or the_end_is_enabled == False:
                the_end_layer = "9999999999"
#Strip the existing M106 lines from the file up to the end of the last layer.
        layer = data[1]
        layer = layer + "M106 S0" + "\n" #fan off for the first layer.  This can be over-ridden in the layer/feature settings.
        data[1] = layer
        for l_index in range(2, len(data) - 1, 1):
            modified_data = ""
            layer = data[l_index]
            lines = layer.split("\n")
            for line in lines:
                if not (line.startswith("M106") or line.startswith("M107")):
                    modified_data += line + "\n"
            if modified_data.endswith("\n"): modified_data = modified_data[:-1]
            data[l_index] = modified_data

#The "By Layer" section
        layer_number = "0"
        if by_layer_or_feature == "by_layer":
            for l_index in range(2,len(data)-1,1):
                layer = data[l_index]
                fan_lines = layer.split("\n")
                for fan_line in fan_lines:
                    if ";LAYER:" in fan_line:
                        layer_number = str(fan_line.split(":")[1])
                        for num in range(0,31,2):
                            if layer_number == fan_array[num]:
                                layer = fan_array[num + 1] + "\n" + layer
                                data[l_index] = layer

#The "By Feature" section
        layer_number = "0"
        index = 1
        if by_layer_or_feature == "by_feature":
            for l_index in range(2,len(data)-1,1):
                modified_data = ""
                layer = data[l_index]
                lines = layer.split("\n")
                for line in lines:
                    modified_data += line + "\n"
                    if ";LAYER:" in line:
                        layer_number = str(line.split(":")[1])
                    if int(layer_number) >= int(the_start_layer) and int(layer_number) <= int(the_end_layer):
                        if ";TYPE:SKIRT" in line:
                            modified_data += fan_sp_skirt + "\n"
                        elif ";TYPE:WALL-INNER" in line:
                            modified_data += fan_sp_wall_inner + "\n"
                        elif ";TYPE:WALL-OUTER" in line:
                            modified_data += fan_sp_wall_outer + "\n"
                        elif ";TYPE:FILL" in line:
                            modified_data += fan_sp_fill + "\n"
                        elif ";TYPE:SKIN" in line:
                            modified_data += fan_sp_skin + "\n"
                        elif ";TYPE:SUPPORT" in line:
                            modified_data += fan_sp_support + "\n"
                        elif ";TYPE:SUPPORT-INTERFACE" in line:
                            modified_data += fan_sp_support_interface + "\n"
                        elif ";MESH:NONMESH" in line:
                            if fan_combing == True:
                                modified_data += "M106 S0" + "\n"
                        elif ";TYPE:PRIME-TOWER" in line:
                            modified_data += fan_sp_prime_tower + "\n"
                        elif line == ";BRIDGE":
                            modified_data += fan_sp_bridge + "\n"
                    if line == ";LAYER:" + str(int(the_end_layer) + 1)  and the_end_is_enabled == True:
                        modified_data += fan_sp_feature_final + "\n"
                if modified_data.endswith("\n"): modified_data = modified_data[0: - 1]
                data[l_index] = modified_data
        return data
        
class check_line():
    def line_checker(fan_string: str, ty_pe: str, fan_mode: bool) -> str:
        fan_string_l = str(fan_string.split("/")[0])
        try:
            if int(fan_string_l) <= 0: fan_string_l = "0"
            if fan_string_l == "": fan_string_l = "999999999"
        except ValueError:
            fan_string_l = "999999999"
        fan_string_p = str(fan_string.split("/")[1])
        if fan_string_p == "": fan_string_p = "0"
        try:
            if int(fan_string_p) < 0: fan_string_p = "0"
            if int(fan_string_p) > 100: fan_string_p = "100"
        except ValueError:
            fan_string_p = "0"
        if int(fan_string_p) < 15 and int(fan_string_p) != 0:
            fan_string_p = "15"
        fan_layer_line = str(fan_string_l)
        if fan_mode:
            fan_percent_line = "M106 S" + str(round(int(fan_string_p) * 2.55))
        else:
            fan_percent_line = "M106 S" + str(round(int(fan_string_p) / 100, 1))
        if ty_pe == "l":
            return str(fan_layer_line)
        elif ty_pe == "p":
            return str(fan_percent_line)

class check_feature():
    def feat_checker(fan_feat_string: str, fan_mode: bool) -> str:
        if fan_feat_string < 0: fan_feat_string = 0
        if fan_feat_string > 0 and fan_feat_string < 15: fan_feat_string = 15
        if fan_feat_string > 100: fan_feat_string = 100
        if fan_mode:
            fan_sp_feat = "M106 S" + str(round(fan_feat_string * 2.55))
        else:
            fan_sp_feat = "M106 S" + str(round(fan_feat_string / 100, 1))
        return fan_sp_feat
        