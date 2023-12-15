# January 2023 by GregValiant (Greg Foresi).
# Functions:
#    Remove all fan speed lines from the file.
#    Enter new M106 lines "By Layer" or "By Feature" (;TYPE:WALL-OUTER, etc.).
#    A Starting layer and/or an Ending layer can be defined.
#    Fan speeds are scaled PWM (0 - 255) or RepRap (0 - 1) depending on {machine_scale_fan_speed_zero_to_one}.
#    If the fan is on the minimum speed is 12%.
#    If multiple extruders have separate fan circuits the speeds are set at tool changes and conform to the layer or
#    feature setting.  There is support for up to 4 layer cooling fan circuits.
#    The option for whether or not to remove the existing M106 lines is added to allow multiple instances of this post-processor to be installed without the followup instances wiping out the insertions of previous instances.  1/3 of a file can be 'By Layer' and the second third 'By Feature', and end up with 'By Layer' again.
#    I am aware the script is long.  My design intent was to make it as full featured and "industrial strength" as I could.
#    My thanks to @5axes, @fieldOfView(@AHoeben), @Ghostkeeper, and @Torgeir.
#    9/14/23 added support for One-at-a-Time and removed the kick out code

from ..Script import Script
from UM.Application import Application
import re
from UM.Message import Message

