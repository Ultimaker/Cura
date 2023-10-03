# Written by GregValiant (Greg Foresi) June of 2023
# Released under the terms of the AGPLv3 or higher.
#
#  This post processor is for machines with 2-in, 3-in, or 4-in-1-out hot ends that have shared heaters and nozzles.
#     If 'Extruders Share Heater' and 'Extruders Share Nozzle' are not enabled in Cura - the post will exit.
#     This script REQUIRES that M163 and M164 are enabled in the firmware.  (RepRap uses M567 and is not compatible.)
#     Prime Towers are not allowed.
#     'One-at-a-Time' is not supported
#     'Printer Settings / Shared Nozzle Initial Retraction Amount', 'Dual Extrusion / Nozzle Switch Retraction Distance', and 'Dual Extrusion / Nozzle Switch Extra Prime Amount' will be set to "0".  Users are informed of the defaults so they can be reset manually after slicing is complete.
#     Options are: Constant Mix, Gradient Mix, Range of Layers, the Entire File, the 'Resume Extruder', 'Purge' at mix change and "Initial Purge Only'.
#     Additional instances of the Post Processor can be run on different layers and with different mix ratios.
#     All tool changes and M109 and M104's will be removed from the beginning of the start layer to the end of the end layer.
#     If you choose to Purge and if retractions are required before moving to park position, then the 'Extruder #1' retract setting in Cura is always used for those retractions.
#     Without a 'Purge' the tool changes this Post applies are done 'On-the-Fly' and printing simply continues after any tool change or any mix percentage change.  If you elect to insert a Purge, the tool head will move to the park position and purge itself and then continue.  This may leave a tit on a print.  If at the end of a Mix you want to switch to a non-mixing extruder then without a purge it will take a bit for the color to change.
#   If you end the mix at a mid-print layer; you can continue with the final mix or switch to another extruder.
#   The sum of the Start Percent for the extruders enabled in this post must equal 100%.
#   The sum of the End Percent (when Gradient is used) for the extruders enabled in this post must also equal 100%.
#   Ex: If you are using two extruders in the mix and one starts at 66 then the other must start at 34.
#   Ex: If you are using three extruders and the first starts with 33, and 2nd with 33 then E3 must start with 34.
#   The same thing applies to the End numbers when you use a gradient mix.
#   If the Percentage Sums do not add up then the post will exit with a message.
#     The virtual extruder is always Extruder_count + 1.  (If the printer has 3 extruders then the virtual mixing extruder will be Extruder 4 (T3 in the gcode)).
#     This Post can also be used to simply set an extruder mix for an entire print.
#   May be used with either Absolute or Relative extrusion.
#   'One-at-a-Time' printing is not supported as it isn't allowed for multi-extruder printers in Cura.

from ..Script import Script
from UM.Application import Application
from UM.Message import Message
import re

