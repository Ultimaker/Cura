# Written by GregValiant (Greg Foresi) June of 2023 with thanks to @AHoeben and @Ghostkeeper
# Released under the terms of the AGPLv3 or higher.
#   
#  This post processor is for machines with a 2-in-1-out or 3-in-1-out hot ends that have shared heaters and nozzles.
#     If 'Extruders Share Heater' and 'Extruders Share Nozzle' are not enabled in Cura - the post will exit.
#     This script REQUIRES that M163 and M164 are enabled in the firmware.
#     Options are: Constant Mix or Gradient Mix.  A Range of Layers, or Entire File. 'Resume Extruder' and 'Purge'.
#     Additional instances of the Post Processor can be run on different layers and with different mix ratios.
#     This Post Processor is designed for use with 'single extruder' prints.  You should disable all extruders
#        except for Extruder#1.  If Cura inserts tool changes in the gcode they will interfere with the
#        'Virtual' mixing extruder. Prime Tower should be disabled.
#        If you choose to Purge and if retractions are required before moving to park position, then the Extruder #1 retract distance is always used for those retractions.
#        Without a 'Purge' the tool changes this Post applies are done 'On-the-Fly' and printing simply continues after any tool change.  If you select to insert a Purge, the tool head will move to the park position and purge itself and then continue.  This may leave a tit on a print.  If at the end of a Mix you want to switch to a single extrudere you should probably add a purge or it may be a bit before the color straightens out.
#     If you end the mix at a mid-print layer; you can continue with the final mix or switch to another extruder.
#   The sum of the Start Percent for the extruders enabled in this post must equal 100.
#   The sum of the End Percent (when Gradient is used) for the extruders enabled in this post must also equal 100.
#   Ex: If you are using two extruders in the mix and one starts at 66 then the other must start at 34.
#   Ex: If you are using three extruders and the first starts with 35, and 2nd with 10 then E3 must start with 55.
#   The same thing applies to the End numbers when you use a gradient mix.
#   If the Percentage Sums do not add up then the post will exit with a message.
#     The virtual extruder is always Extruder_count+1 (either T2 or T3 in the gcode)
#     This Post can also be used to simply set an extruder for a print.
#   May be used with either Absolute or Relative extrusion.
#   If 'One-at-a-Time' printing and only Extruder #1 is enabled, ALL extruders will be available post-process.

from ..Script import Script
from UM.Application import Application
from UM.Message import Message
from cura.CuraApplication import CuraApplication
import re

