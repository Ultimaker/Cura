# Alter Z-Hops:  Authored by: Greg Foresi (GregValiant)
# February 2023
#      Sometimes you only need Z-hops for a specific part of a print
# This script changes the Z-Hop height from the beginning of the 'Start Layer' to the end of the 'End Layer'.
#   If the new hop height is 0.0 it negates the z-hop movement.
# The Z-hop command lines are altered, not removed.
# Z-hops are 'Settable per extruder' and this script supports different hop heights for up to 4 extruders.
# For multi-extruder printers - Z-hops at tool change are not affected by this script
# Adaptive Layers is not compatible and there is an exit if it is enabled in Cura
# Z-Hops must be enabled for at least one extruder in Cura or the plugin exits.

from ..Script import Script
from UM.Message import Message
from cura.CuraApplication import CuraApplication
import re

class AlterZhops(Script):

    def initialize(self) -> None:
        super().initialize()
        mycura = CuraApplication.getInstance().getGlobalContainerStack()
        extruder = mycura.extruderList
        extruder_count = int(mycura.getProperty("machine_extruder_count", "value"))
        
        # Default Z-hop settings------------------------------------------------------------------
        extrudert0 = mycura.extruderList[0]
        retraction_hop_enabled_t0 = bool(extrudert0.getProperty("retraction_hop_enabled", "value"))
        if retraction_hop_enabled_t0:
            orig_hop_hgt_t0 = extrudert0.getProperty("retraction_hop", "value")
            self._instance.setProperty("new_hop_hgt_t0", "value", orig_hop_hgt_t0)
        if extruder_count > 1:
            extrudert1 = mycura.extruderList[1]
            retraction_hop_enabled_t1 = bool(extrudert1.getProperty("retraction_hop_enabled", "value"))
            if retraction_hop_enabled_t1:
                orig_hop_hgt_t1 = extrudert1.getProperty("retraction_hop", "value")
                self._instance.setProperty("new_hop_hgt_t1", "value", orig_hop_hgt_t1)
        if extruder_count > 2:
            extrudert2 = mycura.extruderList[2]
            retraction_hop_enabled_t2 = bool(extrudert2.getProperty("retraction_hop_enabled", "value"))
            if retraction_hop_enabled_t2:
                orig_hop_hgt_t2 = extrudert2.getProperty("retraction_hop", "value")
                self._instance.setProperty("new_hop_hgt_t2", "value", orig_hop_hgt_t2)
        if extruder_count > 3:
            extrudert3 = mycura.extruderList[3]
            retraction_hop_enabled_t3 = bool(extrudert3.getProperty("retraction_hop_enabled", "value"))
            if retraction_hop_enabled_t3:
                orig_hop_hgt_t3 = extrudert3.getProperty("retraction_hop", "value")
                self._instance.setProperty("new_hop_hgt_t3", "value", orig_hop_hgt_t3)
    
    def getSettingDataString(self):
            return """{
            "name": "Alter Z-hops layer-to-layer",
            "key": "AlterZhops",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "new_hop_hgt_t0":
                {
                    "label": "The new Z-Hop Height T0",
                    "description": "Enter the new Z-Hop height for your gcode.  This will become the Hop Hgt across the range(s) of layers.  Enter a '0' to eliminate the Z-hops.  This is for any single extruder printer and for T0 (Extruder1) on a multi-extruder printer.",
                    "type": "float",
                    "enabled": true,
                    "unit": "mm ",
                    "default_value": 0.0
                },
                "new_hop_hgt_t1":
                {
                    "label": "The new Z-Hop Height T1",
                    "description": "Enter the new Z-Hop height for your gcode.  This will become the Hop Hgt across the range of layers.  Enter a '0' to eliminate the Z-hops.  This will be used for T1 (Extruder 2) on a multi-extruder printer.",
                    "type": "float",
                    "enabled": "resolveOrValue('machine_extruder_count') > 1",
                    "unit": "mm ",
                    "default_value": 0.0
                },
                "new_hop_hgt_t2":
                {
                    "label": "The new Z-Hop Height T2",
                    "description": "Enter the new Z-Hop height for your gcode.  This will become the Hop Hgt across the range of layers.  Enter a '0' to eliminate the Z-hops.  This will be used for T2 (Extruder 3) on a multi-extruder printer.",
                    "type": "float",
                    "enabled": "resolveOrValue('machine_extruder_count') > 2",
                    "unit": "mm ",
                    "default_value": 0.0
                },
                "new_hop_hgt_t3":
                {
                    "label": "The new Z-Hop Height T3",
                    "description": "Enter the new Z-Hop height for your gcode.  This will become the Hop Hgt across the range of layers.  Enter a '0' to eliminate the Z-hops.  This will be used for T3 (Extruder 4) on a multi-extruder printer.",
                    "type": "float",
                    "enabled": "resolveOrValue('machine_extruder_count') > 3",
                    "unit": "mm ",
                    "default_value": 0.0
                },
                "z_start_layer1":
                {
                    "label": "From Start of Layer:",
                    "description": "Use the Cura Preview numbers. Enter the Layer to start the changes at. The minimum is Layer 1.",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": 1,
                    "unit": "Lay# ",
                    "enabled": true
                },
                "z_end_layer1":
                {
                    "label": "To End of Layer",
                    "description": "Use the Cura Preview numbers. Enter '-1' for the entire file or enter a layer number.  The changes will stop at the end of your 'End Layer'.",
                    "type": "int",
                    "default_value": -1,
                    "minimum_value": -1,
                    "unit": "Lay# ",
                    "enabled": true
                },
                "z_layers2":
                {
                    "label": "Enable a second layer range",
                    "description": "Add a second range of layers.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": true
                },
                "z_start_layer2":
                {
                    "label": "    From Start of Layer:",
                    "description": "Use the Cura Preview numbers. Enter the Layer to start the changes at. The 'Minimum Value' is the previous End Layer + 1.",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": "z_end_layer1 + 1 if z_end_layer1 > -1 else 9999",
                    "unit": "Lay# ",
                    "enabled": "z_layers2"
                },
                "z_end_layer2":
                {
                    "label": "    To End of Layer",
                    "description": "Use the Cura Preview numbers. Enter '-1' for the last layer or enter a layer number.  The changes will stop at the end of your 'End Layer'.",
                    "type": "int",
                    "default_value": -1,
                    "minimum_value": -1,
                    "unit": "Lay# ",
                    "enabled": "z_layers2"
                },
                "z_layers3":
                {
                    "label": "Enable a third layer range",
                    "description": "Add a second range of layers.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "z_layers2"
                },
                "z_start_layer3":
                {
                    "label": "    From Start of Layer:",
                    "description": "Use the Cura Preview numbers. Enter the Layer to start the changes at. The 'Minimum Value' is the previous End Layer + 1.",
                    "type": "int",
                    "default_value": 120,
                    "minimum_value": "z_end_layer2 + 1 if z_end_layer2 > -1 else 9999",
                    "unit": "Lay# ",
                    "enabled": "z_layers3 and z_layers2"
                },
                "z_end_layer3":
                {
                    "label": "    To End of Layer",
                    "description": "Use the Cura Preview numbers. Enter the Layer to start the changes at. The number must be greater than the previous End Layer.",
                    "type": "int",
                    "default_value": -1,
                    "minimum_value": -1,
                    "unit": "Lay# ",
                    "enabled": "z_layers3 and z_layers2"
                }
            }
        }"""

    def execute(self, data):
        mycura = CuraApplication.getInstance().getGlobalContainerStack()
        extrudert0 = mycura.extruderList[0]
        orig_hop_hgt_t0 = extrudert0.getProperty("retraction_hop", "value")
        tool_hop_t0 = bool(extrudert0.getProperty("retraction_hop_after_extruder_switch","value"))
        z_hop_speed_t0 = extrudert0.getProperty("speed_z_hop", "value")
        z_hop_str_t0 = "F" + str(int(z_hop_speed_t0) * 60)
        extruder_count = mycura.getProperty("machine_extruder_count", "value")
        retraction_hop_enabled_t0 = extrudert0.getProperty("retraction_hop_enabled", "value")
        retraction_hop_enabled_t1 = False
        retraction_hop_enabled_t2 = False
        retraction_hop_enabled_t3 = False
        #Multi-extruder settings------------------------------------------------------------------------------
        try:
            if extruder_count > 1:
                extrudert1 = mycura.extruderList[1]
                orig_hop_hgt_t1 = str(extrudert1.getProperty("retraction_hop", "value"))
                tool_hop_t1 = bool(extrudert1.getProperty("retraction_hop_after_extruder_switch","value"))
                z_hop_speed_t1 = extrudert1.getProperty("speed_z_hop", "value")
                z_hop_str_t1 = "F" + str(int(z_hop_speed_t1) * 60)
                retraction_hop_enabled_t1 = extrudert1.getProperty("retraction_hop_enabled", "value")
        except:
            orig_hop_hgt_t1 = orig_hop_hgt_t0
            z_hop_str_t1 = z_hop_str_t0

        try:
            if extruder_count > 2:
                extrudert2 = mycura.extruderList[2]
                orig_hop_hgt_t2 = str(extrudert2.getProperty("retraction_hop", "value"))
                tool_hop_t2 = bool(extrudert2.getProperty("retraction_hop_after_extruder_switch","value"))
                z_hop_speed_t2 = extrudert2.getProperty("speed_z_hop", "value")
                z_hop_str_t2 = "F" + str(int(z_hop_speed_t2) * 60)
                retraction_hop_enabled_t2 = extrudert2.getProperty("retraction_hop_enabled", "value")
        except:
            orig_hop_hgt_t2 = orig_hop_hgt_t0
            z_hop_str_t2 = z_hop_str_t0

        try:
            if extruder_count > 3:
                extrudert3 = mycura.extruderList[3]
                orig_hop_hgt_t3 = str(extrudert3.getProperty("retraction_hop", "value"))
                tool_hop_t3 = bool(extrudert3.getProperty("retraction_hop_after_extruder_switch","value"))
                z_hop_speed_t3 = extrudert3.getProperty("speed_z_hop", "value")
                z_hop_str_t3 = "F" + str(int(z_hop_speed_t3) * 60)
                retraction_hop_enabled_t3 = extrudert3.getProperty("retraction_hop_enabled", "value")
        except:
            orig_hop_hgt_t3 = orig_hop_hgt_t0
            z_hop_str_t3 = z_hop_str_t0

        #General settings-------------------------------------------------------------------------------------------------------
        layer_height = mycura.getProperty("layer_height", "value")
        layer_height_0 = mycura.getProperty("layer_height_0", "value")
        adaptive_layers = mycura.getProperty("adaptive_layer_height_enabled", "value")
        tool_change = False

        #Exit if Adaptive layers is enabled in Cura.-----------------------------------------------------------------
        if adaptive_layers:
            data[0] += ";  [Alter Z-Hops] did not run because it is not compatible with Adaptive Layers" + "\n"
            Message(title = "Alter Z-Hops:", text = "The post processor exited because it is not compatible with Adaptive Layers.").show()
            return data

        #Exit if Z-hops aren't enabled for at least 1 extruder-----------------------------------------------------
        if retraction_hop_enabled_t0 + retraction_hop_enabled_t1 + retraction_hop_enabled_t2 + retraction_hop_enabled_t3 == 0:
            data[0] += ";  [Alter Z-Hops] did not run because Z-Hops are not enabled in Cura" + "\n"
            Message(title = "Alter Z-Hops:", text = "The post processor exited because Z-Hops are not enabled in Cura.").show()
            return data

        #Set the new Z-hop heights------------------------------------------------------------------------------------------
        new_hop_hgt_t0 = str(self.getSettingValueByKey("new_hop_hgt_t0"))
        try:
            if extruder_count > 1:
                new_hop_hgt_t1 = str(self.getSettingValueByKey("new_hop_hgt_t1"))
            if extruder_count > 2:
                new_hop_hgt_t2 = str(self.getSettingValueByKey("new_hop_hgt_t2"))
            if extruder_count > 3:
                new_hop_hgt_t3 = str(self.getSettingValueByKey("new_hop_hgt_t3"))
        except:
            new_hop_hgt_t1 = new_hop_hgt_t0
            new_hop_hgt_t2 = new_hop_hgt_t0
            new_hop_hgt_t3 = new_hop_hgt_t0

        # Make a list of start and end layers-----------------------------
        layer_list = []
        list_error = False
        z_start_layer = self.getSettingValueByKey("z_start_layer1") - 1
        z_end_layer = self.getSettingValueByKey("z_end_layer1")
        if z_end_layer == -1: z_end_layer = len(data) - 4
        for m in range(z_start_layer, z_end_layer):
            layer_list.append(m)
        if bool(self.getSettingValueByKey("z_layers2")):
            z_start_layer = self.getSettingValueByKey("z_start_layer2") - 1
            # Error check for layer range 2
            if z_start_layer <= self.getSettingValueByKey("z_end_layer1") - 1:
                Message(title = "[Alter Z-hops]", text = "There is a conflict between the end layer of range 1 and the start layer of range 2.  Range 2 and 3 were ignored.").show()
                list_error = True
            z_end_layer = self.getSettingValueByKey("z_end_layer2")
            if z_end_layer == -1: z_end_layer = len(data) - 4
            if not list_error:
                for m in range(z_start_layer, z_end_layer):
                    layer_list.append(m)
        if bool(self.getSettingValueByKey("z_layers3")) and bool(self.getSettingValueByKey("z_layers2")):
            z_start_layer = self.getSettingValueByKey("z_start_layer3") -1
            # Error check for layer range 3
            if z_start_layer <= self.getSettingValueByKey("z_end_layer2") - 1:
                Message(title = "[Alter Z-hops]", text = "There is a conflict between the end layer of range 2 and the start layer of range 3.  Range 3 was ignored.").show()
                list_error = True
            z_end_layer = self.getSettingValueByKey("z_end_layer3")
            if z_end_layer == -1: z_end_layer = len(data) - 4
            if not list_error:
                for m in range(z_start_layer, z_end_layer):
                    layer_list.append(m)
                
        #Initialize some variables---------------------------------------------------------------------------------
        new_z = float(layer_height_0)
        working_z = float(layer_height_0)
        height_current_layer = float(layer_height_0)
        z_value = 0.2
        z_up = False
        layer_number = 0
        tool_hop = False   #This one tracks if there is a hop at tool change----------------------------------------
        skip_next = False  #This one is to avoid wiping out 'retract at tool change' hops---------------------------------

        #Set hop height for any printer----------------------------------------------------------------------------
        new_hop_hgt = new_hop_hgt_t0
        prev_hop_hgt = new_hop_hgt_t0
        orig_hop_hgt = orig_hop_hgt_t0

        #Go to work------------------------------------------------------------------------------------------------------
        for index_num in range(2,len(data)-1,1):
            layer = data[index_num]
            lines = layer.split("\n")
            search_str = f"G1 {z_hop_str_t0} Z"
            modified_data = ""
            #Multi extruder printers require checking a line ahead so this keeps track of the line number----------
            current_line_nr = -1
            for line in lines:
                current_line_nr += 1
                if line.startswith(";LAYER:"):
                    layer_number = str(line.split(":")[1])
                    if int(layer_number) > 0: height_current_layer = float(layer_height)
                    working_z = round(float(layer_height_0) + (float(layer_number) * float(layer_height)),3)
                #Switch hop height for separate extruders or leave as is for single extruders--------------------------------                
                if line.startswith("T0"):
                    prev_hop_hgt = new_hop_hgt
                    new_hop_hgt = new_hop_hgt_t0
                    orig_hop_hgt = orig_hop_hgt_t0
                    search_str = f"G1 {z_hop_str_t0} Z"
                    tool_hop = tool_hop_t0
                elif line.startswith("T1"):
                #Tool change requires one last hop from the previous tools Z-Hop height.---------------------           
                    prev_hop_hgt = new_hop_hgt
                    new_hop_hgt = new_hop_hgt_t1
                    orig_hop_hgt = orig_hop_hgt_t1
                    search_str = f"G1 {z_hop_str_t1} Z"
                    tool_hop = tool_hop_t1
                elif line.startswith("T2"):
                    prev_hop_hgt = new_hop_hgt
                    new_hop_hgt = new_hop_hgt_t2
                    orig_hop_hgt = orig_hop_hgt_t2
                    search_str = f"G1 {z_hop_str_t2} Z"
                    tool_hop = tool_hop_t2
                elif line.startswith("T3"):
                    prev_hop_hgt = new_hop_hgt
                    new_hop_hgt = new_hop_hgt_t3
                    orig_hop_hgt = orig_hop_hgt_t3
                    search_str = f"G1 {z_hop_str_t3} Z"
                    tool_hop = tool_hop_t3
    
                #Change the gcode between the start layer and end layer (inclusive)-----------------------------------------------
                if int(layer_number) in layer_list:                    
                    if line.startswith(search_str) and not z_up:
                        #If there is a tool change coming up and 'hop on tool change' is enabled allow the hop to pass and go to the next line.
                        if lines[current_line_nr + 2].startswith("T") and tool_hop:
                            modified_data += line + "\n"
                            skip_next = True
                            continue
                        #Allow the hop following a tool change to remain as-is and go to the next line---------------------------
                        if skip_next:
                            modified_data += line + "\n"
                            skip_next = False
                            continue
                        #Else change the hop to the new hop height---------------------------------------------------------
                        z_value = float(line.split("Z")[1])
                        if z_value > working_z:
                            new_z = float(working_z) + float(prev_hop_hgt)
                            new_z = round(new_z,3)
                            modified_data += search_str + str(new_z) + "\n"
                            z_up = True
                            continue
                    #Z up and travel moves.----------------------------------------------------------------------------------
                    if line.startswith("G0") and ("Z" in line) and z_up:
                        new_z = float(working_z) + float(prev_hop_hgt)
                        prev_hop_hgt = new_hop_hgt
                        new_z = round(new_z, 3)
                        modified_data += str(line.split("Z")[0]) + "Z" + str(new_z) + "\n"
                        #For dual extruder printers - check if the next line starts with 'G1 Fxxx Z'.  If True then pass through the 'not z_up' section the next time around
                        next_line = lines[current_line_nr + 1]
                        if next_line.startswith(search_str):
                            z_up = False
                        else:
                            z_up = True
                        continue
                    #If it gets this far then it's the line that drops the Z back to the layer height---------------------------
                    if line.startswith(search_str) and z_up:
                        z_up = False
                modified_data += line + "\n"
            if modified_data.endswith("\n"): modified_data = modified_data[0: -1]
            data[index_num] = modified_data
        return data