class MultiExtColorMix(Script):

    # Adjust Cura settings and enable the 3rd and/or 4th extruder if they exist--
    def initialize(self) -> None:
        super().initialize()
        firmware_flavor = str(Application.getInstance().getGlobalContainerStack().getProperty("machine_gcode_flavor", "value"))
        if firmware_flavor != "RepRap (Marlin/Sprinter)":
            Message(title = "Multi-Extruder Color Mixer:", text = "This post processor is only compatible with Marlin firmware.  The post processor will not run.").show()
        self._instance.setProperty("enable_3rd_extruder", "value", False)
        self._instance.setProperty("enable_4th_extruder", "value", False)
        ext_list = Application.getInstance().getGlobalContainerStack().extruderList
        extruder_count = Application.getInstance().getGlobalContainerStack().getProperty("machine_extruder_count", "value")
        enable_3rd_extruder = extruder_count > 2
        enable_4th_extruder = extruder_count > 3
        self._instance.setProperty("enable_3rd_extruder", "value", enable_3rd_extruder)
        self._instance.setProperty("enable_4th_extruder", "value", enable_4th_extruder)
        self._instance.setProperty("resume_ext_nr", "maximum_value_warning", int(extruder_count + 2))
        # Disable the Prime Tower as it interferes with the tool changes by this script
        if bool(Application.getInstance().getGlobalContainerStack().getProperty("prime_tower_enable", "value")):
            Application.getInstance().getGlobalContainerStack().setProperty("prime_tower_enable", "value", False)
        # Set the nozzle-switch retraction distances to zero--------------
        shared_retraction_list = []
        switch_retraction_list = []
        switch_xtra_prime_list = []
        for ext in range(0,extruder_count,1):
            shared_initial_retraction_amt = ext_list[ext].getProperty("machine_extruders_shared_nozzle_initial_retraction", "value")
            shared_retraction_list.append(shared_initial_retraction_amt)
            switch_retraction_amt = ext_list[ext].getProperty("switch_extruder_retraction_amount", "value")
            switch_retraction_list.append(switch_retraction_amt)
            switch_extruder_extra_prime_amount = ext_list[ext].getProperty("switch_extruder_extra_prime_amount", "value")
            switch_xtra_prime_list.append(switch_extruder_extra_prime_amount)
            ext_list[ext].setProperty("machine_extruders_shared_nozzle_initial_retraction", "value", 0.0)
            ext_list[ext].setProperty("switch_extruder_retraction_amount", "value", 0.0)
            ext_list[ext].setProperty("switch_extruder_extra_prime_amount", "value", 0.0)

    # Message the user that settings may be changed-----------------------
        multi_present = 0
        try:
            pp_name_list = Application.getInstance().getGlobalContainerStack().getMetaDataEntry("post_processing_scripts")
            for pp_name in pp_name_list.split("\n"):
                if "MultiExtColorMix" in pp_name:
                    multi_present += 1
            if multi_present <= 1:
                ext1_default_str = ""
                ext2_default_str = ""
                ext3_default_str = ""
                ext4_default_str = ""
                if extruder_count >= 2:
                    ext1_default_str += "Extruder 1:\n"
                    ext1_default_str += "----Nozzle Switch Retraction Distance.......... " + str(switch_retraction_list[0]) + "\n"
                    ext1_default_str += "----Shared Extruder Initial Retraction Amt.. " + str(shared_retraction_list[0]) + "\n"
                    ext1_default_str += "----Nozzle Switch Extra Prime Amt............... " + str(switch_xtra_prime_list[0]) + "\n"
                    ext2_default_str += "Extruder 2:\n"
                    ext2_default_str += "----Nozzle Switch Retraction Distance.......... " + str(switch_retraction_list[1]) + "\n"
                    ext2_default_str += "----Shared Extruder Initial Retraction Amt.. " + str(shared_retraction_list[1]) + "\n"
                    ext2_default_str += "----Nozzle Switch Extra Prime Amt............... " + str(switch_xtra_prime_list[1]) + "\n"
                if extruder_count >= 3:
                    ext3_default_str += "Extruder 3:\n"
                    ext3_default_str += "----Nozzle Switch Retraction Distance.......... " + str(switch_retraction_list[2]) + "\n"
                    ext3_default_str += "----Shared Extruder Initial Retraction Amt.. " + str(shared_retraction_list[2]) + "\n"
                    ext3_default_str += "----Nozzle Switch Extra Prime Amt............... " + str(switch_xtra_prime_list[2]) + "\n"
                if extruder_count == 4:
                    ext4_default_str += "Extruder 4:\n"
                    ext4_default_str += "----Nozzle Switch Retraction Distance.......... " + str(switch_retraction_list[3]) + "\n"
                    ext4_default_str += "----Shared Extruder Initial Retraction Amt.. " + str(shared_retraction_list[3]) + "\n"
                    ext4_default_str += "----Nozzle Switch Extra Prime Amt............... " + str(switch_xtra_prime_list[3]) + "\n"
                Message(title = "Multi-Extruder Color Mixer:", text = "You must have a Blending Hot End and 'Extruders Share Heater' and 'Extruders Share Nozzle' must be enabled in the 'Printer Settings' in Cura.\nThe 'Printer Settings / Shared Nozzle Initial Retraction Amount' will be set to '0.0' for all extruders.\nThe 'Dual Extrusion / Nozzle Switch Retraction Distance' will be set to '0.0' for all extruders.\nThe 'Dual Extrusion / Nozzle Switch Extra Prime Amount' will be set to '0.0' for all extruders.\nPrime Tower is not allowed and will be turned off.\n\nNote Your Default Settings:" + "\n" + ext1_default_str + ext2_default_str + ext3_default_str + ext4_default_str).show()
        except:
            pass

    def getSettingDataString(self):
        return """{
            "name": "Multi-Extruder Color Mixer",
            "key": "MultiExtColorMix",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "mix_style":
                {
                    "label": "Mix Style",
                    "description": "'Constant' is set at the start of Start Layer and continues without change to the end of End Layer.  'Gradient' is VARIABLE from Start Mix percentage to End Mix percentage across the spread of layers. You can any combination of extruders.  The 'Start Mix' numbers must add up to 100.  The gradient 'End Mix' numbers must add up to 100.",
                    "type": "enum",
                    "options": {"constant":"Constant","gradient":"Gradient"},
                    "default_value": "constant"
                },
                "start_layer":
                {
                    "label": "Start Layer",
                    "description": "Mixing starts at the beginning of this layer.  Use the Cura preview number.",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": 1
                },
                "end_layer":
                {
                    "label": "End Layer",
                    "description": "Mixing stops at the end of this layer.  Use -1 for the whole print or the Cura preview layer that you wish to stop mixing at.",
                    "type": "int",
                    "default_value": -1,
                    "minimum_value": -1
                },
                "resume_ext_nr":
                {
                    "label": "    Resume Extruder #",
                    "description": "The extruder to use after mixing ends.  The virtual mixing extruder is 'Number of Extruders' + 1 (regardless of whether they are enabled or not).  If the printer has 3 extruders then the mixer is Extruder #4).",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": "1",
                    "maximum_value_warning": "6",
                    "enabled": "end_layer != -1"
                },
                "t0_include":
                {
                    "label": "Ext-1 in the Mix",
                    "description": "Check For dual extruders.  For 3-in-1-out hot end Check if you want this extruder in the Mix.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                },
                "t0_mix_start":
                {
                    "label": "    Ext-1 Start mix %",
                    "description": "First extruder percentage 0-100",
                    "type": "int",
                    "unit": "%",
                    "default_value": 100,
                    "minimum_value": 0,
                    "maximum_value": 100,
                    "enabled": "t0_include"
                },
                "t0_mix_end":
                {
                    "label": "    Ext-1 End mix %",
                    "description": "First extruder percentage 0-100 to finish blend",
                    "type": "int",
                    "unit": "%",
                    "default_value": 0,
                    "minimum_value": 0,
                    "maximum_value": 100,
                    "enabled": "t0_include and mix_style == 'gradient'"
                },
                "t1_include":
                {
                    "label": "Ext-2 in the Mix",
                    "description": "Check For dual extruders.  For 3-in-1-out hot end Check if you want this extruder included in the Mix.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                },
                "t1_mix_start":
                {
                    "label": "    Ext-2 Start mix %",
                    "description": "Second extruder percentage 0-100",
                    "type": "int",
                    "unit": "%",
                    "default_value": 0,
                    "minimum_value": "0",
                    "maximum_value": "100",
                    "enabled": "t1_include"
                },
                "t1_mix_end":
                {
                    "label": "    Ext-2 End mix %",
                    "description": "Second extruder percentage 0-100 to finish blend",
                    "type": "int",
                    "unit": "%",
                    "default_value": 100,
                    "minimum_value": "0",
                    "maximum_value": "100",
                    "enabled": "t1_include and mix_style == 'gradient'"
                },
                "enable_3rd_extruder":
                {
                    "label": "Enable 3rd Extruder:",
                    "description": "Hidden from the user.  Sets 'T2_enable' visibility to true if there are 3 extruders.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": false
                },
                "t2_include":
                {
                    "label": "Ext-3 in the Mix",
                    "description": "For 3-in-1-out hot end Check if you want this extruder included in the Mix.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_3rd_extruder"
                },
                "t2_mix_start":
                {
                    "label": "    Ext-3 Start mix %",
                    "description": "Third extruder percentage 0-100",
                    "type": "int",
                    "unit": "%",
                    "default_value": 0,
                    "minimum_value": "0",
                    "maximum_value": "100",
                    "enabled": "t2_include"
                },
                "t2_mix_end":
                {
                    "label": "    Ext-3 End mix %",
                    "description": "Third extruder percentage 0-100 to finish blend",
                    "type": "int",
                    "unit": "%",
                    "default_value": 0,
                    "minimum_value": "0",
                    "maximum_value": "100",
                    "enabled": "t2_include and mix_style == 'gradient'"
                },
                "enable_4th_extruder":
                {
                    "label": "Enable 4th Extruder:",
                    "description": "Hidden from the user.  Sets 'T3_enable' visibility to true if there are 4 extruders.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": false
                },
                "t3_include":
                {
                    "label": "Ext-4 in the Mix",
                    "description": "For 4-in-1-out hot end Check if you want this extruder included in the Mix.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_4th_extruder"
                },
                "t3_mix_start":
                {
                    "label": "    Ext-4 Start mix %",
                    "description": "Fourth extruder percentage 0-100",
                    "type": "int",
                    "unit": "%",
                    "default_value": 0,
                    "minimum_value": "0",
                    "maximum_value": "100",
                    "enabled": "t3_include and enable_4th_extruder"
                },
                "t3_mix_end":
                {
                    "label": "    Ext-4 End mix %",
                    "description": "Fourth extruder percentage 0-100 to finish blend",
                    "type": "int",
                    "unit": "%",
                    "default_value": 0,
                    "minimum_value": "0",
                    "maximum_value": "100",
                    "enabled": "t3_include and mix_style == 'gradient'"
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
                },
                "park_head_init_only":
                {
                    "label": "    Initial Purge only",
                    "description": "When enabled only the first use of the mixing extruder will Park and Purge.  Any other changes will be done on-the-fly.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "park_head"
                }
            }
        }"""

    def execute(self, data):
        mycura = Application.getInstance().getGlobalContainerStack()
        extruder_count = mycura.getProperty("machine_extruder_count", "value")
        init_extruder = Application.getInstance().getExtruderManager().getInitialExtruderNr()
        firmware_flavor = str(mycura.getProperty("machine_gcode_flavor", "value"))
        if firmware_flavor != "RepRap (Marlin/Sprinter)":
            Message(title = "Multi-Extruder Color Mixer:", text = "This post processor is only compatible with Marlin firmware.  The post processor will exit.").show()
            data[0] += ";  [Multi-Extruder Color Mix] Did not run because it is only compatible with Marlin firmware\n"
            return data
        if extruder_count > 1:
            t0_include = self.getSettingValueByKey("t0_include")
            t1_include = self.getSettingValueByKey("t1_include")
            t2_include = False
            t3_include = False
        if extruder_count >= 2:
            t2_include = self.getSettingValueByKey("t2_include")
            t3_include = False
        if extruder_count > 3:
            t3_include = self.getSettingValueByKey("t3_include")
        park_head = bool(self.getSettingValueByKey("park_head"))
        park_x = str(self.getSettingValueByKey("park_x"))
        park_y = str(self.getSettingValueByKey("park_y"))
        purge_amt = str(self.getSettingValueByKey("purge_amt"))
        park_head_init_only = bool(self.getSettingValueByKey("park_head_init_only"))
        park_string = ""

        # If the Prime Tower is enabled after the script is loaded then inform the user and exit-----
        if bool(mycura.getProperty("prime_tower_enable", "value")):
            data[0] += ";  [Multi-Extruder Color Mixer] Did not run because - Prime Tower is enabled.\n"
            Message(title = "[Multi-Extruder Color Mixer]:", text = "DID NOT RUN because Prime Tower is enabled.").show()
            return data

        # If Extruder Count > 4 then inform the user that only 1 thru 4 may be mixed
        if extruder_count > 4:
            Message(title = "[Multi-Extruder Color Mixer]:", text = "The number of extruders is > 4 but only extruders #1, #2, #3, and #4 can be used when mixing.").show()

        # If it is a single extruder printer exit with a message-----------
        if extruder_count == 1:
            data[0] += ";  [Multi-Extruder Color Mixer] did not run because the printer has one extruder\n"
            Message(title = "Multi-Extruder Color Mixer:", text = "The post processor exited because the printer has a single extruder.").show()
            return data

        # If the printer is not equipped with Shared Heater and Shared Nozzle then exit with a message------------------
        shared_heater = bool(mycura.getProperty("machine_extruders_share_heater", "value"))
        try:
            shared_nozzle = bool(mycura.getProperty("machine_extruders_share_nozzle", "value"))
        except:
            shared_nozzle = shared_heater
        if not shared_heater and not shared_nozzle:
            Message(title = "Multi-Extruder Color Mixer:", text = "This post is for machines with 'Shared Heaters' and 'Shared Nozzles'.  Separate hot ends won't work.  Those settings are not enabled in Cura.  The Post Process will exit.").show()
            data[0] += ";  [Multi-Extruder Color Mixer] did not run because - 'Shared Heaters' and/or 'Shared Nozzles' are not enabled in Cura.\n"
            return data

        # Set variables---------------------------------------------------------------------
        start_layer = self.getSettingValueByKey("start_layer") - 1
        end_layer = self.getSettingValueByKey("end_layer")
        resume_ext_nr = self.getSettingValueByKey("resume_ext_nr")-1
        if resume_ext_nr > extruder_count + 1: resume_ext_nr = extruder_count + 1
        m164_ext_nr = extruder_count
        mix_style = self.getSettingValueByKey("mix_style")

        # Figure out the actual End Layer-------------------------------------------------------------
        if end_layer == -1:
            end_layer = len(data)-2
        elif end_layer <= start_layer:
            end_layer = start_layer + 1
        layer_span = end_layer - start_layer - 1

        # Calculate the 'Gradient' Indexing Factor for extruders included in the mixing------------
        if t0_include:
            t0_mix_start = int(self.getSettingValueByKey("t0_mix_start")); t0_mix_end = int(self.getSettingValueByKey("t0_mix_end")); t0_ext_incr = (t0_mix_start - t0_mix_end) / (layer_span)
        else:
            t0_mix_start = 0; t0_mix_end = 0; t0_ext_incr = 0
        if t1_include:
            t1_mix_start = int(self.getSettingValueByKey("t1_mix_start")); t1_mix_end = int(self.getSettingValueByKey("t1_mix_end")); t1_ext_incr = (t1_mix_start - t1_mix_end) / (layer_span)
        else:
            t1_mix_start = 0; t1_mix_end = 0; t1_ext_incr = 0
        if t2_include:
            t2_mix_start = int(self.getSettingValueByKey("t2_mix_start")); t2_mix_end = int(self.getSettingValueByKey("t2_mix_end")); t2_ext_incr = (t2_mix_start - t2_mix_end) / (layer_span)
        else:
            t2_mix_start = 0; t2_mix_end = 0; t2_ext_incr = 0
        if t3_include:
            t3_mix_start = int(self.getSettingValueByKey("t3_mix_start")); t3_mix_end = int(self.getSettingValueByKey("t3_mix_end")); t3_ext_incr = (t3_mix_start - t3_mix_end) / (layer_span)
        else:
            t3_mix_start = 0; t3_mix_end = 0; t3_ext_incr = 0

        # Check that the Start %s and the End %s add up to 100.  If not then Exit with a message and add a notice to data[0]----
        total_start_percent = 0
        total_end_percent = 0
        if t0_include:
            total_start_percent += t0_mix_start
            total_end_percent += t0_mix_end
        if t1_include:
            total_start_percent += t1_mix_start
            total_end_percent += t1_mix_end
        if t2_include:
            total_start_percent += t2_mix_start
            total_end_percent += t2_mix_end
        if t3_include:
            total_start_percent += t3_mix_start
            total_end_percent += t3_mix_end
        if mix_style == "constant": # 'Constant' mix style doesn't use the End percent so set the total to 100
            total_end_percent = 100
        if total_start_percent != 100 or total_end_percent != 100:
            textstring = "The post processor exited due to a 'Total Percentage' error. Start Total Percent = " + str(total_start_percent) + " EndTotalPercent = " + str(total_end_percent) + " Each sum must equal 100"
            Message(title = "[Multi-Extruder Color Mixer]:", text  = textstring).show()
            data[0] += ";  [Multi-Extruder Color Mixer] Did not run because Start Total Percent = " + str(total_start_percent) + " EndTotalPercent = " + str(total_end_percent) + " Each sum must equal 100%\n"
            return data

        # Start to alter the data----------------------------------------------
        # Remove the existing tool changes and temperature lines from the Start Layer through the End Layer.  This leaves one G92 E0 at each previous tool change
        for num in range(start_layer + 2,end_layer + 1,1):
            data[num] = re.sub("G92 E0\nT(\d*)\n", "", data[num])
            data[num] = re.sub("M109 S(\d.*)\n", "",data[num])
            data[num] = re.sub("M104 S(\d.*)\n", "",data[num])
            data[num] = re.sub("M105\n", "",data[num])

        # Put together the Reset String----------------------------------------
        m163_reset = ""
        if extruder_count == 2:
            m163_reset = "M163 P0.50 S0\nM163 P0.50 S1\n"
        if extruder_count == 3:
            m163_reset = "M163 P0.33 S0\nM163 P0.34 S1\nM163 P0.33 S2\n"
        if extruder_count == 4:
            m163_reset = "M163 P0.25 S0\nM163 P0.25 S1\nM163 P0.25 S2\nM163 P0.25 S3\n"
        m163_reset += f"M164 S{m164_ext_nr}\n"

        # Put together the Initial Mix String----------------------------------
        if t0_include:
            m163_t0 = f"\nM163 P{t0_mix_start/100} S0"
        else:
            m163_t0 = ""
        if t1_include:
            m163_t1 = f"\nM163 P{t1_mix_start/100} S1"
        else:
            m163_t1 = ""
        if t2_include:
            m163_t2 = f"\nM163 P{t2_mix_start/100} S2"
        else:
            m163_t2 = ""
        if t3_include:
            m163_t3 = f"\nM163 P{t3_mix_start/100} S3"
        else:
            m163_t3 = ""
        m164str = m163_t0 + m163_t1 + m163_t2 + m163_t3 + "\nM164 S" + str(m164_ext_nr) + "\nT" + str(m164_ext_nr)

        # If purge is selected-------------------------------------------------
        initial_purge = ""
        start_purge = ""
        final_string = ""
        if park_head:
            initial_purge = self.park_script(0, data, park_x, park_y, purge_amt)[1]
        if park_head and m164_ext_nr != resume_ext_nr and not park_head_init_only:
            start_purge = self.park_script(start_layer, data, park_x, park_y, purge_amt)[1]
        if park_head and self.getSettingValueByKey("end_layer") != -1:
            final_string = self.park_script(end_layer, data, park_x, park_y, purge_amt)[0]

        # Check to see if a reset is already present (if multiple instances of this post processor are running) and if so then move on--------
        reset_present = False
        start_up_sect = data[1]
        lines = start_up_sect.split("\n")
        lines.reverse()
        for z_index in range(0,7,1):
            if lines[z_index].startswith("M164") or "Purge" in lines[z_index]:
                reset_present = True
                break
        if not reset_present:
            init_str = f"{m163_t0}{m163_t1}{m163_t2}{m163_t3}\nM164 S{m164_ext_nr}\n"
            if start_layer == 0: init_str += f"T{init_extruder}\n"
            if start_layer > 0: init_str += initial_purge
            lines = data[1].split("\n")
            lines.insert(len(lines)-2, init_str[1:])
            data[1] = "\n".join(lines)

        # Constant
        if mix_style == "constant":
            self.processConstant(data,
                                start_layer,
                                end_layer,
                                park_head,
                                park_x,
                                park_y,
                                purge_amt,
                                m164str,
                                resume_ext_nr,
                                park_head_init_only)

        # Gradient
        elif mix_style == "gradient":
            self.processGradient(data,
                                start_layer,
                                end_layer,
                                park_head,
                                park_x,
                                park_y,
                                purge_amt,
                                m164str,
                                resume_ext_nr,
                                t0_include,
                                t0_mix_start,
                                t0_ext_incr,
                                t1_include,
                                t1_mix_start,
                                t1_ext_incr,
                                t2_include,
                                t2_mix_start,
                                t2_ext_incr,
                                t3_include,
                                t3_mix_start,
                                t3_ext_incr,
                                m163_t0,
                                m163_t1,
                                m163_t2,
                                m163_t3,
                                m164_ext_nr,
                                park_head_init_only)
        if not reset_present:
            data[len(data)-1] = m163_reset + "T" + str(resume_ext_nr) + "\n" + data[len(data)-1]
        return data

    def processConstant(self,
                        data: str,
                        start_layer: int,
                        end_layer: int,
                        park_head: bool,
                        park_x: str,
                        park_y: str,
                        purge_amt: str,
                        m164str: str,
                        resume_ext_nr: int,
                        park_head_init_only: bool) -> str:
        pre_ret = False
        post_prime = False
        for index, layer in enumerate(data):
            if ";LAYER:" + str(start_layer) + "\n" in layer:
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
                        add_str = self.park_script(start_layer, data, park_x, park_y, purge_amt)[0]
                    elif not pre_ret and post_prime:
                        add_str = self.park_script(start_layer, data, park_x, park_y, purge_amt)[1]
                    elif pre_ret and not post_prime:
                        add_str = self.park_script(start_layer, data, park_x, park_y, purge_amt)[2]
                    elif pre_ret and post_prime:
                        add_str = self.park_script(start_layer, data, park_x, park_y, purge_amt)[3]
                elif not park_head:
                    add_str = ""
                #if park_head_init_only:
                #    add_str = ""
                data[index] = layer.replace(";LAYER:" + str(start_layer) + "\n", ";LAYER:" + str(start_layer) + m164str + add_str + "\n")
            if ";LAYER:" + str(end_layer) in layer:
                lines = layer.split("\n")
                # The last retraction and prime------------------------------------------
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
                if park_head and not park_head_init_only:
                    if not pre_ret:
                        final_string = self.park_script(end_layer, data, park_x, park_y, purge_amt)[0]
                    elif not pre_ret and post_prime:
                        final_string = self.park_script(end_layer, data, park_x, park_y, purge_amt)[1]
                    elif pre_ret and not post_prime:
                        final_string = self.park_script(end_layer, data, park_x, park_y, purge_amt)[2]
                    elif pre_ret and post_prime:
                        final_string = self.park_script(end_layer, data, park_x, park_y, purge_amt)[3]
                elif not park_head:
                    final_string = ""
                data[index] = data[index].replace(";LAYER:" + str(end_layer), ";LAYER:" + str(end_layer) + "\n" + "T" + str(resume_ext_nr) + final_string)
                break
        return

    def processGradient(self,
                        data: str,
                        start_layer: int,
                        end_layer: int,
                        park_head: bool,
                        park_x: str,
                        park_y: str,
                        purge_amt: str,
                        m164str: str,
                        resume_ext_nr: int,
                        t0_include: bool,
                        t0_mix_start: int,
                        t0_ext_incr: int,
                        t1_include: bool,
                        t1_mix_start: int,
                        t1_ext_incr: int,
                        t2_include:bool,
                        t2_mix_start: int,
                        t2_ext_incr: int,
                        t3_include:bool,
                        t3_mix_start: int,
                        t3_ext_incr: int,
                        m163_t0: str,
                        m163_t1: str,
                        m163_t2: str,
                        m163_t3: str,
                        m164_ext_nr: int,
                        park_head_init_only: bool) -> str:
        pre_ret = False
        post_prime = False
        for index, layer in enumerate(data):
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
                        add_str = self.park_script(start_layer, data, park_x, park_y, purge_amt)[0]
                    elif not pre_ret and post_prime:
                        add_str = self.park_script(start_layer, data, park_x, park_y, purge_amt)[1]
                    elif pre_ret and not post_prime:
                        add_str = self.park_script(start_layer, data, park_x, park_y, purge_amt)[2]
                    elif pre_ret and post_prime:
                        add_str = self.park_script(start_layer, data, park_x, park_y, purge_amt)[3]
                elif not park_head:
                    add_str = ""

                # Gradient percentages and fix rounding errors------------------------------
                data[index] = data[index].replace(";LAYER:" + str(start_layer) + "\n", ";LAYER:" + str(start_layer) + m164str + add_str + "\n")
                for L in range(index + 1, len(data)-2):
                    if t0_include:
                        t0_mix_start -= t0_ext_incr
                        if t0_mix_start > 100: t0_mix_start = 100
                        if t0_mix_start < 0: t0_mix_start = 0
                        m163_t0 = f"\nM163 P{round(t0_mix_start/100, 2)} S0"
                    else:
                        m163_t0 = ""
                    if t1_include:
                        t1_mix_start -= t1_ext_incr
                        if t1_mix_start > 100: t1_mix_start = 100
                        if t1_mix_start < 0: t1_mix_start = 0
                        m163_t1 = f"\nM163 P{round(t1_mix_start/100, 2)} S1"
                    else:
                        m163_t1 = ""
                    if t2_include:
                        t2_mix_start -= t2_ext_incr
                        if t2_mix_start > 100: t2_mix_start = 100
                        if t2_mix_start < 0: t2_mix_start = 0
                        m163_t2 = f"\nM163 P{round(t2_mix_start/100, 2)} S2"
                    else:
                        m163_t2 = ""
                    if t3_include:
                        t3_mix_start -= t3_ext_incr
                        if t3_mix_start > 100: t3_mix_start = 100
                        if t3_mix_start < 0: t3_mix_start = 0
                        m163_t3 = f"\nM163 P{round(t3_mix_start/100, 2)} S3"
                    else:
                        m163_t3 = ""
                    m164str = f"{m163_t0}{m163_t1}{m163_t2}{m163_t3}\nM164 S{m164_ext_nr}\nT{m164_ext_nr}\n"
                    try:
                        lines = data[L].split("\n")
                        layer_num = int(lines[0].split(":")[1])
                        if layer_num < end_layer:
                            data[L] = data[L].replace(";LAYER:" + str(layer_num) + "\n", ";LAYER:" + str(layer_num) + m164str)
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
                            if park_head and not park_head_init_only:
                                if not pre_ret and not post_prime:
                                    final_string = self.park_script(end_layer, data, park_x, park_y, purge_amt)[0]
                                elif not pre_ret and post_prime:
                                    final_string = self.park_script(end_layer, data, park_x, park_y, purge_amt)[1]
                                elif pre_ret and not post_prime:
                                    final_string = self.park_script(end_layer, data, park_x, park_y, purge_amt)[2]
                                elif pre_ret and post_prime:
                                    final_string = self.park_script(end_layer, data, park_x, park_y, purge_amt)[3]
                            elif not park_head:
                                final_string = ""
                            if park_head_init_only:
                                final_string = ""
                            m164str = "\nT" + str(resume_ext_nr)
                            data[L] = data[L].replace(";LAYER:" + str(end_layer), ";LAYER:" + str(end_layer) + m164str + final_string)
                            break
                    except:
                        pass
                if layer_num == end_layer:
                    break
        return

    @staticmethod
    def park_script(purge_layer: str, data: str, park_x: str, park_y: str, retract_amt: str) -> str:
        # Put together the park/purge lines to be inserted----------------------------
        mycura = Application.getInstance().getGlobalContainerStack()
        extruder = mycura.extruderList
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
        park_ret_prime = "\n;TYPE:CUSTOM Multi Mix Purge\nG91\nM83\n"
        park_ret = "\n;TYPE:CUSTOM Multi Mix Purge\nG91\nM83\n"
        park_prime = "\n;TYPE:CUSTOM Multi Mix Purge\nG91\nM83\n"
        park_none = "\n;TYPE:CUSTOM Multi Mix Purge\nG91\nM83\n"
        firmware_retract = bool(mycura.getProperty("machine_firmware_retract", "value"))
        speed_travel = str(int(extruder[0].getProperty("speed_travel", "value")) * 60)
        speed_print = str(int(extruder[0].getProperty("speed_print", "value")) * 60)
        speed_z_hop = str(int(extruder[0].getProperty("speed_z_hop", "value")) * 60)
        retract_distance = str(extruder[0].getProperty("retraction_amount", "value"))
        speed_retract = " F" + str(int(extruder[0].getProperty("retraction_retract_speed", "value")) *60)
        relative_ext = bool(mycura.getProperty("relative_extrusion", "value"))
        relative_str = "M83\n" if relative_ext else "M82\n"
        e_retract = "G10\n" if firmware_retract else f"G1{speed_retract} E-{retract_distance}\n"
        e_prime = "G11\n" if firmware_retract else f"G1{speed_retract} E{retract_distance}\n"
        hop_str = f"G1 F{speed_z_hop}{zup}"
        park_at_str = f"G0 F{speed_travel} X{park_x} Y{park_y}\n"
        purge_str = f"G1 F200 E{retract_amt}\n"
        goto_str = f"G0 F{speed_travel}{xloc}{yloc}\n"
        z_str = f"G91\nG1 F{speed_z_hop}{zdn}"
        # Used when yes retraction and yes prime
        park_ret_prime += f"{e_retract}{hop_str}G90\n{park_at_str}{purge_str}{e_retract}{goto_str}{z_str}{e_prime}{relative_str}G90\nG1 F{speed_print}\n; End of Purge"
        # Used when yes retraction and no prime
        park_ret += f"{e_retract}{hop_str}G90\n{park_at_str}{purge_str}{e_retract}{goto_str}{z_str}{relative_str}G90\nG1 F{speed_print}\n; End of Purge"
        # Used when no retraction and yes prime
        park_prime += f"{hop_str}G90\n{park_at_str}{purge_str}{e_retract}{goto_str}{z_str}{e_prime}{relative_str}G90\nG1 F{speed_print}\n; End of Purge"
        # Used when no retraction and no prime
        park_none += f"{hop_str}G90\n{park_at_str}{purge_str}{e_retract}{goto_str}{z_str}{relative_str}G90\nG1 F{speed_print}\n; End of Purge"
        return park_ret_prime, park_ret, park_prime, park_none