class AddCoolingProfile(Script):

    def getSettingDataString(self):
        return """{
            "name": "Advanced Cooling Fan Control",
            "key": "AddCoolingProfile",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "fan_layer_or_feature":
                {
                    "label": "Cooling Control by:",
                    "description": "A fan percentage of ''0'' turns the fan off.  Minimum Fan is 12% (when on).  All layer entries are the Cura Preview number.  ''By Layer'': Enter as ''Layer#/Fan%'' (foreslash is the delimiter). Your final layer speed will continue to the end of the Gcode.  ''By Feature'': If you enable an 'End Layer' then the ''Final %'' is available and is the speed that will finish the file.  'By Feature' is better for large slow prints than it is for short fast prints.",
                    "type": "enum",
                    "options": {
                        "by_layer": "Layer Numbers",
                        "by_feature": "Feature Types"},
                    "default_value": "by_layer"
                },
                "delete_existing_m106":
                {
                    "label": "Remove M106 lines prior to inserting new.",
                    "description": "If you have 2 or more instances of 'Advanced Cooling Fan Control' running (to cool a portion of a print differently), then uncheck this box or the followup instances will remove all the lines inserted by the first instance.  Pay attention to the Start and Stop layers.  If you want to keep the Cura inserted lines up to the point where this post-processor will start making insertions, then un-check the box.",
                    "type": "bool",
                    "enabled": true,
                    "default_value": true
                },
                "feature_fan_start_layer":
                {
                    "label": "Starting Layer",
                    "description": "Layer to start the insertion at. Use the Cura preview numbers.  Changes will begin at the start of that layer.",
                    "type": "int",
                    "default_value": 5,
                    "minimum_value": 1,
                    "unit": "Lay#   ",
                    "enabled": "fan_layer_or_feature == 'by_feature'"
                },
                "feature_fan_end_layer":
                {
                    "label": "Ending Layer",
                    "description": "Layer to complete the insertion at.  Enter '-1' for the entire file or enter a layer number.  Insertions will stop at the END of this layer.  If you set an End Layer then you should set the Final % that will finish the file",
                    "type": "int",
                    "default_value": -1,
                    "minimum_value": -1,
                    "unit": "Lay#   ",
                    "enabled": "fan_layer_or_feature == 'by_feature'"
                },
                "layer_fan_1st":
                {
                    "label": "Layer/Percent #1",
                    "description": "Enter as: 'LAYER / Percent' Ex: 57/100 with the layer first, then a '/' to delimit, and then the fan percentage.",
                    "type": "str",
                    "default_value": "5/30",
                    "unit": "L#/%    ",
                    "enabled": "fan_layer_or_feature == 'by_layer'"
                },
                "layer_fan_2nd":
                {
                    "label": "Layer/Percent #2",
                    "description": "Enter as: 'LAYER / Percent' Ex: 57/100 with the layer first, then a '/' to delimit, and then the fan percentage.",
                    "type": "str",
                    "default_value": "",
                    "unit": "L#/%    ",
                    "enabled": "fan_layer_or_feature == 'by_layer'"
                },
                "layer_fan_3rd":
                {
                    "label": "Layer/Percent #3",
                    "description": "Enter as: 'LAYER / Percent' Ex: 57/100 with the layer first, then a '/' to delimit, and then the fan percentage.",
                    "type": "str",
                    "default_value": "",
                    "unit": "L#/%    ",
                    "enabled": "fan_layer_or_feature == 'by_layer'"
                },
                "layer_fan_4th":
                {
                    "label": "Layer/Percent #4",
                    "description": "Enter as: 'LAYER / Percent' Ex: 57/100 with the layer first, then a '/' to delimit, and then the fan percentage.",
                    "type": "str",
                    "default_value": "",
                    "unit": "L#/%    ",
                    "enabled": "fan_layer_or_feature == 'by_layer'"
                },
                "layer_fan_5th":
                {
                    "label": "Layer/Percent #5",
                    "description": "Enter as: 'LAYER / Percent' Ex: 57/100 with the layer first, then a '/' to delimit, and then the fan percentage.",
                    "type": "str",
                    "default_value": "",
                    "unit": "L#/%    ",
                    "enabled": "fan_layer_or_feature == 'by_layer'"
                },
                "layer_fan_6th":
                {
                    "label": "Layer/Percent #6",
                    "description": "Enter as: 'LAYER / Percent' Ex: 57/100 with the layer first, then a '/' to delimit, and then the fan percentage.",
                    "type": "str",
                    "default_value": "",
                    "unit": "L#/%    ",
                    "enabled": "fan_layer_or_feature == 'by_layer'"
                },
                "layer_fan_7th":
                {
                    "label": "Layer/Percent #7",
                    "description": "Enter as: 'LAYER / Percent' Ex: 57/100 with the layer first, then a '/' to delimit, and then the fan percentage.",
                    "type": "str",
                    "default_value": "",
                    "unit": "L#/%    ",
                    "enabled": "fan_layer_or_feature == 'by_layer'"
                },
                "layer_fan_8th":
                {
                    "label": "Layer/Percent #8",
                    "description": "Enter as: 'LAYER / Percent' Ex: 57/100 with the layer first, then a '/' to delimit, and then the fan percentage.",
                    "type": "str",
                    "default_value": "",
                    "unit": "L#/%    ",
                    "enabled": "fan_layer_or_feature == 'by_layer'"
                },
                "feature_fan_skirt":
                {
                    "label": "Skirt/Brim/Ooze Shield %",
                    "description": "Enter the fan percentage for skirt/brim.  If you are starting at a layer above 1 then this setting only affects Ooze Shields and from the Start layer up.",
                    "type": "int",
                    "default_value": 0,
                    "minimum_value": 0,
                    "maximum_value": 100,
                    "unit": "%    ",
                    "enabled": "fan_layer_or_feature == 'by_feature'"
                },
                "feature_fan_wall_inner":
                {
                    "label": "Inner Walls %",
                    "description": "Enter the fan percentage for the Wall-Inner.",
                    "type": "int",
                    "default_value": 35,
                    "minimum_value": 0,
                    "maximum_value": 100,
                    "unit": "%    ",
                    "enabled": "fan_layer_or_feature == 'by_feature'"
                },
                "feature_fan_wall_outer":
                {
                    "label": "Outer Walls %",
                    "description": "Enter the fan percentage for the Wall-Outer.",
                    "type": "int",
                    "default_value": 75,
                    "minimum_value": 0,
                    "maximum_value": 100,
                    "unit": "%    ",
                    "enabled": "fan_layer_or_feature == 'by_feature'"
                },
                "feature_fan_fill":
                {
                    "label": "Infill %",
                    "description": "Enter the fan percentage for the Infill.",
                    "type": "int",
                    "default_value": 35,
                    "minimum_value": 0,
                    "maximum_value": 100,
                    "unit": "%    ",
                    "enabled": "fan_layer_or_feature == 'by_feature'"
                },
                "feature_fan_skin":
                {
                    "label": "Top/Bottom (Skin) %",
                    "description": "Enter the fan percentage for the Skins.",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": 0,
                    "maximum_value": 100,
                    "unit": "%    ",
                    "enabled": "fan_layer_or_feature == 'by_feature'"
                },
                "feature_fan_support":
                {
                    "label": "Support %",
                    "description": "Enter the fan percentage for the Supports.",
                    "type": "int",
                    "default_value": 35,
                    "minimum_value": 0,
                    "maximum_value": 100,
                    "unit": "%    ",
                    "enabled": "fan_layer_or_feature == 'by_feature'"
                },
                "feature_fan_support_interface":
                {
                    "label": "Support Interface %",
                    "description": "Enter the fan percentage for the Support Interface.",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": 0,
                    "maximum_value": 100,
                    "unit": "%    ",
                    "enabled": "fan_layer_or_feature == 'by_feature'"
                },
                "feature_fan_prime_tower":
                {
                    "label": "Prime Tower %",
                    "description": "Enter the fan percentage for the Prime Tower (whether it's used or not).",
                    "type": "int",
                    "default_value": 35,
                    "minimum_value": 0,
                    "maximum_value": 100,
                    "unit": "%    ",
                    "enabled": "fan_layer_or_feature == 'by_feature'"
                },
                "feature_fan_bridge":
                {
                    "label": "Bridge %",
                    "description": "Enter the fan percentage for any Bridging (whether it's used on not).",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": 0,
                    "maximum_value": 100,
                    "unit": "%    ",
                    "enabled": "fan_layer_or_feature == 'by_feature'"
                },
                "feature_fan_combing":
                {
                    "label": "Fan 'OFF' during Combing:",
                    "description": "When checked will set the fan to 0% for combing moves over 5 lines long in the gcode. When un-checked the fan speed during combing is whatever the previous speed is set to.",
                    "type": "bool",
                    "enabled": "fan_layer_or_feature == 'by_feature'",
                    "default_value": true
                },
                "feature_fan_feature_final":
                {
                    "label": "Final %",
                    "description": "If you choose an 'End Layer' then this is the fan speed that will carry through to the end of the gcode file.  It will go into effect at the 'END' of your end layer.",
                    "type": "int",
                    "default_value": 35,
                    "minimum_value": 0,
                    "maximum_value": 100,
                    "unit": "%    ",
                    "enabled": "(int(feature_fan_end_layer) != -1) and (fan_layer_or_feature == 'by_feature')"
                },
                "fan_enable_raft":
                {
                    "label": "Enable Raft Cooling",
                    "description": "Enable the fan for the raft layers.  When enabled the Raft Fan Speed will continue until another Layer or Feature setting over-rides it.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": true
                },
                "fan_raft_percent":
                {
                    "label": "Raft Fan %:",
                    "description": "Enter the percentage for the Raft.",
                    "type": "int",
                    "default_value": 35,
                    "minimum_value": 0,
                    "maximum_value": 100,
                    "unit": "%    ",
                    "enabled": "fan_enable_raft"
                }
            }
        }"""

    def execute(self, data):
        #Initialize variables that are buried in if statements.
        t0_fan = " P0"; t1_fan = " P0"; t2_fan = " P0"; t3_fan = " P0"; is_multi_extr_print = True

        #Get some information from Cura-----------------------------------
        extruder = Application.getInstance().getGlobalContainerStack().extruderList

        #This will be true when fan scale is 0-255pwm and false when it's RepRap 0-1 (Cura 5.x)
        fan_mode = True

        #For 4.x versions that don't have the 0-1 option------------------
        try:
            fan_mode = not bool(extruder[0].getProperty("machine_scale_fan_speed_zero_to_one", "value"))
        except:
            pass
        bed_adhesion = (extruder[0].getProperty("adhesion_type", "value"))
        extruder_count = Application.getInstance().getGlobalContainerStack().getProperty("machine_extruder_count", "value")
        print_sequence = str(Application.getInstance().getGlobalContainerStack().getProperty("print_sequence", "value"))

        #Assign the fan numbers to the tools------------------------------
        if extruder_count == 1:
            is_multi_fan = False
            is_multi_extr_print = False
            if int((extruder[0].getProperty("machine_extruder_cooling_fan_number", "value"))) > 0:
                t0_fan = " P" + str((extruder[0].getProperty("machine_extruder_cooling_fan_number", "value")))
            else:
        #No P parameter if there is a single fan circuit------------------
                t0_fan = ""
        elif extruder_count > 1:
            is_multi_fan = True
            t0_fan = " P" + str((extruder[0].getProperty("machine_extruder_cooling_fan_number", "value")))
        if is_multi_fan:
            if extruder_count > 1: t1_fan = " P" + str((extruder[1].getProperty("machine_extruder_cooling_fan_number", "value")))
            if extruder_count > 2: t2_fan = " P" + str((extruder[2].getProperty("machine_extruder_cooling_fan_number", "value")))
            if extruder_count > 3: t3_fan = " P" + str((extruder[3].getProperty("machine_extruder_cooling_fan_number", "value")))

        #Initialize the fan_list with defaults----------------------------
        fan_list = []
        for q in range(0,8,1):
            fan_list.append(len(data))
            fan_list.append("M106 S0")

        #Assign the variable values if "By Layer"-------------------------
        by_layer_or_feature = self.getSettingValueByKey("fan_layer_or_feature")
        if  by_layer_or_feature == "by_layer":
            #By layer doesn't do any feature search
            feature_fan_combing = False

            #If there is no delimiter then ignore the line else put the settings in a list
            layer_fan_1st = self.getSettingValueByKey("layer_fan_1st")
            if "/" in layer_fan_1st:
                fan_list[0] = check_layer.layer_checker(layer_fan_1st, "l", fan_mode)
                fan_list[1] = check_layer.layer_checker(layer_fan_1st, "p", fan_mode)
            layer_fan_2nd = self.getSettingValueByKey("layer_fan_2nd")
            if "/" in layer_fan_2nd:
                fan_list[2] = check_layer.layer_checker(layer_fan_2nd, "l", fan_mode)
                fan_list[3] = check_layer.layer_checker(layer_fan_2nd, "p", fan_mode)
            layer_fan_3rd = self.getSettingValueByKey("layer_fan_3rd")
            if "/" in layer_fan_3rd:
                fan_list[4] = check_layer.layer_checker(layer_fan_3rd, "l", fan_mode)
                fan_list[5] = check_layer.layer_checker(layer_fan_3rd, "p", fan_mode)
            layer_fan_4th = self.getSettingValueByKey("layer_fan_4th")
            if "/" in layer_fan_4th:
                fan_list[6] = check_layer.layer_checker(layer_fan_4th, "l", fan_mode)
                fan_list[7] = check_layer.layer_checker(layer_fan_4th, "p", fan_mode)
            layer_fan_5th = self.getSettingValueByKey("layer_fan_5th")
            if "/" in layer_fan_5th:
                fan_list[8] = check_layer.layer_checker(layer_fan_5th, "l", fan_mode)
                fan_list[9] = check_layer.layer_checker(layer_fan_5th, "p", fan_mode)
            layer_fan_6th = self.getSettingValueByKey("layer_fan_6th")
            if "/" in layer_fan_6th:
                fan_list[10] = check_layer.layer_checker(layer_fan_6th, "l", fan_mode)
                fan_list[11] = check_layer.layer_checker(layer_fan_6th, "p", fan_mode)
            layer_fan_7th = self.getSettingValueByKey("layer_fan_7th")
            if "/" in layer_fan_7th:
                fan_list[12] = check_layer.layer_checker(layer_fan_7th, "l", fan_mode)
                fan_list[13] = check_layer.layer_checker(layer_fan_7th, "p", fan_mode)
            layer_fan_8th = self.getSettingValueByKey("layer_fan_8th")
            if "/" in layer_fan_8th:
                fan_list[14] = check_layer.layer_checker(layer_fan_8th, "l", fan_mode)
                fan_list[15] = check_layer.layer_checker(layer_fan_8th, "p", fan_mode)

        #Assign the variable values if "By Feature"-----------------------
        elif by_layer_or_feature == "by_feature":
            the_start_layer = self.getSettingValueByKey("feature_fan_start_layer") - 1
            the_end_layer = self.getSettingValueByKey("feature_fan_end_layer")
            try:
                if int(the_end_layer) != -1:
                    #Catch a possible input error.
                    if the_end_layer < the_start_layer:
                        the_end_layer = the_start_layer
            except:
            #If there is an input error default to the entire gcode file.
                the_end_layer = -1

            #Get the speed for each feature-------------------------------
            fan_sp_skirt = check_feature.feature_checker(self.getSettingValueByKey("feature_fan_skirt"), fan_mode)
            fan_sp_wall_inner = check_feature.feature_checker(self.getSettingValueByKey("feature_fan_wall_inner"), fan_mode)
            fan_sp_wall_outer = check_feature.feature_checker(self.getSettingValueByKey("feature_fan_wall_outer"), fan_mode)
            fan_sp_fill = check_feature.feature_checker(self.getSettingValueByKey("feature_fan_fill"), fan_mode)
            fan_sp_skin = check_feature.feature_checker(self.getSettingValueByKey("feature_fan_skin"), fan_mode)
            fan_sp_support = check_feature.feature_checker(self.getSettingValueByKey("feature_fan_support"), fan_mode)
            fan_sp_support_interface = check_feature.feature_checker(self.getSettingValueByKey("feature_fan_support_interface"), fan_mode)
            fan_sp_prime_tower = check_feature.feature_checker(self.getSettingValueByKey("feature_fan_prime_tower"), fan_mode)
            fan_sp_bridge = check_feature.feature_checker(self.getSettingValueByKey("feature_fan_bridge"), fan_mode)
            fan_sp_feature_final = check_feature.feature_checker(self.getSettingValueByKey("feature_fan_feature_final"), fan_mode)
            feature_fan_combing = self.getSettingValueByKey("feature_fan_combing")
            if the_end_layer > -1 and by_layer_or_feature == "by_feature":
                #Required so the final speed input can be determined------
                the_end_is_enabled = True
            else:
                #There is no ending layer so do the whole file------------
                the_end_is_enabled = False
            if the_end_layer == -1 or the_end_is_enabled == False:
                the_end_layer = len(data) + 2

        #Find the Layer0Index and the RaftIndex---------------------------
        raft_start_index = 0
        number_of_raft_layers = 0
        layer_0_index = 0
        #Catch the number of raft layers.
        for l_num in range(1,10,1):
            layer = data[l_num]
            if ";LAYER:-" in layer:
                number_of_raft_layers += 1
                if raft_start_index == 0:
                    raft_start_index = l_num
            if ";LAYER:0" in layer:
                layer_0_index = l_num
                break

        #Is this a single extruder print on a multi-extruder printer? - get the correct fan number for the extruder being used.
        if is_multi_fan:
            T0_used = False
            T1_used = False
            T2_used = False
            T3_used = False
            #Bypass the file header and ending gcode.
            for num in range(1,len(data)-1,1):
                lines = data[num]
                if "T0" in lines:
                    T0_used = True
                if "T1" in lines:
                    T1_used = True
                if "T2" in lines:
                    T2_used = True
                if "T3" in lines:
                    T3_used = True
            is_multi_extr_print = True if sum([T0_used, T1_used, T2_used, T3_used]) > 1 else False

            #On a multi-extruder printer and single extruder print find out which extruder starts the file.
            init_fan = t0_fan
            if not is_multi_extr_print:
                startup = data[1]
                lines = startup.split("\n")
                for line in lines:
                    if line == "T1":
                        t0_fan = t1_fan
                    elif line == "T2":
                        t0_fan = t2_fan
                    elif line == "T3":
                        t0_fan = t3_fan
            elif is_multi_extr_print:
            #On a multi-extruder printer and multi extruder print find out which extruder starts the file.
                startup = data[1]
                lines = startup.split("\n")
                for line in lines:
                    if line == "T0":
                        init_fan = t0_fan
                    elif line == "T1":
                        init_fan = t1_fan
                    elif line == "T2":
                        init_fan = t2_fan
                    elif line == "T3":
                        init_fan = t3_fan
        else:
            init_fan = ""
        #Assign the variable values if "Raft Enabled"---------------------
        raft_enabled = self.getSettingValueByKey("fan_enable_raft")
        if raft_enabled and bed_adhesion == "raft":
            fan_sp_raft = check_feature.feature_checker(self.getSettingValueByKey("fan_raft_percent"), fan_mode)
        else:
            fan_sp_raft = "M106 S0"

        #Start to alter the data.

        #Strip the existing M106 lines from the file up to the end of the last layer.  If a user wants to use more than one instance of this plugin then they won't want to erase the M106 lines that the preceding plugins inserted so 'delete_existing_m106' is an option.
        delete_existing_m106 = self.getSettingValueByKey("delete_existing_m106")
        if delete_existing_m106:
        #Start deleting from the beginning
            start_from = int(raft_start_index)
        else:
            if by_layer_or_feature == "by_layer":
                altered_start_layer = str(len(data))
                #The fan list layers don't need to be in ascending order.  Get the lowest.
                for num in range(0,15,2):
                    if int(fan_list[num]) < int(altered_start_layer):
                        altered_start_layer = int(fan_list[num])
            elif by_layer_or_feature == "by_feature":
                altered_start_layer = int(the_start_layer) - 1
            start_from = int(layer_0_index) + int(altered_start_layer)

        #Strip the M106 and M107 lines from the file----------------------
        for l_index in range(start_from, len(data) - 1, 1):
            data[l_index] = re.sub(re.compile("M106(\s\w\d*)\n"), "", data[l_index])
            data[l_index] = re.sub(re.compile("M107(\w*)\n"), "", data[l_index])

        #Deal with a raft and with One-At-A-Time--------------------------
        if raft_enabled and bed_adhesion == "raft":
            if print_sequence == "one_at_a_time":
                for r_index in range(2,len(data)-2,1):
                    lines = data[r_index].split("\n")
                    if not raft_enabled or bed_adhesion != "raft":
                        if ";LAYER:0" in data[r_index] or ";LAYER:-" in data[r_index]:
                            lines.insert(1, "M106 S0" + str(t0_fan))
                    if raft_enabled and bed_adhesion == "raft":
                        if ";LAYER:-" in data[r_index]:
                        #Turn the raft fan on-----------------------------
                            lines.insert(1, fan_sp_raft + str(t0_fan))
                        #Shut the raft fan off----------------------------
                        if ";LAYER:0" in data[r_index]:
                            lines.insert(1,"M106 S0" + str(t0_fan))
                    data[r_index] = "\n".join(lines)
            elif print_sequence == "all_at_once":
                layer = data[raft_start_index]
                lines = layer.split("\n")
                if ";LAYER:-" in layer:
                    #Turn the raft fan on
                    lines.insert(1, fan_sp_raft + str(init_fan))
                layer = "\n".join(lines)
                data[raft_start_index] = layer
                layer = data[layer_0_index]
                lines = layer.split("\n")
                #Shut the raft fan off
                lines.insert(1, "M106 S0" + str(init_fan))
                data[layer_0_index] = "\n".join(lines)
        else:
            for r_index in range(2,len(data)-2,1):
                lines = data[r_index].split("\n")
                if ";LAYER:0" in data[r_index] or ";LAYER:-" in data[r_index]:
                    if not "0" in fan_list:
                        lines.insert(1, "M106 S0" + str(t0_fan))
                data[r_index] = "\n".join(lines)

        #Turn off all fans at the end of data[1]--------------------------
        temp_startup = data[1].split("\n")
        temp_startup.insert(len(temp_startup)-2,"M106 S0" + str(t0_fan))
        #If there are multiple cooling fans shut them all off
        if is_multi_fan:
            if extruder_count > 1 and t1_fan != t0_fan: temp_startup.insert(len(temp_startup)-2,"M106 S0" + str(t1_fan))
            if extruder_count > 2 and t2_fan != t1_fan and t2_fan != t0_fan: temp_startup.insert(len(temp_startup)-2,"M106 S0" + str(t2_fan))
            if extruder_count > 3 and t3_fan != t2_fan and t3_fan != t1_fan and t3_fan != t0_fan: temp_startup.insert(len(temp_startup)-2,"M106 S0" + str(t3_fan))
        data[1] = "\n".join(temp_startup)

        #Add additional 'MESH:NONMESH' lines for travel moves over 5 lines long if 'feature_fan_combing' is True
        #The "MESH:NONMESH" line changed in Cura 5.3.0.  It changed back in 5.3.1.
        if feature_fan_combing:
            for layer_num in range(2,len(data)):
                layer = data[layer_num]
                data[layer_num] = re.sub(";MESH:NOMESH", ";MESH:NONMESH", layer)
            data = add_mesh_nonmesh.add_travel_comment(data, layer_0_index)

        #The Single Fan "By Layer" section--------------------------------
        if by_layer_or_feature == "by_layer" and not is_multi_fan:
            layer_number = "0"
            for l_index in range(layer_0_index,len(data)-1,1):
                layer = data[l_index]
                fan_lines = layer.split("\n")
                for fan_line in fan_lines:
                    if ";LAYER:" in fan_line:
                        layer_number = str(fan_line.split(":")[1])
                        #If there is a match for the current layer number make the insertion.
                        for num in range(0,15,2):
                            if int(layer_number) == int(fan_list[num]):
                                layer = layer.replace(fan_lines[0],fan_lines[0] + "\n" + fan_list[num + 1] + str(t0_fan))
                                data[l_index] = layer
            return data

        #The Multi-Fan "By Layer" section---------------------------------
        if by_layer_or_feature == "by_layer" and is_multi_fan:
            layer_number = "0"
            current_fan_speed = "0"
            prev_fan = str(t0_fan)
            this_fan = str(t0_fan)
            start_index = str(len(data))
            for num in range(0,15,2):
            #The fan_list may not be in ascending order.  Get the lowest layer number
                if int(fan_list[num]) < int(start_index):
                    start_index = str(fan_list[num])
            #Move the start point if delete_existing_m106 is false
            start_index = int(start_index) + int(layer_0_index)
            #Track the tool number
            for num in range(1,start_index,1):
                layer = data[num]
                lines = layer.split("\n")
                for line in lines:
                    if line == "T0":
                        prev_fan = this_fan
                        this_fan = t0_fan
                    elif line == "T1":
                        prev_fan = this_fan
                        this_fan = t1_fan
                    elif line == "T2":
                        prev_fan = this_fan
                        this_fan = t2_fan
                    elif line == "T3":
                        prev_fan = this_fan
                        this_fan = t3_fan
            for l_index in range(start_index,len(data)-1,1):
                modified_data = ""
                layer = data[l_index]
                fan_lines = layer.split("\n")
                for fan_line in fan_lines:
                    #Prepare to shut down the previous fan and start the next one.
                    if fan_line.startswith("T"):
                        if fan_line == "T0": this_fan = str(t0_fan)
                        if fan_line == "T1": this_fan = str(t1_fan)
                        if fan_line == "T2": this_fan = str(t2_fan)
                        if fan_line == "T3": this_fan = str(t3_fan)
                        modified_data += "M106 S0" + prev_fan + "\n"
                        modified_data += fan_line + "\n"
                        modified_data += "M106 S" + str(current_fan_speed) + this_fan + "\n"
                        prev_fan = this_fan
                    elif ";LAYER:" in fan_line:
                        modified_data += fan_line + "\n"
                        layer_number = str(fan_line.split(":")[1])
                        for num in range(0,15,2):
                            if layer_number == str(fan_list[num]):
                                modified_data += fan_list[num + 1] + this_fan + "\n"
                                current_fan_speed = str(fan_list[num + 1].split("S")[1])
                                current_fan_speed = str(current_fan_speed.split(" ")[0]) #Just in case
                    else:
                        modified_data += fan_line + "\n"
                if modified_data.endswith("\n"): modified_data = modified_data[0:-1]
                data[l_index] = modified_data
            return data

        #The Single Fan "By Feature" section------------------------------
        if by_layer_or_feature == "by_feature" and (not is_multi_fan or not is_multi_extr_print):
            layer_number = "0"
            index = 1
            #Start with layer:0
            for l_index in range(layer_0_index,len(data)-1,1):
                modified_data = ""
                layer = data[l_index]
                lines = layer.split("\n")
                for line in lines:
                    if ";LAYER:" in line:
                        layer_number = str(line.split(":")[1])
                    if int(layer_number) >= int(the_start_layer) and int(layer_number) < int(the_end_layer)-1:
                        if ";TYPE:SKIRT" in line:
                            modified_data += fan_sp_skirt + t0_fan + "\n"
                        elif ";TYPE:WALL-INNER" in line:
                            modified_data += fan_sp_wall_inner + t0_fan + "\n"
                        elif ";TYPE:WALL-OUTER" in line:
                            modified_data += fan_sp_wall_outer + t0_fan + "\n"
                        elif ";TYPE:FILL" in line:
                            modified_data += fan_sp_fill + t0_fan + "\n"
                        elif ";TYPE:SKIN" in line:
                            modified_data += fan_sp_skin + t0_fan + "\n"
                        elif line == ";TYPE:SUPPORT":
                            modified_data += fan_sp_support + t0_fan + "\n"
                        elif ";TYPE:SUPPORT-INTERFACE" in line:
                            modified_data += fan_sp_support_interface + t0_fan + "\n"
                        elif ";MESH:NOMESH" in line or ";MESH:NONMESH" in line:  #compatibility with 5.3.0 'NOMESH'
                            if feature_fan_combing == True:
                                modified_data += "M106 S0" + t0_fan + "\n"
                        elif ";TYPE:PRIME-TOWER" in line:
                            modified_data += fan_sp_prime_tower + t0_fan + "\n"
                        elif line == ";BRIDGE":
                            modified_data += fan_sp_bridge + t0_fan + "\n"
                    modified_data += line + "\n"
                    #If an End Layer is defined then insert the Final Speed
                    if line == ";LAYER:" + str(the_end_layer)  and the_end_is_enabled == True:
                        modified_data += fan_sp_feature_final + t0_fan + "\n"
                if modified_data.endswith("\n"): modified_data = modified_data[0: - 1]
                data[l_index] = modified_data
            return data

        #The Multi Fan "By Feature" section-------------------------------
        if by_layer_or_feature == "by_feature" and is_multi_fan:
            layer_number = "0"
            start_index = 1
            prev_fan = t0_fan
            this_fan = t0_fan
            modified_data = ""
            current_fan_speed = "0"
            for my_index in range(1, len(data) - 1, 1):
                layer = data[my_index]
                if ";LAYER:" + str(the_start_layer) + "\n" in layer:
                    start_index = int(my_index) - 1
                    break
            #Track the previous tool changes
            for num in range(1,start_index,1):
                layer = data[num]
                lines = layer.split("\n")
                for line in lines:
                    if line == "T0":
                        prev_fan = this_fan
                        this_fan = t0_fan
                    elif line == "T1":
                        prev_fan = this_fan
                        this_fan = t1_fan
                    elif line == "T2":
                        prev_fan = this_fan
                        this_fan = t2_fan
                    elif line == "T3":
                        prev_fan = this_fan
                        this_fan = t3_fan
            #Get the current tool.
            for l_index in range(start_index,start_index + 1,1):
                layer = data[l_index]
                lines = layer.split("\n")
                for line in lines:
                    if line.startswith("T"):
                        if line == "T0": this_fan = t0_fan
                        if line == "T1": this_fan = t1_fan
                        if line == "T2": this_fan = t2_fan
                        if line == "T3": this_fan = t3_fan
                        prev_fan = this_fan

            #Start to make insertions-------------------------------------
            for l_index in range(start_index+1,len(data)-1,1):
                layer = data[l_index]
                lines = layer.split("\n")
                for line in lines:
                    if line.startswith("T"):
                        if line == "T0": this_fan = t0_fan
                        if line == "T1": this_fan = t1_fan
                        if line == "T2": this_fan = t2_fan
                        if line == "T3": this_fan = t3_fan
                        #Turn off the prev fan
                        modified_data += "M106 S0" + prev_fan + "\n"
                        modified_data += line + "\n"
                        #Turn on the current fan
                        modified_data += "M106 S" + str(current_fan_speed) + this_fan + "\n"
                        prev_fan = this_fan
                    if ";LAYER:" in line:
                        layer_number = str(line.split(":")[1])
                        modified_data += line + "\n"
                    if int(layer_number) >= int(the_start_layer): # Problem with oneatatime < start
                        if ";TYPE:SKIRT" in line:
                            modified_data += line + "\n"
                            modified_data += fan_sp_skirt + this_fan + "\n"
                            current_fan_speed = str(fan_sp_skirt.split("S")[1])
                        elif ";TYPE:WALL-INNER" in line:
                            modified_data += line + "\n"
                            modified_data += fan_sp_wall_inner + this_fan + "\n"
                            current_fan_speed = str(fan_sp_wall_inner.split("S")[1])
                        elif ";TYPE:WALL-OUTER" in line:
                            modified_data += line + "\n"
                            modified_data += fan_sp_wall_outer + this_fan + "\n"
                            current_fan_speed = str(fan_sp_wall_outer.split("S")[1])
                        elif ";TYPE:FILL" in line:
                            modified_data += line + "\n"
                            modified_data += fan_sp_fill + this_fan + "\n"
                            current_fan_speed = str(fan_sp_fill.split("S")[1])
                        elif ";TYPE:SKIN" in line:
                            modified_data += line + "\n"
                            modified_data += fan_sp_skin + this_fan + "\n"
                            current_fan_speed = str(fan_sp_skin.split("S")[1])
                        elif line == ";TYPE:SUPPORT":
                            modified_data += line + "\n"
                            modified_data += fan_sp_support + this_fan + "\n"
                            current_fan_speed = str(fan_sp_support.split("S")[1])
                        elif ";TYPE:SUPPORT-INTERFACE" in line:
                            modified_data += line + "\n"
                            modified_data += fan_sp_support_interface + this_fan + "\n"
                            current_fan_speed = str(fan_sp_support_interface.split("S")[1])
                        elif ";MESH:NOMESH" in line or ";MESH:NONMESH" in line:  #compatibility with 5.3.0 'NOMESH'
                            if feature_fan_combing == True:
                                modified_data += line + "\n"
                                modified_data += "M106 S0" + this_fan + "\n"
                                current_fan_speed = "0"
                            else:
                                modified_data += line + "\n"
                        elif ";TYPE:PRIME-TOWER" in line:
                            modified_data += line + "\n"
                            modified_data += fan_sp_prime_tower + this_fan + "\n"
                            current_fan_speed = str(fan_sp_prime_tower.split("S")[1])
                        elif line == ";BRIDGE":
                            modified_data += line + "\n"
                            modified_data += fan_sp_bridge + this_fan + "\n"
                            current_fan_speed = str(fan_sp_bridge.split("S")[1])
                        #If an end layer is defined - Insert the final speed and set the other variables to Final Speed to finish the file
                        elif line == ";LAYER:" + str(the_end_layer):
                            modified_data += fan_sp_feature_final + this_fan + "\n"
                            fan_sp_skirt = fan_sp_feature_final
                            fan_sp_wall_inner = fan_sp_feature_final
                            fan_sp_wall_outer = fan_sp_feature_final
                            fan_sp_fill = fan_sp_feature_final
                            fan_sp_skin = fan_sp_feature_final
                            fan_sp_support = fan_sp_feature_final
                            fan_sp_support_interface = fan_sp_feature_final
                            fan_sp_prime_tower = fan_sp_feature_final
                            fan_sp_bridge = fan_sp_feature_final
                        else:
                        #Layer and Tool get inserted above.  All other lines go into modified_data here
                            if not line.startswith("T") and not line.startswith(";LAYER:"): modified_data += line + "\n"
                if modified_data.endswith("\n"): modified_data = modified_data[0: - 1]
                data[l_index] = modified_data
                modified_data = ""
        return data

