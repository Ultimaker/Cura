# Alter Z-Hops:  Authored by: Greg Foresi (GregValiant)
# February 2023
#      Sometimes you only need Z-hops for a specific part of a print
# This script changes the Z-Hop height from the beginning of the 'Start Layer' to the end of the 'End Layer'.
#   If the new hop height is 0.0 it negates the z-hop movement.
# The Z-hop command lines are altered, not removed.
# This script supports different hop heights for up to 4 extruders.
# Z-Hops at tool change are not affected when 'Alter Z-Hops' runs BEFORE other post-processors that
#   make code insertions just before Tool Change lines
# Adaptive Layers is not compatible and there is an exit if it is enabled in Cura
# Z-Hops must be enabled for at least one extruder in Cura or the plugin exits.

from ..Script import Script
from UM.Logger import Logger
from UM.Message import Message
from cura.CuraApplication import CuraApplication
import re

class AlterZhops(Script):
    #def __init__(self):
        #super().__init__()

    def getSettingDataString(self):
            return """{
            "name": "Alter Z-hops layer-to-layer",
            "key": "AlterZhops",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "new_hop_hgt_T0":
                {
                    "label": "The new Z-Hop Height T0",
                    "description": "Enter the new Z-Hop height for your gcode.  Enter a '0' to eliminate the Z-hops.  This is for any single extruder printer and for T0 (Extruder1) on a multi-extruder printer.",
                    "type": "float",
                    "enabled": true,
                    "unit": "mm ",
                    "default_value": 0.0
                },
                "new_hop_hgt_T1":
                {
                    "label": "The new Z-Hop Height T1",
                    "description": "Enter the new Z-Hop height for your gcode.  Enter a '0' to eliminate the Z-hops.  This will be used fof T1 (Extruder-2) on a multi-extruder printer.",
                    "type": "float",
                    "enabled": "resolveOrValue('machine_extruder_count') > 1",
                    "unit": "mm ",
                    "default_value": 0.0
                },
                "new_hop_hgt_T2":
                {
                    "label": "The new Z-Hop Height T2",
                    "description": "Enter the new Z-Hop height for your gcode.  Enter a '0' to eliminate the Z-hops.  This will be used fof T2 (Extruder-3) on a multi-extruder printer.",
                    "type": "float",
                    "enabled": "resolveOrValue('machine_extruder_count') > 2",
                    "unit": "mm ",
                    "default_value": 0.0
                },
                "new_hop_hgt_T3":
                {
                    "label": "The new Z-Hop Height T3",
                    "description": "Enter the new Z-Hop height for your gcode.  Enter a '0' to eliminate the Z-hops.  This will be used fof T3 (Extruder-4) on a multi-extruder printer.",
                    "type": "float",
                    "enabled": "resolveOrValue('machine_extruder_count') > 3",
                    "unit": "mm ",
                    "default_value": 0.0
                },
                "z_start_layer":
                {
                    "label": "From Start of Layer:",
                    "description": "Use the Cura Preview numbers. Enter the Layer to start the changes at. The minimum is Layer 1.",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": 1,
                    "unit": "Lay# ",
                    "enabled": true
                },
                "z_end_layer":
                {
                    "label": "To End of Layer",
                    "description": "Use the Cura Preview numbers. Enter '-1' for the entire file or enter a layer number.  The changes will stop at the end of your 'End Layer'.",
                    "type": "int",
                    "default_value": -1,
                    "minimum_value": -1,
                    "unit": "Lay# ",
                    "enabled": true
                }
            }
        }"""

    def execute(self, data):
        global_container_stack = CuraApplication.getInstance().getGlobalContainerStack()
        extruderT0 = global_container_stack.extruderList[0]
        orig_hop_hgt_T0 = extruderT0.getProperty("retraction_hop", "value")
        tool_hop_T0 = bool(extruderT0.getProperty("retraction_hop_after_extruder_switch","value"))
        z_hop_speed_T0 = extruderT0.getProperty("speed_z_hop", "value")
        z_hop_str_T0 = "F" + str(int(z_hop_speed_T0) * 60)
        extruder_count = global_container_stack.getProperty("machine_extruder_count", "value")
        retraction_hop_enabled_T0 = extruderT0.getProperty("retraction_hop_enabled", "value")
    
        #Multi-extruder settings------------------------------------------------------------------------------
        try:
            if extruder_count > 1:                
                extruderT1 = global_container_stack.extruderList[1]
                orig_hop_hgt_T1 = str(extruderT1.getProperty("retraction_hop", "value"))
                tool_hop_T1 = bool(extruderT1.getProperty("retraction_hop_after_extruder_switch","value"))
                z_hop_speed_T1 = extruderT1.getProperty("speed_z_hop", "value")
                z_hop_str_T1 = "F" + str(int(z_hop_speed_T1) * 60)
                retraction_hop_enabled_T1 = extruderT1.getProperty("retraction_hop_enabled", "value")        
        except:
            orig_hop_hgt_T1 = orig_hop_hgt_T0
            z_hop_str_T1 = z_hop_str_T0
    
        try:
            if extruder_count > 2:                
                extruderT2 = global_container_stack.extruderList[2]
                orig_hop_hgt_T2 = str(extruderT2.getProperty("retraction_hop", "value"))
                tool_hop_T2 = bool(extruderT2.getProperty("retraction_hop_after_extruder_switch","value"))
                z_hop_speed_T2 = extruderT2.getProperty("speed_z_hop", "value")
                z_hop_str_T2 = "F" + str(int(z_hop_speed_T2) * 60)
                retraction_hop_enabled_T2 = extruderT2.getProperty("retraction_hop_enabled", "value")        
        except:
            orig_hop_hgt_T2 = orig_hop_hgt_T0
            z_hop_str_T2 = z_hop_str_T0
            
        try:
            if extruder_count > 3:                
                extruderT3 = global_container_stack.extruderList[3]
                orig_hop_hgt_T3 = str(extruderT3.getProperty("retraction_hop", "value"))
                tool_hop_T3 = bool(extruderT3.getProperty("retraction_hop_after_extruder_switch","value"))
                z_hop_speed_T3 = extruderT3.getProperty("speed_z_hop", "value")
                z_hop_str_T3 = "F" + str(int(z_hop_speed_T3) * 60)
                retraction_hop_enabled_T3 = extruderT3.getProperty("retraction_hop_enabled", "value")        
        except:
            orig_hop_hgt_T3 = orig_hop_hgt_T0
            z_hop_str_T3 = z_hop_str_T0
    
        #General settings-------------------------------------------------------------------------------------------------------
        layer_height = global_container_stack.getProperty("layer_height", "value")
        layer_height_0 = global_container_stack.getProperty("layer_height_0", "value")        
        adaptive_layers = global_container_stack.getProperty("adaptive_layer_height_enabled", "value")
        tool_change = False
        
        #Exit if Adaptive layers is enabled in Cura.-----------------------------------------------------------------
        if adaptive_layers:
            data[0] += ";  [Alter Z-Hops] did not run because it is not compatible with Adaptive Layers" + "\n"
            Message(title = "Alter Z-Hops:", text = "The post processor exited because it is not compatible with Adaptive Layers.").show()
            return data
    
        #Exit if Z-hops aren't enabled for at least 1 extruder-----------------------------------------------------
        if extruder_count == 1:
            if not retraction_hop_enabled_T0:
                data[0] += ";  [Alter Z-Hops] did not run because Z-Hops are not enabled in Cura" + "\n"
                Message(title = "Alter Z-Hops:", text = "The post processor exited because Z-Hops are not enabled in Cura.").show()
                return data
        elif extruder_count == 2:
            if not (retraction_hop_enabled_T0 or retraction_hop_enabled_T1):            
                data[0] += ";  [Alter Z-Hops] did not run because Z-Hops are not enabled in Cura" + "\n"
                Message(title = "Alter Z-Hops:", text = "The post processor exited because Z-Hops are not enabled in Cura.").show()
                return data
        elif extruder_count == 3:
            if not (retraction_hop_enabled_T0 or retraction_hop_enabled_T1 or retraction_hop_enabled_T2):
                data[0] += ";  [Alter Z-Hops] did not run because Z-Hops are not enabled in Cura" + "\n"
                Message(title = "Alter Z-Hops:", text = "The post processor exited because Z-Hops are not enabled in Cura.").show()
                return data
        elif extruder_count == 4:
            if not (retraction_hop_enabled_T0 or retraction_hop_enabled_T1 or retraction_hop_enabled_T2 or retraction_hop_enabled_T3):
                data[0] += ";  [Alter Z-Hops] did not run because Z-Hops are not enabled in Cura" + "\n"
                Message(title = "Alter Z-Hops:", text = "The post processor exited because Z-Hops are not enabled in Cura.").show()
                return data
    
        #Set the new Z-hop heights------------------------------------------------------------------------------------------
        new_hop_hgt_T0 = str(self.getSettingValueByKey("new_hop_hgt_T0"))
        try:
            if extruder_count > 1:
                new_hop_hgt_T1 = str(self.getSettingValueByKey("new_hop_hgt_T1"))
            if extruder_count > 2:
                new_hop_hgt_T2 = str(self.getSettingValueByKey("new_hop_hgt_T2"))
            if extruder_count > 3:
                new_hop_hgt_T3 = str(self.getSettingValueByKey("new_hop_hgt_T3"))
        except:
            new_hop_hgt_T1 = new_hop_hgt_T0
            new_hop_hgt_T2 = new_hop_hgt_T0
            new_hop_hgt_T3 = new_hop_hgt_T0  
            
        #Set the start layer and end layer-----------------------------------------------------------------------
        z_start_layer = int(self.getSettingValueByKey("z_start_layer"))
        z_start_layer -= 1 #Set the start layer to base0
        z_end_layer = int(self.getSettingValueByKey("z_end_layer"))
        if z_end_layer == -1:
            z_end_layer = 999999999
        elif z_end_layer > 0:
            z_end_layer -= 1
        if z_end_layer < z_start_layer:
            z_end_layer = z_start_layer + 1
        if z_end_layer == 999999999:
            info_str = "End Layer"
        else:
            info_str = z_end_layer + 1
            
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
        new_hop_hgt = new_hop_hgt_T0
        prev_hop_hgt = new_hop_hgt_T0
        orig_hop_hgt = orig_hop_hgt_T0

        #Go to work------------------------------------------------------------------------------------------------------
        for index_num in range(2,len(data)-1,1):
            layer = data[index_num]
            lines = layer.split("\n")
            search_str = f"G1 {z_hop_str_T0} Z"
            modified_data = ""
            #Multi extruder printers require checking a line ahead so this keeps track of the line number----------
            current_line_nr = -1
            for line in lines:
                current_line_nr += 1
                if line.startswith(";LAYER:"):
                    layer_number = str(line.split(":")[1])
                    if int(layer_number) > int(0): height_current_layer = float(layer_height)
                    working_z = round(float(layer_height_0) + (float(layer_number) * float(layer_height)),3)
            #Switch hop height for separate extruders or leave as is for single extruders--------------------------------
                if line.startswith("T0"):
                    prev_hop_hgt = new_hop_hgt
                    new_hop_hgt = new_hop_hgt_T0
                    orig_hop_hgt = orig_hop_hgt_T0
                    search_str = f"G1 {z_hop_str_T0} Z"
                    tool_hop = tool_hop_T0
                elif line.startswith("T1"):
            #Tool change requires one last hop from the previous tools Z-Hop height.---------------------           
                    prev_hop_hgt = new_hop_hgt
                    new_hop_hgt = new_hop_hgt_T1
                    orig_hop_hgt = orig_hop_hgt_T1
                    search_str = f"G1 {z_hop_str_T1} Z"
                    tool_hop = tool_hop_T1
                elif line.startswith("T2"):
                    prev_hop_hgt = new_hop_hgt
                    new_hop_hgt = new_hop_hgt_T2
                    orig_hop_hgt = orig_hop_hgt_T2
                    search_str = f"G1 {z_hop_str_T2} Z"
                    tool_hop = tool_hop_T2
                elif line.startswith("T3"):
                    prev_hop_hgt = new_hop_hgt
                    new_hop_hgt = new_hop_hgt_T3
                    orig_hop_hgt = orig_hop_hgt_T3
                    search_str = f"G1 {z_hop_str_T3} Z"
                    tool_hop = tool_hop_T3
    
            #Change the gcode between the start layer and end layer (inclusive)-----------------------------------------------
                if (int(layer_number) >= z_start_layer) and (int(layer_number) <= z_end_layer):                    
                    if line.startswith(search_str) and not z_up:  # Ex G1 F600 Z
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