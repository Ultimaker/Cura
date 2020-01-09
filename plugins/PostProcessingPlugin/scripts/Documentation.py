# Copyright (c) 2019 5axes
#
import re #To perform the search and replace.

from ..Script import Script
from UM.Application import Application #To get the current printer's settings.
from cura.CuraVersion import CuraVersion  # type: ignore
        
##  Performs a search-and-replace on all g-code.
#
#   Due to technical limitations, the search can't cross the border between layers.
class Documentation(Script):
    def getSettingDataString(self):
        return """{
            "name": "Documentation parametres",
            "key": "Documentation",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "search":
                {
                    "label": "Search",
                    "description": "All occurrences of this text will get replaced by the parameter list.",
                    "type": "str",
                    "default_value": ";FLAVOR:Marlin"
                },
                "advanced_desc":
                {
                    "label": "Advanced description",
                    "description": "Select for avdvanced description",
                    "type": "bool",
                    "default_value": false
                },
                "extruder_nb":
                {
                    "label": "Extruder Id",
                    "description": "Define extruder Id in case of multi extruders ",
                    "unit": "",
                    "type": "int",
                    "default_value": 1
                }
            }
        }"""

#   Format the text
    def SetSpace(self,key,dec):
        dec_line = " " * int(dec)
        new_line = dec_line + str(key)
        lg = 55 - len(new_line)
        string_val = " " * abs(lg)
        
        new_line = "\n; " + new_line + string_val + ": "
        return new_line

    def SetSect(self,key):
        new_line = str(key)
        lg = int((76 - len(new_line)) * 0.5) 
        string_val = "-" * lg
        new_line = "\n; " + string_val + " " + new_line + " " + string_val
        return new_line
    
    
    def execute(self, data):
        search_string = self.getSettingValueByKey("search")
        adv_desc = self.getSettingValueByKey("advanced_desc")
        extruder_id  = self.getSettingValueByKey("extruder_nb")
        extruder_id = extruder_id -1
        search_regex = re.compile(search_string)

        replace_string = search_string
        replace_string = replace_string + "\n;===============================================================================\n;  Documentation\n;==============================================================================="   

        #   machine_extruder_count
        extruder_count=Application.getInstance().getGlobalContainerStack().getProperty("machine_extruder_count", "value")
        extruder_count = extruder_count-1
        if extruder_id>extruder_count :
            extruder_id=extruder_count
        # GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("machine_extruder_count", "label")
        # replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val}".format(Val = extruder_count)
        
        # add extruder specific data to slice info
        extruders = list(Application.getInstance().getGlobalContainerStack().extruders.values())
        #   Profile
        GetValStr = extruders[extruder_id].qualityChanges.getMetaData().get("name", "")
        GetLabel = "Profile ( Version Cura " + CuraVersion + " )"
        replace_string = replace_string + self.SetSpace(GetLabel,0) + GetValStr
        #   Quality
        GetValStr = extruders[extruder_id].quality.getMetaData().get("name", "")
        GetLabel = "Quality"
        replace_string = replace_string + self.SetSpace(GetLabel,0) + GetValStr        
        #   Material
        GetValStr = extruders[extruder_id].material.getMetaData().get("material", "")
        GetLabel = "Material"
        replace_string = replace_string + self.SetSpace(GetLabel,0) + GetValStr
        #   material_diameter 
        GetVal = extruders[extruder_id].getProperty("material_diameter", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("material_diameter", "label")
        replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} mm".format(Val = GetVal)        
        #   machine_nozzle_size
        GetVal = extruders[extruder_id].getProperty("machine_nozzle_size", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("machine_nozzle_size", "label")
        replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} mm".format(Val = GetVal)        
        #   -----------------------------------  resolution ----------------------------- 
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("resolution", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSect(GetLabel)

        #   layer_height
        GetVal = extruders[extruder_id].getProperty("layer_height", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("layer_height", "label")
        replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} mm".format(Val = GetVal)
        #   layer_height_0
        GetVal = extruders[extruder_id].getProperty("layer_height_0", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("layer_height_0", "label")
        replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} mm".format(Val = GetVal)          
        #   line_width 
        GetVal = extruders[extruder_id].getProperty("line_width", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("line_width", "label")
        replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} mm".format(Val = GetVal)
        #   initial_layer_line_width_factor 
        GetVal = extruders[extruder_id].getProperty("initial_layer_line_width_factor", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("initial_layer_line_width_factor", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} %".format(Val = GetVal)

        #   -----------------------------------  shell ----------------------------- 
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("shell", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSect(GetLabel)

        #   wall_thickness 
        GetVal = extruders[extruder_id].getProperty("wall_thickness", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("wall_thickness", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} mm".format(Val = GetVal)
        #   wall_line_count 
        GetVal = extruders[extruder_id].getProperty("wall_line_count", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("wall_line_count", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,10) + "{Val}".format(Val = GetVal)

        #   wall_0_wipe_dist
        GetVal = extruders[extruder_id].getProperty("wall_0_wipe_dist", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("wall_0_wipe_dist", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} mm".format(Val = GetVal)           
        #   top_layers
        GetVal = extruders[extruder_id].getProperty("top_layers", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("top_layers", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,10) + "{Val}".format(Val = GetVal)
        #   bottom_layers
        GetVal = extruders[extruder_id].getProperty("bottom_layers", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("bottom_layers", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,10) + "{Val}".format(Val = GetVal)            

        #   top_bottom_pattern 
        GetValStr = extruders[extruder_id].getProperty("top_bottom_pattern", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("top_bottom_pattern", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + GetValStr
        #   outer_inset_first
        GetVal = extruders[extruder_id].getProperty("outer_inset_first", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("outer_inset_first", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "[{Val}]".format(Val = GetVal)
        #   travel_compensate_overlapping_walls_enabled
        GetVal = extruders[extruder_id].getProperty("travel_compensate_overlapping_walls_enabled", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("travel_compensate_overlapping_walls_enabled", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "[{Val}]".format(Val = GetVal)
        #   fill_perimeter_gaps 
        GetValStr = extruders[extruder_id].getProperty("fill_perimeter_gaps", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("fill_perimeter_gaps", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + GetValStr
            
        #   fill_outline_gaps
        GetVal = extruders[extruder_id].getProperty("fill_outline_gaps", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("fill_outline_gaps", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "[{Val}]".format(Val = GetVal)

        #   xy_offset
        GetVal = extruders[extruder_id].getProperty("xy_offset", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("xy_offset", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} mm".format(Val = GetVal)           
         #   z_seam_type 
        GetValStr = extruders[extruder_id].getProperty("z_seam_type", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("z_seam_type", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + GetValStr
         #   z_seam_corner 
        GetValStr = extruders[extruder_id].getProperty("z_seam_corner", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("z_seam_corner", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + GetValStr            
        #   ironing_enabled 
        GetVal = extruders[extruder_id].getProperty("ironing_enabled", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("ironing_enabled", "label")
        replace_string = replace_string + self.SetSpace(GetLabel,0) + "[{Val}]".format(Val = GetVal)
        
        #   -----------------------------------  infill ------------------------------ 
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("infill", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSect(GetLabel)

        #   infill_sparse_density 
        GetVal = extruders[extruder_id].getProperty("infill_sparse_density", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("infill_sparse_density", "label")
        replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} %".format(Val = GetVal)
        #   infill_pattern
        GetValStr = extruders[extruder_id].getProperty("infill_pattern", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("infill_pattern", "label")
        replace_string = replace_string + self.SetSpace(GetLabel,0) + GetValStr
        #   infill_overlap
        GetVal = extruders[extruder_id].getProperty("infill_overlap", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("infill_overlap", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} %".format(Val = GetVal)        
        #   gradual_infill_steps
        GetVal = extruders[extruder_id].getProperty("gradual_infill_steps", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("gradual_infill_steps", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val}".format(Val = GetVal)
            
        #   ------------------------------------  material ------------------------------- 
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("material", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSect(GetLabel)
        #   material_flow 
        GetVal = extruders[extruder_id].getProperty("material_flow", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("material_flow", "label")
        replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} %".format(Val = GetVal)
        #   material_print_temperature 
        GetVal = extruders[extruder_id].getProperty("material_print_temperature", "value")      
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("material_print_temperature", "label")
        replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val}°C".format(Val = GetVal)
        #   material_print_temperature_layer_0
        GetVal = extruders[extruder_id].getProperty("material_print_temperature_layer_0", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("material_print_temperature_layer_0", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val}°C".format(Val = GetVal)
        #   material_bed_temperature
        GetVal = extruders[extruder_id].getProperty("material_bed_temperature", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("material_bed_temperature", "label")
        replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val}°C".format(Val = GetVal)
        #   material_bed_temperature_layer_0
        GetVal = extruders[extruder_id].getProperty("material_bed_temperature_layer_0", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("material_bed_temperature_layer_0", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val}°C".format(Val = GetVal)
        #   retraction_enable 
        GetVal = extruders[extruder_id].getProperty("retraction_enable", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("retraction_enable", "label")
        replace_string = replace_string + self.SetSpace(GetLabel,0) + "[{Val}]".format(Val = GetVal)
        #   retract_at_layer_change
        GetVal = extruders[extruder_id].getProperty("retract_at_layer_change", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("retract_at_layer_change", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "[{Val}]".format(Val = GetVal)        
        #   retraction_amount 
        GetVal = extruders[extruder_id].getProperty("retraction_amount", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("retraction_amount", "label")
        replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} mm".format(Val = GetVal)
        #   retraction_speed 
        GetVal = extruders[extruder_id].getProperty("retraction_speed", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("retraction_speed", "label")
        replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} mm/s".format(Val = GetVal)

        #   ------------------------------------  speed ------------------------------ 
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("speed", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSect(GetLabel)

        #   speed_print 
        GetVal = extruders[extruder_id].getProperty("speed_print", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("speed_print", "label")
        replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} mm/s".format(Val = GetVal)
        #   speed_infill 
        GetVal = extruders[extruder_id].getProperty("speed_infill", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("speed_infill", "label")
        replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} mm/s".format(Val = GetVal)        
        #   speed_wall 
        GetVal = extruders[extruder_id].getProperty("speed_wall", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("speed_wall", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,5) + "{Val} mm/s".format(Val = GetVal)        
        #   speed_wall_0 
        GetVal = extruders[extruder_id].getProperty("speed_wall_0", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("speed_wall_0", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,10) + "{Val} mm/s".format(Val = GetVal)        
        #   speed_wall_x 
        GetVal = extruders[extruder_id].getProperty("speed_wall_x", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("speed_wall_x", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,10) + "{Val} mm/s".format(Val = GetVal)        

        #   speed_topbottom 
        GetVal = extruders[extruder_id].getProperty("speed_topbottom", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("speed_topbottom", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,5) + "{Val} mm/s".format(Val = GetVal)        
        #   speed_support 
        GetVal = extruders[extruder_id].getProperty("speed_support", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("speed_support", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,5) + "{Val} mm/s".format(Val = GetVal)
            
        #   speed_layer_0 
        GetVal = extruders[extruder_id].getProperty("speed_layer_0", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("speed_layer_0", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} mm/s".format(Val = GetVal)        
        #   skirt_brim_speed 
        GetVal = extruders[extruder_id].getProperty("skirt_brim_speed", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("skirt_brim_speed", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} mm/s".format(Val = GetVal)

        #   acceleration_enabled 
        GetVal = extruders[extruder_id].getProperty("acceleration_enabled", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("acceleration_enabled", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "[{Val}]".format(Val = GetVal)
        #   acceleration_print 
        GetVal = extruders[extruder_id].getProperty("acceleration_print", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("acceleration_print", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,10) + "{Val} mm/s2".format(Val = GetVal)
        #   acceleration_travel 
        GetVal = extruders[extruder_id].getProperty("acceleration_travel", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("acceleration_travel", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,10) + "{Val} mm/s2".format(Val = GetVal)
            
        #   jerk_enabled 
        GetVal = extruders[extruder_id].getProperty("jerk_enabled", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("jerk_enabled", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "[{Val}]".format(Val = GetVal)
         #   jerk_print 
        GetVal = extruders[extruder_id].getProperty("jerk_print", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("jerk_print", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,10) + "{Val} mm/s3".format(Val = GetVal)           
            
        #   -----------------------------------  travel ----------------------------- 
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("travel", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSect(GetLabel)

        #   retraction_combing
        GetValStr = extruders[extruder_id].getProperty("retraction_combing", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("retraction_combing", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + GetValStr
        #   travel_retract_before_outer_wall
        GetVal = extruders[extruder_id].getProperty("travel_retract_before_outer_wall", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("travel_retract_before_outer_wall", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,20) + "[{Val}]".format(Val = GetVal)
        #   travel_avoid_other_parts
        GetVal = extruders[extruder_id].getProperty("travel_avoid_other_parts", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("travel_avoid_other_parts", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,20) + "[{Val}]".format(Val = GetVal)
        #   travel_avoid_supports
        GetVal = extruders[extruder_id].getProperty("travel_avoid_supports", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("travel_avoid_supports", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,20) + "[{Val}]".format(Val = GetVal)
        #   travel_avoid_distance
        GetVal = extruders[extruder_id].getProperty("travel_avoid_distance", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("travel_avoid_distance", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,20) + "{Val} mm".format(Val = GetVal)
                                                                                                        
        #   retraction_hop_enabled
        GetVal = extruders[extruder_id].getProperty("retraction_hop_enabled", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("retraction_hop_enabled", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,20) + "[{Val}]".format(Val = GetVal)
        #   retraction_hop
        GetVal = extruders[extruder_id].getProperty("retraction_hop", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("retraction_hop", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,20) + "{Val} mm".format(Val = GetVal)
            
        #   -----------------------------------  cooling ----------------------------- 
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("cooling", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSect(GetLabel)

        #   cool_fan_enabled
        GetVal = extruders[extruder_id].getProperty("cool_fan_enabled", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("cool_fan_enabled", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "[{Val}]".format(Val = GetVal)           
        #   cool_fan_speed
        GetVal = extruders[extruder_id].getProperty("cool_fan_speed", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("cool_fan_speed", "label")
        replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} %".format(Val = GetVal)    
        #   cool_fan_speed_0
        GetVal = extruders[extruder_id].getProperty("cool_fan_speed_0", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("cool_fan_speed_0", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} %".format(Val = GetVal) 		
        #   cool_fan_full_layer
        GetVal = extruders[extruder_id].getProperty("cool_fan_full_layer", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("cool_fan_full_layer", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val}".format(Val = GetVal)
        #   cool_min_layer_time
        GetVal = extruders[extruder_id].getProperty("cool_min_layer_time", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("cool_min_layer_time", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} s".format(Val = GetVal)
        #   cool_min_speed
        GetVal = extruders[extruder_id].getProperty("cool_min_speed", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("cool_min_speed", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} mm/s".format(Val = GetVal)      
        #   cool_lift_head
        GetVal = extruders[extruder_id].getProperty("cool_lift_head", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("cool_lift_head", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "[{Val}]".format(Val = GetVal)
            
        #   -----------------------------------  support ------------------------------ 
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("support", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSect(GetLabel)
            
        #   support_enable 
        GetVal = extruders[extruder_id].getProperty("support_enable", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("support_enable", "label")
        replace_string = replace_string + self.SetSpace(GetLabel,0) + "[{Val}]".format(Val = GetVal)
        #   support_type
        GetValStr = extruders[extruder_id].getProperty("support_type", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("support_type", "label")
        replace_string = replace_string + self.SetSpace(GetLabel,0) + GetValStr
        #   support_angle
        GetVal = extruders[extruder_id].getProperty("support_angle", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("support_angle", "label")
        replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val}°".format(Val = GetVal)
        #   support_pattern
        GetValStr = extruders[extruder_id].getProperty("support_pattern", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("support_pattern", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + GetValStr
        #   support_connect_zigzags
        GetVal = extruders[extruder_id].getProperty("support_connect_zigzags", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("support_connect_zigzags", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "[{Val}]".format(Val = GetVal)
                                                                                                         
        #   support_infill_rate
        GetVal = extruders[extruder_id].getProperty("support_infill_rate", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("support_infill_rate", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} %".format(Val = GetVal)
        #   support_z_distance
        GetVal = extruders[extruder_id].getProperty("support_z_distance", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("support_z_distance", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,5) + "{Val} mm".format(Val = GetVal)
        #   support_xy_distance
        GetVal = extruders[extruder_id].getProperty("support_xy_distance", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("support_xy_distance", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,5) + "{Val} mm".format(Val = GetVal)        
        #   support_xy_overrides_z
        GetValStr = extruders[extruder_id].getProperty("support_xy_overrides_z", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("support_xy_overrides_z", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,5) + GetValStr
        #   support_interface_enable
        GetVal = extruders[extruder_id].getProperty("support_interface_enable", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("support_interface_enable", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "[{Val}]".format(Val = GetVal)
        #   support_roof_enable
        GetVal = extruders[extruder_id].getProperty("support_roof_enable", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("support_roof_enable", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "[{Val}]".format(Val = GetVal)            
        #   support_interface_height
        GetVal = extruders[extruder_id].getProperty("support_interface_height", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("support_interface_height", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} mm".format(Val = GetVal)
        #   support_roof_height
        GetVal = extruders[extruder_id].getProperty("support_roof_height", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("support_roof_height", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} mm".format(Val = GetVal)
        #   support_interface_skip_height
        GetVal = extruders[extruder_id].getProperty("support_interface_skip_height", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("support_interface_skip_height", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} mm".format(Val = GetVal)
        #   support_interface_density
        GetVal = extruders[extruder_id].getProperty("support_interface_density", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("support_interface_density", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} %".format(Val = GetVal)            
        #   support_interface_pattern
        GetValStr = extruders[extruder_id].getProperty("support_interface_pattern", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("support_interface_pattern", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + GetValStr
            

        #   -----------------------------------  platform_adhesion ----------------------------- 
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("platform_adhesion", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSect(GetLabel)
            
        #   adhesion_type
        GetValStr = extruders[extruder_id].getProperty("adhesion_type", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("adhesion_type", "label")
        replace_string = replace_string + self.SetSpace(GetLabel,0) + GetValStr
         #   brim_width 
        GetVal = extruders[extruder_id].getProperty("brim_width", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("brim_width", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "{Val} mm".format(Val = GetVal)

         #   -----------------------------------  meshfix ------------------------------ 
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("meshfix", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSect(GetLabel)
        #   meshfix_union_all
        GetVal = extruders[extruder_id].getProperty("meshfix_union_all", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("meshfix_union_all", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "[{Val}]".format(Val = GetVal)

        #   meshfix_union_all_remove_holes
        GetVal = extruders[extruder_id].getProperty("meshfix_union_all_remove_holes", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("meshfix_union_all_remove_holes", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "[{Val}]".format(Val = GetVal)
                                                                                                         
        #   -----------------------------------  blackmagic ------------------------------ 
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("blackmagic", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSect(GetLabel)

         #   print_sequence
        GetValStr = extruders[extruder_id].getProperty("print_sequence", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("print_sequence", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + GetValStr
            
         #   magic_spiralize
        GetVal = extruders[extruder_id].getProperty("magic_spiralize", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("magic_spiralize", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "[{Val}]".format(Val = GetVal)

        #   -----------------------------------  experimental ------------------------------ 
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("experimental", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSect(GetLabel)
            
        #   support_tree_enable 
        GetVal = extruders[extruder_id].getProperty("support_tree_enable", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("support_tree_enable", "label")
        replace_string = replace_string + self.SetSpace(GetLabel,0) + "[{Val}]".format(Val = GetVal)
        #   support_tree_angle
        GetVal = extruders[extruder_id].getProperty("support_tree_angle", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("support_tree_angle", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,5) + "{Val} °".format(Val = GetVal)
        #   support_tree_branch_distance
        GetVal = extruders[extruder_id].getProperty("support_tree_branch_distance", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("support_tree_branch_distance", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,5) + "{Val} mm".format(Val = GetVal)
        #   support_tree_branch_diameter
        GetVal = extruders[extruder_id].getProperty("support_tree_branch_diameter", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("support_tree_branch_diameter", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,5) + "{Val} mm".format(Val = GetVal)
        #   support_tree_branch_diameter_angle
        GetVal = extruders[extruder_id].getProperty("support_tree_branch_diameter_angle", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("support_tree_branch_diameter_angle", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,5) + "{Val} °".format(Val = GetVal)
            
        #   coasting_enable
        GetVal = extruders[extruder_id].getProperty("coasting_enable", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("coasting_enable", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "[{Val}]".format(Val = GetVal)
        #   coasting_volume
        GetVal = extruders[extruder_id].getProperty("coasting_volume", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("coasting_volume", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,5) + "{Val} mm3".format(Val = GetVal)
        #   coasting_speed
        GetVal = extruders[extruder_id].getProperty("coasting_speed", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("coasting_speed", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,5) + "{Val} mm/s".format(Val = GetVal)

        # adaptive_layer_height_enabled
        adaptive_layer = Application.getInstance().getGlobalContainerStack().getProperty("adaptive_layer_height_enabled", "value")
        GetVal = adaptive_layer
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("adaptive_layer_height_enabled", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "[{Val}]".format(Val = GetVal)
        #   adaptive_layer_height_variation
        GetVal = extruders[extruder_id].getProperty("adaptive_layer_height_variation", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("adaptive_layer_height_variation", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,5) + "{Val} mm".format(Val = GetVal)
        #   adaptive_layer_height_variation_step
        GetVal = extruders[extruder_id].getProperty("adaptive_layer_height_variation_step", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("adaptive_layer_height_variation_step", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,5) + "{Val} mm".format(Val = GetVal)
            
        #   bridge_settings_enabled
        GetVal = extruders[extruder_id].getProperty("bridge_settings_enabled", "value")
        GetLabel = Application.getInstance().getGlobalContainerStack().getProperty("bridge_settings_enabled", "label")
        if adv_desc :
            replace_string = replace_string + self.SetSpace(GetLabel,0) + "[{Val}]".format(Val = GetVal)

        #   Fin de commentaire 
        replace_string = replace_string + "\n;==============================================================================="
        
        for layer_number, layer in enumerate(data):
            data[layer_number] = re.sub(search_regex, replace_string, layer) #Replace all.

        return data
    