#Try to catch layer input errors, set the minimum speed to 12%, and put the strings together
class check_layer():
    def layer_checker(fan_string: str, ty_pe: str, fan_mode: bool) -> str:
        fan_string_l = str(fan_string.split("/")[0])
        try:
            if int(fan_string_l) <= 1: fan_string_l = "1"
            if fan_string_l == "": fan_string_l = str(len(data))
        except ValueError:
            fan_string_l = str(len(data))
        fan_string_l = str(int(fan_string_l) - 1)
        fan_string_p = str(fan_string.split("/")[1])
        if fan_string_p == "": fan_string_p = "0"
        try:
            if int(fan_string_p) < 0: fan_string_p = "0"
            if int(fan_string_p) > 100: fan_string_p = "100"
        except ValueError:
            fan_string_p = "0"
        #Set the minimum fan speed to 12%
        if int(fan_string_p) < 12 and int(fan_string_p) != 0:
            fan_string_p = "12"
        fan_layer_line = str(fan_string_l)
        if fan_mode:
            fan_percent_line = "M106 S" + str(round(int(fan_string_p) * 2.55))
        else:
            fan_percent_line = "M106 S" + str(round(int(fan_string_p) / 100, 1))
        if ty_pe == "l":
            return str(fan_layer_line)
        elif ty_pe == "p":
            return str(fan_percent_line)