class MultiExtColorMix(Script):
    def __init__(self):
        super().__init__()
    # Enable the third extruder setting if there is one---------------------------------
    def initialize(self) -> None:
        super().initialize()
            
        ext_cnt = Application.getInstance().getGlobalContainerStack().getProperty("machine_extruder_count", "value")
        if ext_cnt > 2:
            enable_invis = True
        else:
            enable_invis = False
        self._instance.setProperty("invis_setting", "value", enable_invis)
    # Post a message if only a single instance of this post is running-------------------------------------------
        multi_present = 0
        pp_name_list = Application.getInstance().getGlobalContainerStack().getMetaDataEntry("post_processing_scripts")
        for pp_name in pp_name_list.split("\n"):
            if "MultiExtColorMix" in pp_name:
                multi_present += 1
        if multi_present == 1:
            Message(text = "Multi-Extruder Color Mixer:" + "\n" + "You must have a Blending Hot End.  Extruders Share Heater' and 'Extruders Share Nozzle' must be enabled in the 'Printer Settings' in Cura.  Open 'MultiExtColorMix.py' in a text editor and review the opening lines for more instructions." + "\n").show()
            
    def getSettingDataString(self):
        return """{
            "name":"Multi-Extruder Color Mixer",
            "key":"MultiExtColorMix",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "mix_style":
                {
                    "label": "Mix Style",
                    "description": "'Constant' is NO CHANGE.  'Gradient' is VARIABLE from Start Mix percentage to End Mix percentage across the spread of layers. If you have 3 extruders you can include two or all three.  The 'Start Mix' numbers must add up to 100.  The 'End Mix' numbers must add up to 100.",
                    "type": "enum",
                    "options": {"constant":"Constant","gradient":"Gradient"},
                    "default_value": "constant"
                },
                "start_layer":
                {
                    "label": "Start Layer",
                    "description": "Layer to start mixing.  Use the Cura preview number.",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": 1
                },
                "end_layer":
                {
                    "label": "End Layer",
                    "description": "Layer to end the mixing.  Use -1 for the top layer or the Cura preview layer you wish to end at.",
                    "type": "int",
                    "default_value": -1,
                    "minimum_value": -1
                },
                "resume_ext":
                {
                    "label": "    Resume Extruder",
                    "description": "The extruder to use after mixing ends.  The mixing extruder is 'Number of Extruders' + 1 (regardless of whether they are enabled or not, if the printer has 3 extruders then the mixer is Extruder #4).",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": "1",
                    "maximum_value": "4",
                    "enabled": "end_layer != -1"
                },
                "T0_include":
                {
                    "label": "Ext-1 in the Mix",
                    "description": "Check For dual extruders.  For 3-in-1-out hot end Check if you want this extruder in the Mix.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": true
                },
                "T0_mix_start":
                {
                    "label": "    Ext-1 Start mix %",
                    "description": "First extruder percentage 0-100",
                    "type": "int",
                    "unit": "%",
                    "default_value": 100,
                    "minimum_value": "0",
                    "minimum_value_warning": "0",
                    "maximum_value_warning": "100",
                    "enabled": "T0_include"
                },
                "T0_mix_end":
                {
                    "label": "    Ext-1 End mix %",
                    "description": "First extruder percentage 0-100 to finish blend",
                    "type": "int",
                    "unit": "%",
                    "default_value": 0,
                    "minimum_value": "0",
                    "minimum_value_warning": "0",
                    "maximum_value_warning": "100",
                    "enabled": "T0_include and mix_style == 'gradient'"
                },
                "T1_include":
                {
                    "label": "Ext-2 in the Mix",
                    "description": "Check For dual extruders.  For 3-in-1-out hot end Check if you want this extruder included in the Mix.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": true
                },
                "T1_mix_start":
                {
                    "label": "    Ext-2 Start mix %",
                    "description": "Second extruder percentage 0-100",
                    "type": "int",
                    "unit": "%",
                    "default_value": 100,
                    "minimum_value": "0",
                    "minimum_value_warning": "0",
                    "maximum_value_warning": "100",
                    "enabled": "T1_include"
                },
                "T1_mix_end":
                {
                    "label": "    Ext-2 End mix %",
                    "description": "Second extruder percentage 0-100 to finish blend",
                    "type": "int",
                    "unit": "%",
                    "default_value": 0,
                    "minimum_value": "0",
                    "minimum_value_warning": "0",
                    "maximum_value_warning": "100",
                    "enabled": "T1_include and mix_style == 'gradient'"
                },
                "invis_setting":
                {
                    "label": "TEST:",
                    "description": "HIDDEN.  Sets 'T2_enable' visibility to true if there are 3 extruders.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": false
                },
                "T2_include":
                {
                    "label": "Ext-3 in the Mix",
                    "description": "For 3-in-1-out hot end Check if you want this extruder included in the Mix.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "invis_setting"
                },
                "T2_mix_start":
                {
                    "label": "    Ext-2 Start mix %",
                    "description": "Third extruder percentage 0-100",
                    "type": "int",
                    "unit": "%",
                    "default_value": 0,
                    "minimum_value": "0",
                    "minimum_value_warning": "0",
                    "maximum_value_warning": "100",
                    "enabled": "T2_include"
                },
                "T2_mix_end":
                {
                    "label": "    Ext-2 End mix %",
                    "description": "Third extruder percentage 0-100 to finish blend",
                    "type": "int",
                    "unit": "%",
                    "default_value": 100,
                    "minimum_value": "0",
                    "minimum_value_warning": "0",
                    "maximum_value_warning": "100",
                    "enabled": "T2_include and mix_style == 'gradient'"
                },
                "park_head":
                {
                    "label": "Park and Purge",
                    "description": "Whether to Park the head and Purge before starting a new Mix Ratio.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": true
                },
                "park_x":
                {
                    "label": "    Park X Location",
                    "description": "What X.",
                    "type": "int",
                    "default_value": 0,
                    "enabled": "park_head"
                },
                "park_y":
                {
                    "label": "    Park Y Location",
                    "description": "What Y.",
                    "type": "int",
                    "default_value": "0",
                    "enabled": "park_head"
                },
                "purge_amt":
                {
                    "label": "    Purge Amount",
                    "description": "The extruder to use after mixing ends.  The mixing extruder is 'Extruder_Count +1 (will be T3 in the gcode).",
                    "type": "int",
                    "unit": "mm ",
                    "default_value": 25,
                    "minimum_value": "1",
                    "maximum_value": "50",
                    "enabled": "park_head"
                }
            }
        }"""
    
    def execute(self, data):
        MyCura = Application.getInstance().getGlobalContainerStack()   
        extruder_count = MyCura.getProperty("machine_extruder_count", "value")
        print_sequence = str(MyCura.getProperty("print_sequence", "value"))
        init_extruder = Application.getInstance().getExtruderManager().getInitialExtruderNr()
        if extruder_count >1:
            T0_include = self.getSettingValueByKey("T0_include")
            T1_include = self.getSettingValueByKey("T1_include")
            T2_include = False
        if extruder_count == 3:
            T2_include = self.getSettingValueByKey("T2_include")
        enabled_extruders = extruder_count
        park_head = bool(self.getSettingValueByKey("park_head"))
        park_x = str(self.getSettingValueByKey("park_x"))
        park_y = str(self.getSettingValueByKey("park_y"))
        purge_amt = str(self.getSettingValueByKey("purge_amt"))
        park_string = ""
        
        # If it is a single extruder printer or if only one extruder is enabled then exit with a message-----------
        if extruder_count == 1 or enabled_extruders < 2:
            data[0] += ";  Multi-Extruder Color Mixer did not run because - Single extruder printer or single extruder enabled\n"
            Message(text = "Color Mixer: {}".format("The post processor exited: single extruder printer OR single extruder enabled.")).show()
            return data
            
        # If the printer is not equipped with Shared Heater and Shared Nozzle then exit with a message------------------
        shared_heater = bool(MyCura.getProperty("machine_extruders_share_heater", "value"))
        shared_nozzle = bool(MyCura.getProperty("machine_extruders_share_nozzle", "value"))
        if not shared_heater and not shared_nozzle:
            Message(text = "Color Mixer: {}".format("This post is for machines with 'Shared Heaters' and 'Shared Nozzles'.  Separate hot ends won't work.  Those settings are NOT enabled in Cura.  The Post Process will exit.")).show()
            data[0] += ";  Multi-Extruder Color Mixer did not run because - 'Shared Heaters' and/or 'Shared Nozzles' are diabled in Cura.\n"
            return data
            
        # Set variables---------------------------------------------------------------------
        start_layer = self.getSettingValueByKey("start_layer") - 1
        end_layer = self.getSettingValueByKey("end_layer")
        layer_span = end_layer - start_layer
        resume_extruder = self.getSettingValueByKey("resume_ext")-1
        if resume_extruder > extruder_count: resume_extruder = extruder_count
        M164_extruder = extruder_count
        mix_style = self.getSettingValueByKey("mix_style")
        
        # Figure out the actual End Layer-------------------------------------------------------------
        if end_layer == -1:
            end_layer = len(data)-3
        elif end_layer <= start_layer:
            end_layer = start_layer + 1
        else:
            end_layer -= 1            
        layer_span = end_layer - start_layer
        
        # If an extruder is enabled in Cura and included in this mix then calculate the 'Gradient' Indexing Factor------------
        if T0_include:
            T0_mix_start = int(self.getSettingValueByKey("T0_mix_start"))
            T0_mix_end = int(self.getSettingValueByKey("T0_mix_end"))
            T0_ext_incr = ((T0_mix_start - T0_mix_end) / (layer_span - 1))
        else:
            T0_mix_start = 0
            T0_mix_end = 0
            T0_ext_incr = 0
        if T1_include:
            T1_mix_start = int(self.getSettingValueByKey("T1_mix_start"))
            T1_mix_end = int(self.getSettingValueByKey("T1_mix_end"))
            T1_ext_incr = ((T1_mix_start - T1_mix_end) / (layer_span - 1))
        else:
            T1_mix_start = 0
            T1_mix_end = 0
            T1_ext_incr = 0
        if T2_include:
            T2_mix_start = int(self.getSettingValueByKey("T2_mix_start"))
            T2_mix_end = int(self.getSettingValueByKey("T2_mix_end"))
            T2_ext_incr = ((T2_mix_start - T2_mix_end) / (layer_span - 1))
        else:
            T2_mix_start = 0
            T2_mix_end = 0
            T2_ext_incr = 0
      
        # Check that the Start Percentages and the End Percentages add up to 100.  If not then Exit with a message----
        total_start_percent = 0
        total_end_percent = 0
        if T0_include:
            total_start_percent += T0_mix_start
            total_end_percent += T0_mix_end
        if T1_include:
            total_start_percent += T1_mix_start
            total_end_percent += T1_mix_end
        if T2_include:
            total_start_percent += T2_mix_start
            total_end_percent += T2_mix_end
        
        # 'Constant' mix style doesn't use the End percent so set the total to 100
        if mix_style == "constant":
            total_end_percent = 100
        if total_start_percent != 100 or total_end_percent != 100:
            textstring = "The post processor exited due to a 'Total Percentage' error. Start Total Percent = " + str(total_start_percent) + " EndTotalPercent = " + str(total_end_percent) + " Both sums must equal 100"
            Message(text = "Color Mixer: {}".format(textstring)).show()
            data[0] += ";  Multi-Extruder Color Mixer did not run because - Start Total Percent = " + str(total_start_percent) + " EndTotalPercent = " + str(total_end_percent) + " Both sums must equal 100\n"
            return data
        
        # Put together the Reset String-----------------------------------------------------------
        if extruder_count == 2:
            M163_reset = "M163 P0.50 S0" + "\nM163 P0.50 S1\n"
        if extruder_count == 3:
            M163_reset = "M163 P0.33 S0" + "\nM163 P0.34 S1\n" + "M163 P0.33 S2\n"
        M163_reset += "M164 S" + str(M164_extruder) + "\n"
            
        # Put together the Initial Mix String----------------------------------------------------------    
        if T0_include:
            M163_T0 = "\nM163 P" + str(T0_mix_start/100) + " S0"
        else:
            M163_T0 = ""
        if T1_include:
            M163_T1 = "\nM163 P" + str(T1_mix_start/100) + " S1"
        else:
            M163_T1 = ""
        if T2_include:
            M163_T2 = "\nM163 P" + str(T2_mix_start/100) + " S2"
        else:
            M163_T2 = ""
        M164str = M163_T0 + M163_T1 + M163_T2 + "\nM164 S" + str(M164_extruder) + "\nT" + str(M164_extruder)
        
        # If purge is selected--------------------------------------------------------
        initial_purge = ""
        start_purge = ""
        final_string = ""
        if park_head:
            initial_purge = ParkAndPurge.park_script(0, data, park_x, park_y, purge_amt)[1]
        if park_head and M164_extruder != resume_extruder:
            start_purge = ParkAndPurge.park_script(start_layer, data, park_x, park_y, purge_amt)[1]
        if park_head and self.getSettingValueByKey("end_layer") != -1:
            final_string = ParkAndPurge.park_script(end_layer, data, park_x, park_y, purge_amt)[0]
        
        # Check to see if a reset is already present and if so then move on-------------------------------
        reset_present = False
        start_up_sect = data[1]
        lines = start_up_sect.split("\n")
        lines.reverse()
        for z_index in range(0,7,1):          
            if lines[z_index].startswith("M164") or "Purge" in lines[z_index]:
                reset_present = True
                break
        if not reset_present:
            INIT_str = M163_T0 + M163_T1 + M163_T2 + "\nM164 S" + str(M164_extruder) + "\nT" + str(init_extruder)
            if start_layer > 0: INIT_str += initial_purge
            lines = data[1].split("\n")
            lines.insert(len(lines)-2, INIT_str[1:])
            data[1] = "\n".join(lines)
        
        pre_ret = False
        post_prime = False
        for index, layer in enumerate(data):
        # Constant-------------------------------------------------------------------------------
            if mix_style == "constant":
                if ";LAYER:" + str(start_layer) in layer:
                    lines = layer.split("\n")
                    # Is there a previous retraction and prime------------------------------
                    for line in lines:
                        if re.search(" X(\d.*) Y(\d.*) E(\d.*)",line):
                            post_prime = False
                            break
                        if re.search("G1 F(\d*) E(\d.*)", line):
                            post_prime = True
                            break
                    pre_lines = data[index-1].split("\n")
                    for pre_line in reversed(pre_lines):
                        if re.search(" X(\d.*) Y(\d.*) E(\d.*)",pre_line):
                            pre_ret = False
                            break
                        if re.search("G1 F(\d*) E(.\d*)", pre_line):
                            pre_ret = True
                            break
                    # Add the proper line for retraction/prime-------------------------------
                    if park_head:
                        if not pre_ret and not post_prime:
                            add_str = ParkAndPurge.park_script(start_layer, data, park_x, park_y, purge_amt)[0]
                        elif not pre_ret and post_prime:
                            add_str = ParkAndPurge.park_script(start_layer, data, park_x, park_y, purge_amt)[1]
                        elif pre_ret and not post_prime:
                            add_str = ParkAndPurge.park_script(start_layer, data, park_x, park_y, purge_amt)[2]
                        elif pre_ret and post_prime:
                            add_str = ParkAndPurge.park_script(start_layer, data, park_x, park_y, purge_amt)[3]
                    elif not park_head:
                        add_str = ""
                    
                    data[index] = layer.replace(";LAYER:" + str(start_layer), ";LAYER:" + str(start_layer) + M164str + add_str)
                if ";LAYER:" + str(end_layer) in layer:
                    lines = layer.split("\n")
                    # retraction and prime------------------------------------------
                    for line in lines:
                        if re.search(" X(\d.*) Y(\d.*) E(\d.*)",line):
                            post_prime = False
                            break
                        if re.search("G1 F(\d*) E(\d.*)", line):
                            post_prime = True
                            break
                    pre_lines = data[index-1].split("\n")
                    for pre_line in reversed(pre_lines):
                        if re.search(" X(\d.*) Y(\d.*) E(\d.*)",pre_line):
                            pre_ret = False
                            break
                        if re.search("G1 F(\d*) E(.\d*)", pre_line):
                            pre_ret = True
                            break
                    # Add final line depending on retraction and prime-------------------------------        
                    if park_head:
                        if not pre_ret and not post_prime:
                            final_string = ParkAndPurge.park_script(end_layer, data, park_x, park_y, purge_amt)[0]
                        elif not pre_ret and post_prime:
                            final_string = ParkAndPurge.park_script(end_layer, data, park_x, park_y, purge_amt)[1]
                        elif pre_ret and not post_prime:
                            final_string = ParkAndPurge.park_script(end_layer, data, park_x, park_y, purge_amt)[2]
                        elif pre_ret and post_prime:
                            final_string = ParkAndPurge.park_script(end_layer, data, park_x, park_y, purge_amt)[3]
                    elif not park_head:
                        final_string = ""
                    data[index] = data[index].replace(";LAYER:" + str(end_layer), ";LAYER:" + str(end_layer) + "\n" + "T" + str(resume_extruder) + final_string)
                    break
        # Gradient-------------------------------------------------------------------------------------------
            if mix_style == "gradient":
                if ";LAYER:" + str(start_layer) + "\n" in layer:
                    lines = layer.split("\n")
                    # determine retraction and primes-------------------------------------------------
                    for line in lines:
                        if re.search(" X(\d.*) Y(\d.*) E(\d.*)",line):
                            post_prime = False
                            break
                        if re.search("G1 F(\d*) E(\d.*)", line):
                            post_prime = True
                            break
                    pre_lines = data[index-1].split("\n")
                    for pre_line in reversed(pre_lines):
                        if re.search(" X(\d.*) Y(\d.*) E(\d.*)",pre_line):
                            pre_ret = False
                            break
                        if re.search("G1 F(\d*) E(.\d*)", pre_line):
                            pre_ret = True
                            break
                    # Add the line depending on retraction and prime----------------------------        
                    if park_head:
                        if not pre_ret and not post_prime:
                            add_str = ParkAndPurge.park_script(start_layer, data, park_x, park_y, purge_amt)[0]
                        elif not pre_ret and post_prime:
                            add_str = ParkAndPurge.park_script(start_layer, data, park_x, park_y, purge_amt)[1]
                        elif pre_ret and not post_prime:
                            add_str = ParkAndPurge.park_script(start_layer, data, park_x, park_y, purge_amt)[2]
                        elif pre_ret and post_prime:
                            add_str = ParkAndPurge.park_script(start_layer, data, park_x, park_y, purge_amt)[3]
                    elif not park_head:
                        add_str = ""
                        
                    data[index] = data[index].replace(";LAYER:" + str(start_layer), ";LAYER:" + str(start_layer) + M164str + add_str)
                    for L in range(index + 1, len(data)-2):
                        if T0_include:
                            T0_mix_start -= T0_ext_incr
                            if T0_mix_start > 100: T0_mix_start = 100
                            if T0_mix_start < 0: T0_mix_start = 0
                            M163_T0 = "\nM163 P" + str(round(T0_mix_start/100, 2)) + " S0"
                        else:
                            M163_T0 = ""
                        if T1_include:
                            T1_mix_start -= T1_ext_incr
                            if T1_mix_start > 100: T1_mix_start = 100
                            if T1_mix_start < 0: T1_mix_start = 0
                            M163_T1 = "\nM163 P" + str(round(T1_mix_start/100, 2)) + " S1"
                        else:
                            M163_T1 = ""
                        if T2_include:
                            T2_mix_start -= T2_ext_incr
                            if T2_mix_start > 100: T2_mix_start = 100
                            if T2_mix_start < 0: T2_mix_start = 0
                            M163_T2 = "\nM163 P" + str(round(T2_mix_start/100, 2)) + " S2"
                        else:
                            M163_T2 = ""
                        M164str = M163_T0 + M163_T1 + M163_T2 + "\nM164 S" + str(M164_extruder) + "\nT" + str(M164_extruder)
                        try:
                            layer = data[L].split("\n")
                            layer_num = int(layer[0].split(":")[1])
                            if layer_num < end_layer:
                                data[L] = data[L].replace(";LAYER:" + str(layer_num), ";LAYER:" + str(layer_num) + M164str)
                            elif layer_num == end_layer:
                                lines = layer.split("\n")
                                # determine retraction and prime------------------------------------
                                for line in lines:
                                    if re.search(" X(\d.*) Y(\d.*) E(\d.*)",line):
                                        post_prime = False
                                        break
                                    if re.search("G1 F(\d*) E(\d.*)", line):
                                        post_prime = True
                                        break
                                pre_lines = data[index-1].split("\n")
                                for pre_line in reversed(pre_lines):
                                    if re.search(" X(\d.*) Y(\d.*) E(\d.*)",pre_line):
                                        pre_ret = False
                                        break
                                    if re.search("G1 F(\d*) E(.\d*)", pre_line):
                                        pre_ret = True
                                        break
                                # Add the final line depending on retraction and prime
                                if park_head:
                                    if not pre_ret and not post_prime:
                                        final_string = ParkAndPurge.park_script(end_layer, data, park_x, park_y, purge_amt)[0]       
                                    elif not pre_ret and post_prime:
                                        final_string = ParkAndPurge.park_script(end_layer, data, park_x, park_y, purge_amt)[1]
                                    elif pre_ret and not post_prime:
                                        final_string = ParkAndPurge.park_script(end_layer, data, park_x, park_y, purge_amt)[2]
                                    elif pre_ret and post_prime:
                                        final_string = ParkAndPurge.park_script(end_layer, data, park_x, park_y, purge_amt)[3]
                                elif not park_head:
                                    final_string = ""
                                M164str = "\nT" + str(resume_extruder)
                                data[L] = data[L].replace(";LAYER:" + str(end_layer), ";LAYER:" + str(end_layer) + M164str + final_string)
                                break
                        except:
                            all
                    if layer_num == end_layer: break   
        # Add a reset if there isn't already one in place----------------------------------------------------------
        if not reset_present:
            data[len(data)-1] = M163_reset + "T" + str(resume_extruder) + "\n" + data[len(data)-1]
        return data
        