#Try to catch feature input errors, set the minimum speed to 12%, and put the strings together when By Feature
class check_feature():
    def feature_checker(fan_feat_string: int, fan_mode: bool) -> str:
        if fan_feat_string < 0: fan_feat_string = 0
        #Set the minimum fan speed to 12%
        if fan_feat_string > 0 and fan_feat_string < 12: fan_feat_string = 12
        if fan_feat_string > 100: fan_feat_string = 100
        if fan_mode:
            fan_sp_feat = "M106 S" + str(round(fan_feat_string * 2.55))
        else:
            fan_sp_feat = "M106 S" + str(round(fan_feat_string / 100, 1))
        return fan_sp_feat

#Add more travel comments to turn the fan off during combing.  5.3.0 was "MESH:NOMESH" but 5.3.1 is back to MESH:NONMESH
class add_mesh_nonmesh():
    def add_travel_comment(the_data: str, lay_0_index: str) -> str:
        for lay_num in range(int(lay_0_index), len(the_data)-1,1):
            layer = the_data[lay_num]
            lines = layer.split("\n")
            # Copy the data to new_data and make the insertions there
            new_data = lines
            g0_count = 0
            g0_index = -1
            feature_type = ";TYPE:SUPPORT"
            is_travel = False
            for index, line in enumerate(lines):
                insert_index = 0
                if ";TYPE:" in line:
                    feature_type = line
                    is_travel = False
                    g0_count = 0
                if ";MESH:NONMESH" in line:
                    is_travel = True
                    g0_count = 0
                if line.startswith("G0 ") and not is_travel:
                    g0_count += 1
                    if g0_index == -1:
                        g0_index = lines.index(line)
                elif not line.startswith("G0 ") and not is_travel:
                #Add to shut the fan off during long combing moves--------
                    if g0_count > 5:
                        if not is_travel:
                            new_data.insert(g0_index + insert_index, ";MESH:NONMESH")
                            insert_index += 1
                #Add the feature_type at the end of the combing move to turn the fan back on
                            new_data.insert(g0_index + g0_count + 1, feature_type)
                            insert_index += 1
                        g0_count = 0
                        g0_index = -1
                        is_travel = False
                    elif g0_count <= 5:
                        g0_count = 0
                        g0_index = -1
                        is_travel = False
            the_data[lay_num] = "\n".join(new_data)
        return the_data