class ParkAndPurge:
    def park_script(purge_layer: str, data: str, park_x: str, park_y: str, retract_amt: str) -> str:
        # Put together the park/purge lines to be inserted----------------------------
        MyCura = Application.getInstance().getGlobalContainerStack()
        extruder = MyCura.extruderList
        if int(purge_layer) < 50:
            zup = " Z12\n"
            zdn = " Z-12\n"
        else:
            zup = " Z2\n"
            zdn = " Z-2\n"
        for index, layer in enumerate(data):
            if ";LAYER:" + str(purge_layer) + "\n" in layer:
                prev_layer = data[index-1]
                lines = prev_layer.split("\n")
                lines.reverse()
                xloc = ""
                yloc = ""            
                for line in lines:
                    if line.startswith("G0") or line.startswith("G1") or line.startswith("G2") or line.startswith("G3"):
                        if " X" in line:
                          xtemp = line.split("X")[1]
                          xloc = " X" + str(xtemp.split(" ")[0])
                        if " Y" in line:
                          ytemp = line.split("Y")[1]
                          try:
                            yloc = " Y" + str(ytemp.split(" ")[0])
                          except:
                            yloc = " Y" + str(ytemp)
                    if xloc != "" and yloc != "":
                        break
        park_ret_prime = "\n; Color Mix Purge\nG91\nM83\n"
        park_ret = "\n; Color Mix Purge\nG91\nM83\n"
        park_prime = "\n; Color Mix Purge\nG91\nM83\n"
        park_none = "\n; Color Mix Purge\nG91\nM83\n"
        firmware_retract = bool(MyCura.getProperty("machine_firmware_retract", "value"))
        speed_travel = str(int(extruder[0].getProperty("speed_travel", "value")) * 60)
        speed_print = str(int(extruder[0].getProperty("speed_print", "value")) * 60)
        speed_z_hop = str(int(extruder[0].getProperty("speed_z_hop", "value")) * 60)
        retract_distance = str(extruder[0].getProperty("retraction_amount", "value"))
        speed_retract = " F" + str(int(extruder[0].getProperty("retraction_retract_speed", "value")) *60)
        relative_ext = bool(MyCura.getProperty("relative_extrusion", "value"))
        if relative_ext:
            relative_str = "M83\n"
        else:
            relative_str = "M82\n"
        if firmware_retract:
            E_retract = "G10\n"
            E_prime = "G11\n"
        else:
            E_retract = "G1" + speed_retract + " E-" + retract_distance + "\n"
            E_prime = "G1" + speed_retract + " E" + retract_distance + "\n"
        hop_str = "G1 F" + speed_z_hop + zup
        park_at_str = "G0 F" + speed_travel + " X" + park_x + " Y" + park_y + "\n"
        purge_str = "G1" + " F200" + " E" + retract_amt + "\n"
        goto_str = "G0 F" + speed_travel + str(xloc) + str(yloc) + "\n"
        z_str = "G91\nG1 F" + speed_z_hop + zdn
        # Used when there was no retraction and no prime
        park_ret_prime += E_retract + hop_str + "G90\n" + park_at_str + purge_str + E_retract + goto_str + z_str + E_prime + relative_str + "G90\nG1 F" + speed_print + "\n;  End of Purge"
        # Used when there was no retraction and but there was a prime
        park_ret += E_retract + hop_str + "G90\n" + park_at_str + purge_str + E_retract + goto_str + z_str + relative_str + "G90\nG1 F" + speed_print + "\n;  End of Purge"
        # Used when there was a retraction and but no prime
        park_prime += hop_str + "G90\n" + park_at_str + purge_str + E_retract + goto_str + z_str + E_prime + relative_str + "G90\nG1 F" + speed_print + "\n;  End of Purge"
        # Used when there was no retraction and no prime
        park_none += hop_str + "G90\n" + park_at_str + purge_str + E_retract + goto_str + z_str + relative_str + "G90\nG1 F" + speed_print + "\n;  End of Purge"
        
        return park_ret_prime, park_ret, park_prime, park_none