# Copyright (c) 2023 GregValiant (Greg Foresi)
#   This Post-Processing Plugin is released under the terms of the AGPLv3 or higher.
#   This post processor adds most of the Cura settings to the end of the Gcode file independent of quality changes.
#   A single extruder print will add about 308 lines to the gcode.  A dual extruder print will add about 420 lines.
#   My thanks to @AHoeben and @Dustin for their help.

from UM.Application import Application
import UM.Util
from ..Script import Script
import time
from UM.Qt.Duration import DurationFormat
import configparser
from UM.Preferences import Preferences

class AddCuraSettings(Script):
    """Add Cura settings to the g-code.
    """

    def getSettingDataString(self):
        return """{
            "name": "Add Cura Settings",
            "key": "AddCuraSettings",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "all_or_some":
                {
                    "label": "All or Some...",
                    "description": "Include all categories or you can pick which categories to include.  Selecting All will add about 310 lines for a single extruder print and about 420 lines for a dual extruder print.  This post processor should be the last on the Post Process list.",
                    "type": "enum",
                    "options": {
                        "all_settings": "All Categories",
                        "pick_settings": "Select Categories"},
                    "default_value": "all_settings"
                },
                "general_set":
                {
                    "label": "General",
                    "description": "The General settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "machine_set":
                {
                    "label": "Machine",
                    "description": "The machine settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "quality_set":
                {
                    "label": "Quality",
                    "description": "The Quality settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "wall_set":
                {
                    "label": "Wall",
                    "description": "The Wall settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "topbot_set":
                {
                    "label": "Top/Bottom",
                    "description": "The Top/Bottom settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "infill_set":
                {
                    "label": "Infill",
                    "description": "The Infill settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "material_set":
                {
                    "label": "Material",
                    "description": "The Material settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "speed_set":
                {
                    "label": "Speed",
                    "description": "The Speed settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "travel_set":
                {
                    "label": "Travel",
                    "description": "The Travel settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "cooling_set":
                {
                    "label": "Cooling",
                    "description": "The Cooling settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "support_set":
                {
                    "label": "Support",
                    "description": "The Support settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "adhesion_set":
                {
                    "label": "Build Plate Adhesion",
                    "description": "The Build Plate Adhesion settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "dualext_set":
                {
                    "label": "Dual-Extruder",
                    "description": "The Multi-Extruder settings are only available for multi-extruder printers.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "meshfix_set":
                {
                    "label": "Mesh Fixes",
                    "description": "The Mesh Fixes settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "special_set":
                {
                    "label": "Special Modes",
                    "description": "The Special Mode settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "experimental_set":
                {
                    "label": "Experimental",
                    "description": "The Experimental settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "postprocess_set":
                {
                    "label": "PostProcessors",
                    "description": "Active Post Processor settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                }
            }
        }"""

    def execute(self, data): #Application.getInstance().getPrintInformation().
        mycura = Application.getInstance().getGlobalContainerStack()
        currency_symbol = Application.getInstance().getPreferences().getValue("cura/currency")
        extruderMgr = Application.getInstance().getExtruderManager()
        extruder = Application.getInstance().getGlobalContainerStack().extruderList
        all_or_some = str(self.getSettingValueByKey("all_or_some"))
        machine_extruder_count = int(mycura.getProperty("machine_extruder_count", "value"))
        setting_data = ";\n;  <<< Cura User Settings >>>\n"
        #Extruder Assignments-------------------------------------------------------
        wall_extruder_nr = int(mycura.getProperty("wall_extruder_nr", "value"))
        if wall_extruder_nr == -1: wall_extruder_nr = 0
        wall_0_extruder_nr = int(mycura.getProperty("wall_0_extruder_nr", "value"))
        if wall_0_extruder_nr == -1: wall_0_extruder_nr = 0
        wall_x_extruder_nr = int(mycura.getProperty("wall_x_extruder_nr", "value"))
        if wall_x_extruder_nr == -1: wall_x_extruder_nr = 0
        roofing_extruder_nr = int(mycura.getProperty("roofing_extruder_nr", "value"))
        if roofing_extruder_nr == -1: roofing_extruder_nr = 0
        top_bottom_extruder_nr = int(mycura.getProperty("top_bottom_extruder_nr", "value"))
        if top_bottom_extruder_nr == -1: top_bottom_extruder_nr = 0
        infill_extruder_nr = int(mycura.getProperty("infill_extruder_nr", "value"))
        if infill_extruder_nr == -1: infill_extruder_nr = 0
        support_extruder_nr = int(mycura.getProperty("support_extruder_nr", "value"))
        if support_extruder_nr == -1: support_extruder_nr = 0
        support_infill_extruder_nr = int(mycura.getProperty("support_infill_extruder_nr", "value"))
        if support_infill_extruder_nr == -1: support_infill_extruder_nr = 0
        support_extruder_nr_layer_0 = int(mycura.getProperty("support_extruder_nr_layer_0", "value"))
        if support_extruder_nr_layer_0 == -1: support_extruder_nr_layer_0 = 0
        support_interface_extruder_nr = int(mycura.getProperty("support_interface_extruder_nr", "value"))
        if support_interface_extruder_nr == -1: support_interface_extruder_nr = 0
        support_roof_extruder_nr = int(mycura.getProperty("support_roof_extruder_nr", "value"))
        if support_roof_extruder_nr == -1: support_roof_extruder_nr = 0
        support_bottom_extruder_nr = int(mycura.getProperty("support_bottom_extruder_nr", "value"))
        if support_bottom_extruder_nr == -1: support_bottom_extruder_nr = 0
        #Compatibility problem with 4.x-------------------------------------------------------
        try:
            skirt_brim_extruder_nr = int(mycura.getProperty("skirt_brim_extruder_nr", "value"))
            if skirt_brim_extruder_nr == -1: skirt_brim_extruder_nr = 0
        except:
            all
        adhesion_extruder_nr = int(mycura.getProperty("adhesion_extruder_nr", "value"))
        if adhesion_extruder_nr == -1: adhesion_extruder_nr = 0

        #General Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("general_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [General]\n"
            setting_data += ";Job Name: " + str(Application.getInstance().getPrintInformation().jobName) + "\n"
            setting_data += ";Print Time: " + str(Application.getInstance().getPrintInformation().currentPrintTime.getDisplayString(DurationFormat.Format.ISO8601)) + "\n"
            setting_data += ";Slice Start Time: " + str(time.strftime("%H:%M:%S")) + " (24hr)\n"
            setting_data += ";Slice Date: " + str(time.strftime("%m-%d-%Y")) + " (mm-dd-yyyy)\n"
            setting_data += ";Slice Day: " + str(["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][int(time.strftime("%w"))]) + "\n"
            filament_amt = Application.getInstance().getPrintInformation().materialLengths
            filament_wt = Application.getInstance().getPrintInformation().materialWeights
            filament_cost = Application.getInstance().getPrintInformation().materialCosts
            for num in range(0,machine_extruder_count):
                setting_data += ";Extruder " + str(num+1) + "\n"
                setting_data += ";  Filament Type: " + str(extruder[num].material.getMetaDataEntry("material", "")) + "\n"
                setting_data += ";  Filament Name: " + str(extruder[num].material.getMetaDataEntry("name", "")) + "\n"
                setting_data += ";  Filament Brand: " + str(extruder[num].material.getMetaDataEntry("brand", "")) + "\n"
                setting_data += ";  Filament Amount: " + str(round(filament_amt[num],2)) + "m\n"
                setting_data += ";  Filament Weight: " + str(round(filament_wt[num],2)) + "gm\n"
                setting_data += ";  Filament Cost: " + currency_symbol + "{:.2f}".format(filament_cost[num]) + "\n"

        #Machine Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("machine_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Machine]\n"
            setting_data += ";Machine Name: " + str(mycura.getProperty("machine_name", "value")) + "\n"
            setting_data += ";Material Diameter: " + str(mycura.getProperty("material_diameter", "value")) + "mm\n"
            setting_data += ";Wait for bed heatup: " + str(mycura.getProperty("material_bed_temp_wait", "value")) + "\n"
            setting_data += ";Wait for Nozzle Heatup: " + str(mycura.getProperty("material_print_temp_wait", "value")) + "\n"
            setting_data += ";Add Print Temp Before StartUp: " + str(mycura.getProperty("material_print_temp_prepend", "value")) + "\n"
            setting_data += ";Add Bed Temp Before StartUp: " + str(mycura.getProperty("material_bed_temp_prepend", "value")) + "\n"
            setting_data += ";Machine Width: " + str(mycura.getProperty("machine_width", "value")) + "mm\n"
            setting_data += ";Machine Depth: " +	str(mycura.getProperty("machine_depth", "value")) + "mm\n"
            setting_data += ";Machine Height: " + str(mycura.getProperty("machine_height", "value")) + "mm\n"
            setting_data += ";Machine Bed Shape: " + str(mycura.getProperty("machine_shape", "value")) + "\n"
            setting_data += ";Machine Bed Heated: " + str(mycura.getProperty("machine_heated_bed", "value")) + "\n"
            setting_data += ";Machine Heated Build Volume: " + str(mycura.getProperty("machine_heated_build_volume", "value")) + "\n"
            setting_data += ";Machine Center is Zero: " + str(mycura.getProperty("machine_center_is_zero", "value")) + "\n"
            setting_data += ";Machine Extruder Count: " + str(mycura.getProperty("machine_extruder_count", "value")) + "\n"
            enabled_list = list([mycura.isEnabled for mycura in mycura.extruderList])
            for num in range(0,len(enabled_list)):
                setting_data += ";  Extruder #" + str(num+1) + " Enabled: " + str(enabled_list[num]) + "\n"
            setting_data += ";Enable Nozzle Temperature Control: " + str(mycura.getProperty("machine_nozzle_temp_enabled", "value")) + "\n"
            setting_data += ";Heat Up Speed: " + str(mycura.getProperty("machine_nozzle_heat_up_speed", "value")) + "\n"
            setting_data += ";Cool Down Speed: " + str(mycura.getProperty("machine_nozzle_cool_down_speed", "value")) + "\n"
            setting_data += ";Minimal Time Standby Temperature: " + str(mycura.getProperty("machine_min_cool_heat_time_window", "value")) + "\n"
            setting_data += ";G-code Flavor: " + str(mycura.getProperty("machine_gcode_flavor", "value")) + "\n"
            setting_data += ";Firmware Retraction: " + str(mycura.getProperty("machine_firmware_retract", "value")) + "\n"
            if machine_extruder_count > 1:
                setting_data += ";Extruders Share Heater: " + str(mycura.getProperty("machine_extruders_share_heater", "value")) + "\n"
                setting_data += ";Extruders Share Nozzle: " + str(mycura.getProperty("machine_extruders_share_nozzle", "value")) + "\n"
                setting_data += ";Shared Nozzle Initial Retraction: " + str(mycura.getProperty("machine_extruders_shared_nozzle_initial_retraction", "value")) + "\n"
            mach_dis_areas = mycura.getProperty("machine_disallowed_areas", "value")
            templist = ""
            for num in range(0,len(mach_dis_areas)-1):
                templist += str(mach_dis_areas[num]) + ", "
            if templist == "": templist = "None"
            setting_data += ";Disallowed Areas: " + templist + "\n"
            nozzle_dis_areas = mycura.getProperty("nozzle_disallowed_areas", "value")
            templist = ""
            for num in range(0,len(nozzle_dis_areas)-1):
                templist += str(nozzle_dis_areas[num]) + ", "
            if templist == "": templist = "None"
            setting_data += ";Nozzle Disallowed Areas: " + templist + "\n"
            machine_head_with_fans_polygon = mycura.getProperty("machine_head_with_fans_polygon", "value")
            setting_data += ";Print Head Disallowed Area (for One-At-A-Time): " + str(machine_head_with_fans_polygon[0]) + str(machine_head_with_fans_polygon[1]) + str(machine_head_with_fans_polygon[2]) + str(machine_head_with_fans_polygon[3]) + "\n"
            setting_data += ";Gantry Height: " + str(mycura.getProperty("gantry_height", "value")) + "\n"
            setting_data += ";Nozzle Identifier: " + str(mycura.getProperty("machine_nozzle_id", "value")) + "\n"
            for num in range(0,machine_extruder_count):
                setting_data += ";Extruder #" + str(num+1) + " Nozzle Size: " + str(extruder[num].getProperty("machine_nozzle_size", "value")) + "\n"
            setting_data += ";Offset Extruder: " + str(mycura.getProperty("machine_use_extruder_offset_to_offset_coords", "value")) + "\n"
            setting_data += ";Extruder Prime Z: " + str(mycura.getProperty("extruder_prime_pos_z", "value")) + "\n"
            setting_data += ";Absolute Extruder Prime: " + str(mycura.getProperty("extruder_prime_pos_abs", "value")) + "\n"
            setting_data += ";Max Feedrate X: " + str(mycura.getProperty("machine_max_feedrate_x", "value")) + "mm/sec\n"
            setting_data += ";Max Feedrate Y: " + str(mycura.getProperty("machine_max_feedrate_y", "value")) + "mm/sec\n"
            setting_data += ";Max Feedrate Z: " + str(mycura.getProperty("machine_max_feedrate_z", "value")) + "mm/sec\n"
            setting_data += ";Max Feedrate E: " + str(mycura.getProperty("machine_max_feedrate_e", "value")) + "mm/sec\n"
            setting_data += ";Max Accel X: " + str(mycura.getProperty("machine_max_acceleration_x", "value")) + "mm/sec²\n"
            setting_data += ";Max Accel Y: " + str(mycura.getProperty("machine_max_acceleration_y", "value")) + "mm/sec²\n"
            setting_data += ";Max Accel Z: " + str(mycura.getProperty("machine_max_acceleration_z", "value")) + "mm/sec²\n"
            setting_data += ";Max Accel E: " + str(mycura.getProperty("machine_max_acceleration_e", "value")) + "mm/sec²\n"
            setting_data += ";Default Machine Accel: " + str(mycura.getProperty("machine_acceleration", "value")) + "mm/sec²\n"
            setting_data += ";Default XY Jerk: " + str(mycura.getProperty("machine_max_jerk_xy", "value")) + "mm/sec\n"
            setting_data += ";Default Z Jerk: " + str(mycura.getProperty("machine_max_jerk_z", "value")) + "mm/sec\n"
            setting_data += ";Default E Jerk: " + str(mycura.getProperty("machine_max_jerk_e", "value")) + "mm/sec\n"
            setting_data += ";RepRap 0-1 Fan Scale: " + str(bool(extruder[0].getProperty("machine_scale_fan_speed_zero_to_one", "value"))) + "\n"

        #Quality Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("quality_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Quality]\n"
            setting_data += ";Layer Height: " + str(mycura.getProperty("layer_height", "value")) + "mm\n"
            setting_data += ";Initial Layer Height: " + str(mycura.getProperty("layer_height_0", "value")) + "mm\n"
            for num in range(0,machine_extruder_count):
                setting_data += ";Extruder " + str(num+1) + "\n"
                setting_data += ";  Line Width: " + str(extruder[num].getProperty("line_width", "value")) + "mm\n"
            setting_data += ";Wall Line Width (Ext" + str(wall_extruder_nr+1) + "): " + str(extruder[wall_extruder_nr].getProperty("wall_line_width", "value")) + "mm\n"
            setting_data += ";Outer-Wall Line Width (Ext" + str(wall_0_extruder_nr+1) + "): " + str(extruder[wall_0_extruder_nr].getProperty("wall_line_width_0", "value")) + "mm\n"
            setting_data += ";Inner-Wall Line Width (Ext" + str(wall_x_extruder_nr+1) + "): " + str(extruder[wall_x_extruder_nr].getProperty("wall_line_width_x", "value")) + "mm\n"
            setting_data += ";Skin Line Width (Ext" + str(top_bottom_extruder_nr+1) + "): " + str(extruder[top_bottom_extruder_nr].getProperty("skin_line_width", "value")) + "mm\n"
            setting_data += ";Infill Line Width (Ext" + str(infill_extruder_nr+1) + "): " + str(extruder[infill_extruder_nr].getProperty("infill_line_width", "value")) + "mm\n"
            try:
                setting_data += ";Skirt/Brim Line Width (Ext" + str(skirt_brim_extruder_nr+1) + "): " + str(extruder[skirt_brim_extruder_nr].getProperty("skirt_brim_line_width", "value")) + "mm\n"
            except:
                all
            setting_data += ";Support Line Width (Ext" + str(support_extruder_nr+1) + "): " + str(extruder[support_extruder_nr].getProperty("support_line_width", "value")) + "mm\n"
            setting_data += ";Support Interface Line Width (Ext" + str(support_interface_extruder_nr+1) + "): " + str(extruder[support_interface_extruder_nr].getProperty("support_interface_line_width", "value")) + "mm\n"
            setting_data += ";Support Roof Line Width (Ext" + str(support_roof_extruder_nr+1) + "): " + str(extruder[support_roof_extruder_nr].getProperty("support_roof_line_width", "value")) + "mm\n"
            setting_data += ";Support Floor Line Width (Ext" + str(support_bottom_extruder_nr+1) + "): " + str(extruder[support_bottom_extruder_nr].getProperty("support_bottom_line_width", "value")) + "mm\n"
            if bool(mycura.getProperty("prime_tower_enable", "value")) and machine_extruder_count>1:
                setting_data += ";Prime Tower Line Width: " + str(mycura.getProperty("prime_tower_line_width", "value")) + "mm\n"
            setting_data += ";Init Layer Line Width: " + str(mycura.getProperty("initial_layer_line_width_factor", "value")) + "%\n"

        #Wall Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("wall_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Walls]\n"
            setting_data += ";Wall Extruder Nr: " + str(wall_extruder_nr) + "\n"
            setting_data += ";Outer-Wall Extruder Nr: " + str(wall_0_extruder_nr) + "\n"
            setting_data += ";Inner-Wall Extruder Nr: " + str(wall_x_extruder_nr) + "\n"
            setting_data += ";Wall Thickness: " + str(round(mycura.getProperty("wall_thickness", "value"),2)) + "mm\n"
            setting_data += ";Wall Line Count: " + str(mycura.getProperty("wall_line_count", "value")) + "\n"
            setting_data += ";Outer-Wall Wipe Dist: " + str(mycura.getProperty("wall_0_wipe_dist", "value")) + "mm\n"
            setting_data += ";Wall Order: " + str(extruder[0].getProperty("inset_direction", "value")) + "\n"
            setting_data += ";Alternate Extra Wall: " + str(mycura.getProperty("alternate_extra_perimeter", "value")) + "\n"
            setting_data += ";Minimum Wall Line Width: " + str(mycura.getProperty("min_wall_line_width", "value")) + "mm\n"
            setting_data += ";Print Thin Walls: " + str(mycura.getProperty("fill_outline_gaps", "value")) + "\n"
            setting_data += ";Horizontal Expansion: " + str(mycura.getProperty("xy_offset", "value")) + "mm\n"
            setting_data += ";Initial Layer Horiz Expansion: " + str(mycura.getProperty("xy_offset_layer_0", "value")) + "mm\n"
            setting_data += ";Hole Horizontal Expansion: " + str(mycura.getProperty("hole_xy_offset", "value")) + "mm\n"
            setting_data += ";Z Seam Type: " + str(mycura.getProperty("z_seam_type", "value")) + "\n"
            setting_data += ";Z Seam Position: " + str(mycura.getProperty("z_seam_position", "value")) + "\n"
            setting_data += ";Z Seam X: " + str(mycura.getProperty("z_seam_x", "value")) + "\n"
            setting_data += ";Z Seam Y: " + str(mycura.getProperty("z_seam_y", "value")) + "\n"
            setting_data += ";Z Seam Corner: " + str(mycura.getProperty("z_seam_corner", "value")) + "\n"
            setting_data += ";Z Seam Relative: " + str(mycura.getProperty("z_seam_relative", "value")) + "\n"

        #Top/Bottom Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("topbot_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Top/Bottom]\n"
            setting_data += ";Top Surface Skin Extruder: " + str(roofing_extruder_nr) + "\n"
            setting_data += ";Top Surface Skin Count: " + str(mycura.getProperty("roofing_layer_count", "value")) + "\n"
            setting_data += ";Top Surface Skin Line Width: " + str(extruder[roofing_extruder_nr].getProperty("roofing_line_width", "value")) + "mm\n"
            setting_data += ";Top Surface Skin Pattern: " + str(mycura.getProperty("roofing_pattern", "value")) + "\n"
            setting_data += ";Top Surface Monotonic: " + str(mycura.getProperty("roofing_monotonic", "value")) + "\n"
            setting_data += ";Top Surface Skin Line Directions: " + str(extruder[roofing_extruder_nr].getProperty("roofing_angles", "value")) + "°\n"
            setting_data += ";Top/Bottom Extruder: " + str(top_bottom_extruder_nr) + "\n"
            setting_data += ";Top/Bottom Thickness: " + str(round(mycura.getProperty("top_bottom_thickness", "value"),2)) + "mm\n"
            setting_data += ";Top Thickness: " + str(round(mycura.getProperty("top_thickness", "value"),2)) + "mm\n"
            setting_data += ";Top Layers: " + str(mycura.getProperty("top_layers", "value")) + "\n"
            setting_data += ";Bottom Thickness: " + str(round(mycura.getProperty("bottom_thickness", "value"),2)) + "mm\n"
            setting_data += ";Bottom Layers: " + str(mycura.getProperty("bottom_layers", "value")) + "\n"
            setting_data += ";Initial Bottom Layers: " + str(mycura.getProperty("initial_bottom_layers", "value")) + "\n"
            setting_data += ";Top/Bottom Pattern: " + str(extruder[top_bottom_extruder_nr].getProperty("top_bottom_pattern", "value")) + "\n"
            setting_data += ";Initial Top/Bottom Pattern: " + str(mycura.getProperty("top_bottom_pattern_0", "value")) + "\n"
            setting_data += ";Monotonic Top/Bottom: " + str(extruder[top_bottom_extruder_nr].getProperty("skin_monotonic", "value")) + "\n"
            setting_data += ";Top/Bottom Line Directions: " + str(extruder[top_bottom_extruder_nr].getProperty("skin_angles", "value")) + "°\n"
            setting_data += ";Extra Skin Wall Count: " + str(mycura.getProperty("skin_outline_count", "value")) + "\n"
            setting_data += ";Ironing Enabled: " + str(extruder[top_bottom_extruder_nr].getProperty("ironing_enabled", "value")) + "\n"
            if bool(extruder[top_bottom_extruder_nr].getProperty("ironing_enabled", "value")):
                setting_data += ";  Ironing Top Layer Only: " + str(extruder[0].getProperty("ironing_only_highest_layer", "value")) + "\n"
                setting_data += ";  Ironing Pattern: " + str(mycura.getProperty("ironing_pattern", "value")) + "\n"
                setting_data += ";  Ironing Monotonic: " + str(extruder[top_bottom_extruder_nr].getProperty("ironing_monotonic", "value")) + "\n"
                setting_data += ";  Ironing Flow: " + str(extruder[top_bottom_extruder_nr].getProperty("ironing_flow", "value")) + "%\n"

        #Infill Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("infill_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Infill]\n"
            setting_data += ";Infill Extruder: " + str(infill_extruder_nr) + "\n"
            setting_data += ";Infill Density: " + str(extruder[infill_extruder_nr].getProperty("infill_sparse_density", "value")) + "%\n"
            setting_data += ";Infill Pattern: " + str(extruder[infill_extruder_nr].getProperty("infill_pattern", "value")) + "\n"
            setting_data += ";Infill Line Directions: " + str(extruder[infill_extruder_nr].getProperty("infill_angles", "value")) + "°\n"
            setting_data += ";Infill Line Multiplier: " + str(extruder[infill_extruder_nr].getProperty("infill_multiplier", "value")) + "\n"
            setting_data += ";Infill Wall Line Count: " + str(extruder[infill_extruder_nr].getProperty("infill_wall_line_count", "value")) + "\n"
            setting_data += ";Infill Layer Thickness: " + str(extruder[infill_extruder_nr].getProperty("infill_sparse_thickness", "value")) + "mm\n"
            setting_data += ";Infill Steps: " + str(extruder[infill_extruder_nr].getProperty("gradual_infill_steps", "value")) + "\n"
            setting_data += ";Infill Before Walls: " + str(extruder[infill_extruder_nr].getProperty("infill_before_walls", "value")) + "\n"
            setting_data += ";Infill As Support: " + str(extruder[infill_extruder_nr].getProperty("infill_support_enabled", "value")) + "\n"
            setting_data += ";Infill Support Angle: " + str(extruder[infill_extruder_nr].getProperty("infill_support_angle", "value")) + "°\n"
            setting_data += ";Infill Lightning Support Angle: " + str(extruder[infill_extruder_nr].getProperty("lightning_infill_support_angle", "value")) + "°\n"

        #Material Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("material_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Material]\n"
            if bool(mycura.getProperty("machine_heated_build_volume", "value")):
                setting_data += ";Build Volume Temp: " + str(mycura.getProperty("build_volume_temperature", "value")) + "°\n"
            setting_data += ";Print Cool Down Speed: " + str(mycura.getProperty("material_extrusion_cool_down_speed", "value")) + "mm/sec\n"
            setting_data += ";Print Bed Temp: " + str(mycura.getProperty("material_bed_temperature", "value")) + "°\n"
            setting_data += ";Print Bed Temp Layer 0: " + str(mycura.getProperty("material_bed_temperature_layer_0", "value")) + "°\n"
            for num in range(0,machine_extruder_count):
                setting_data += ";Extruder " + str(num+1) + "\n"
                setting_data += ";  Print Temp: " + str(extruder[num].getProperty("material_print_temperature", "value")) + "°\n"
                setting_data += ";  Print Temp Initial Layer: " + str(extruder[num].getProperty("material_print_temperature_layer_0", "value")) + "°\n"
                setting_data += ";  Print Initial Temp: " + str(extruder[num].getProperty("material_initial_print_temperature", "value")) + "°\n"
                setting_data += ";  Print Final Temp: " + str(extruder[num].getProperty("material_final_print_temperature", "value")) + "°\n"
                setting_data += ";  Material Flow: " + str(extruder[num].getProperty("material_flow", "value")) + "%\n"
                setting_data += ";  Wall Flow: " + str(extruder[num].getProperty("wall_material_flow", "value")) + "%\n"
                setting_data += ";  Outer-Wall Flow: " + str(extruder[num].getProperty("wall_0_material_flow", "value")) + "%\n"
                setting_data += ";  Inner-Wall Flow: " + str(extruder[num].getProperty("wall_x_material_flow", "value")) + "%\n"
                setting_data += ";  Skin Flow: " + str(extruder[num].getProperty("skin_material_flow", "value")) + "%\n"
                setting_data += ";  Top Sufrace Skin Flow: " + str(extruder[num].getProperty("roofing_material_flow", "value")) + "%\n"
                setting_data += ";  Infill Flow: " + str(extruder[num].getProperty("infill_material_flow", "value")) + "%\n"
                setting_data += ";  Skirt/Brim Flow: " + str(extruder[num].getProperty("skirt_brim_material_flow", "value")) + "%\n"
                setting_data += ";  Support Flow: " + str(extruder[num].getProperty("support_material_flow", "value")) + "%\n"
                setting_data += ";  Support Interface Flow: " + str(extruder[num].getProperty("support_interface_material_flow", "value")) + "%\n"
                setting_data += ";  Support Roof Interface Flow: " + str(extruder[num].getProperty("support_roof_material_flow", "value")) + "%\n"
                setting_data += ";  Support Bottom Interface Flow: " + str(extruder[num].getProperty("support_bottom_material_flow", "value")) + "%\n"
                if bool(mycura.getProperty("prime_tower_enable", "value")) and machine_extruder_count > 1:
                    setting_data += ";  Prime Tower Flow: " + str(extruder[num].getProperty("prime_tower_flow", "value")) + "%\n"
                setting_data += ";  Initial Layer Flow: " + str(extruder[num].getProperty("material_flow_layer_0", "value")) + "%\n"
                setting_data += ";  Initial Layer Inner-Wall Flow: " + str(extruder[num].getProperty("wall_x_material_flow_layer_0", "value")) + "%\n"
                setting_data += ";  Initial Layer Outer-Wall Flow: " + str(extruder[num].getProperty("wall_0_material_flow_layer_0", "value")) + "%\n"
                setting_data += ";  Initial Layer Skin Flow: " + str(extruder[num].getProperty("skin_material_flow_layer_0", "value")) + "%\n"
                setting_data += ";  Material Standby Temp: " + str(extruder[num].getProperty("material_standby_temperature", "value")) + "°\n"

        #Speed Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("speed_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Speed]\n"
            for num in range(0,machine_extruder_count):
                setting_data += ";Extruder " + str(num+1) + "\n"
                setting_data += ";  Speed Print: " + str(extruder[num].getProperty("speed_print", "value")) + "mm/sec\n"
                setting_data += ";  Speed Infill: " + str(extruder[num].getProperty("speed_infill", "value")) + "mm/sec\n"
                setting_data += ";  Speed Walls: " + str(extruder[num].getProperty("speed_wall", "value")) + "mm/sec\n"
                setting_data += ";  Speed Outer-Walls: " + str(extruder[num].getProperty("speed_wall_0", "value")) + "mm/sec\n"
                setting_data += ";  Speed Inner-Walls: " + str(extruder[num].getProperty("speed_wall_x", "value")) + "mm/sec\n"
                setting_data += ";  Speed Top Skins: " + str(extruder[num].getProperty("speed_roofing", "value")) + "mm/sec\n"
                setting_data += ";  Speed Top/Bottom: " + str(extruder[num].getProperty("speed_topbottom", "value")) + "mm/sec\n"
                setting_data += ";  Speed Travel: " + str(extruder[num].getProperty("speed_travel", "value")) + "mm/sec\n"
                setting_data += ";  Speed Initial Layer: " + str(extruder[num].getProperty("speed_layer_0", "value")) + "mm/sec\n"
                setting_data += ";  Speed Print Initial Layer: " + str(extruder[num].getProperty("speed_print_layer_0", "value")) + "mm/sec\n"
                setting_data += ";  Speed Travel Initial Layer: " + str(extruder[num].getProperty("speed_travel_layer_0", "value")) + "mm/sec\n"
                setting_data += ";  Speed Z-Hop: " + str(extruder[num].getProperty("speed_z_hop", "value")) + "mm/sec\n"
                setting_data += ";  Acceleration Enabled: " + str(extruder[num].getProperty("acceleration_enabled", "value")) + "\n"
                setting_data += ";  Acceleration Print: " + str(extruder[num].getProperty("acceleration_print", "value")) + "mm/sec²\n"
                setting_data += ";  Acceleration Travel: " + str(extruder[num].getProperty("acceleration_travel", "value")) + "mm/sec²\n"
                setting_data += ";  Jerk Enabled: " + str(extruder[num].getProperty("jerk_enabled", "value")) + "\n"
                setting_data += ";  Jerk Print: " + str(extruder[num].getProperty("jerk_print", "value")) + "mm/sec\n"
                setting_data += ";  Jerk Travel: " + str(extruder[num].getProperty("jerk_travel", "value")) + "mm/sec\n"

            setting_data += ";Speed Support: " + str(extruder[support_extruder_nr].getProperty("speed_support", "value")) + "mm/sec\n"
            setting_data += ";Speed Support Infill: " + str(extruder[support_infill_extruder_nr].getProperty("speed_support_infill", "value")) + "mm/sec\n"
            setting_data += ";Speed Support Interface: " + str(extruder[support_interface_extruder_nr].getProperty("speed_support_interface", "value")) + "mm/sec\n"
            setting_data += ";Speed Support Interface Roof: " + str(extruder[support_roof_extruder_nr].getProperty("speed_support_roof", "value")) + "mm/sec\n"
            setting_data += ";Speed Support Interface Bottom: " + str(extruder[support_bottom_extruder_nr].getProperty("speed_support_bottom", "value")) + "mm/sec\n"
            #Compatibility problem with 4.x--------------------------------------------------------------
            try:
                setting_data += ";Speed Skirt/Brim: " + str(extruder[skirt_brim_extruder_nr].getProperty("skirt_brim_speed", "value")) + "mm/sec\n"
            except:
                all
            if bool(mycura.getProperty("prime_tower_enable", "value")) and machine_extruder_count >1:
                setting_data += ";Speed Prime Tower: " + str(mycura.getProperty("speed_prime_tower", "value")) + "mm/sec\n"
            setting_data += ";Slower Initial Layers: " + str(mycura.getProperty("speed_slowdown_layers", "value")) + "\n"

        #Travel Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("travel_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Travel]\n"
            for num in range(0,machine_extruder_count):
                setting_data += ";Extruder " + str(num+1) + "\n"
                setting_data += ";  Retraction Enabled: " + str(extruder[num].getProperty("retraction_enable", "value")) + "\n"
                setting_data += ";  Retraction at Layer Change: " + str(extruder[num].getProperty("retract_at_layer_change", "value")) + "\n"
                setting_data += ";  Retraction Distance: " + str(extruder[num].getProperty("retraction_amount", "value")) + "mm\n"
                setting_data += ";  Retraction Speed: " + str(extruder[num].getProperty("retraction_speed", "value")) + "mm/sec\n"
                setting_data += ";  Retraction Retract Speed: " + str(extruder[num].getProperty("retraction_retract_speed", "value")) + "mm/sec\n"
                setting_data += ";  Retraction Prime Speed: " + str(extruder[num].getProperty("retraction_prime_speed", "value")) + "mm/sec\n"
                setting_data += ";  Retraction Extra Prime Volume: " + str(extruder[num].getProperty("retraction_extra_prime_amount", "value")) + "mm³\n"
                setting_data += ";  Retraction Combing: " + str(extruder[num].getProperty("retraction_combing", "value")) + "\n"
                setting_data += ";  Retract Before Outer Wall: " + str(extruder[num].getProperty("travel_retract_before_outer_wall", "value")) + "\n"
                setting_data += ";  Travel Avoid Parts: " + str(extruder[num].getProperty("travel_avoid_other_parts", "value")) + "\n"
                setting_data += ";  Travel Avoid Supports: " + str(extruder[num].getProperty("travel_avoid_supports", "value")) + "\n"
                setting_data += ";  Z-Hops Enabled: " + str(extruder[num].getProperty("retraction_hop_enabled", "value")) + "\n"
                setting_data += ";  Z-Hop Only Over Printed Parts: " + str(extruder[num].getProperty("retraction_hop_only_when_collides", "value")) + "\n"
                setting_data += ";  Z-Hop Height: " + str(extruder[num].getProperty("retraction_hop", "value")) + "mm\n"
                setting_data += ";  Z-Hop After Extruder Switch: " + str(extruder[num].getProperty("retraction_hop_after_extruder_switch", "value")) + "\n"
                setting_data += ";  Z-Hop Height After Extruder Switch: " + str(extruder[num].getProperty("retraction_hop_after_extruder_switch_height", "value")) + "mm\n"

        #Cooling Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("cooling_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Cooling]\n"
            for num in range(0,machine_extruder_count):
                setting_data += ";Extruder " + str(num+1) + "\n"
                setting_data += ";  Cooling Enabled: " + str(extruder[num].getProperty("cool_fan_enabled", "value")) + "\n"
                if bool(extruder[num].getProperty("cool_fan_enabled", "value")):
                    setting_data += ";  Cooling Fan Number: " + str((extruder[num].getProperty("machine_extruder_cooling_fan_number", "value"))) + "\n"
                    setting_data += ";  Cooling Fan Speed: " + str(extruder[num].getProperty("cool_fan_speed", "value")) + "%\n"
                    setting_data += ";  Cooling Fan Minimum Speed: " + str(extruder[num].getProperty("cool_fan_speed_min", "value")) + "%\n"
                    setting_data += ";  Cooling Fan Maximum Speed: " + str(extruder[num].getProperty("cool_fan_speed_max", "value")) + "%\n"
                    setting_data += ";  Cooling Fan Min/Max Threshold: " + str(extruder[num].getProperty("cool_min_layer_time_fan_speed_max", "value")) + "%\n"
                    setting_data += ";  Cooling Fan Initial Speed: " + str(extruder[num].getProperty("cool_fan_speed_0", "value")) + "%\n"
                    setting_data += ";  Cooling Fan Regular Speed at Height: " + str(round(extruder[num].getProperty("cool_fan_full_at_height", "value"),2)) + "mm\n"
                    setting_data += ";  Cooling Fan Regular Speed at Layer: " + str(extruder[num].getProperty("cool_fan_full_layer", "value")) + "\n"
                    setting_data += ";  Cooling Minimum Layer Time: " + str(extruder[num].getProperty("cool_min_layer_time", "value")) + "sec\n"
                    setting_data += ";  Cooling Minimum Print Speed: " + str(extruder[num].getProperty("cool_min_speed", "value")) + "mm/sec\n"
                    setting_data += ";  Lift Head: " + str(extruder[num].getProperty("cool_lift_head", "value")) + "\n"
                    setting_data += ";  Small Layer Print Temperature: " + str(extruder[num].getProperty("cool_min_temperature", "value")) + "°\n"

        #Support Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("support_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Support]\n"
            setting_data += ";Enable Support: " + str(mycura.getProperty("support_enable", "value")) + "\n"
            if bool(mycura.getProperty("support_enable", "value")):
                if machine_extruder_count > 1:
                    setting_data += ";Support Extruder: " + str(support_extruder_nr) + "\n"
                    setting_data += ";Support Infill Extruder: " + str(support_infill_extruder_nr) + "\n"
                    setting_data += ";Support Initial Layer Extruder: " + str(support_extruder_nr_layer_0) + "\n"
                    setting_data += ";Support Interface Extruder: " + str(support_interface_extruder_nr) + "\n"
                    setting_data += ";Support Interface Roof Extruder: " + str(support_roof_extruder_nr) + "\n"
                    setting_data += ";Support Interface Bottom Extruder: " + str(support_bottom_extruder_nr) + "\n"
                setting_data += ";Support Structure: " + str(extruder[support_extruder_nr].getProperty("support_structure", "value")) + "\n"
                setting_data += ";Support Type: " + str(extruder[support_extruder_nr].getProperty("support_type", "value")) + "\n"
                setting_data += ";Support Overhang Angle: " + str(extruder[support_extruder_nr].getProperty("support_angle", "value")) + "°\n"
                setting_data += ";Support Pattern: " + str(extruder[support_infill_extruder_nr].getProperty("support_pattern", "value")) + "\n"
                setting_data += ";Support Wall Count: " + str(extruder[support_extruder_nr].getProperty("support_wall_count", "value")) + "\n"
                setting_data += ";Connect Support Lines: " + str(extruder[support_infill_extruder_nr].getProperty("zig_zaggify_support", "value")) + "\n"
                setting_data += ";Support Density: " + str(extruder[support_infill_extruder_nr].getProperty("support_infill_rate", "value")) + "%\n"
                setting_data += ";Support Infill Line Directions: " + str(extruder[support_infill_extruder_nr].getProperty("support_infill_angles", "value")) + "°\n"
                setting_data += ";Support Brim Enabled: " + str(extruder[support_extruder_nr].getProperty("support_brim_enable", "value")) + "\n"
                setting_data += ";Support Brim Width: " + str(extruder[support_extruder_nr].getProperty("support_brim_width", "value")) + "mm\n"
                setting_data += ";Support Z Distance: " + str(extruder[support_extruder_nr].getProperty("support_z_distance", "value")) + "mm\n"
                setting_data += ";Support Top Distance: " + str(extruder[support_extruder_nr].getProperty("support_top_distance", "value")) + "mm\n"
                setting_data += ";Support Bottom Distance: " + str(extruder[support_extruder_nr].getProperty("support_bottom_distance", "value")) + "mm\n"
                setting_data += ";Support XY Distance: " + str(extruder[support_extruder_nr].getProperty("support_xy_distance", "value")) + "mm\n"
                setting_data += ";Support XY Overrides Z: " + str(extruder[support_extruder_nr].getProperty("upport_xy_overrides_z", "value")) + "\n"
                setting_data += ";Support Horizontal Expansion: " + str(extruder[support_extruder_nr].getProperty("support_offset", "value")) + "mm\n"
                setting_data += ";Support Infill Layer Thickness: " + str(extruder[support_infill_extruder_nr].getProperty("support_infill_sparse_thickness", "value")) + "mm\n"
                setting_data += ";Support Minimum Support Area: " + str(extruder[support_extruder_nr].getProperty("minimum_support_area", "value")) + "mm²\n"
                setting_data += ";Support Fan Enabled: " + str(extruder[support_extruder_nr].getProperty("support_fan_enable", "value")) + "\n"
                setting_data += ";Enable Support Interface: " + str(extruder[support_interface_extruder_nr].getProperty("support_interface_enable", "value")) + "\n"
                if bool(extruder[support_interface_extruder_nr].getProperty("support_interface_enable", "value")):
                    setting_data += ";Support Interface Wall Count: " + str(extruder[support_interface_extruder_nr].getProperty("support_interface_wall_count", "value")) + "\n"
                    setting_data += ";Enable Support Roof: " + str(extruder[support_roof_extruder_nr].getProperty("support_roof_enable", "value")) + "\n"
                    setting_data += ";Enable Support Floor: " + str(extruder[support_bottom_extruder_nr].getProperty("support_bottom_enable", "value")) + "\n"
                    setting_data += ";Support Interface Height: " + str(extruder[support_interface_extruder_nr].getProperty("support_interface_height", "value")) + "mm\n"
                    setting_data += ";Support Roof Height: " + str(extruder[support_roof_extruder_nr].getProperty("support_roof_height", "value")) + "mm\n"
                    setting_data += ";Support Floor Height: " + str(extruder[support_bottom_extruder_nr].getProperty("support_bottom_height", "value")) + "mm\n"
                    setting_data += ";Support Interface Density: " + str(extruder[support_roof_extruder_nr].getProperty("support_interface_density", "value")) + "%\n"
                    setting_data += ";Support Interface Pattern: " + str(extruder[support_roof_extruder_nr].getProperty("support_interface_pattern", "value")) + "\n"
                    setting_data += ";Support Interface Min Area: " + str(extruder[support_roof_extruder_nr].getProperty("minimum_interface_area", "value")) + "mm²\n"
                    setting_data += ";Support Interface Horizontal Expansion: " + str(extruder[support_roof_extruder_nr].getProperty("support_interface_offset", "value")) + "mm\n"
                    setting_data += ";Support Interface Line Directions:" + str(extruder[support_interface_extruder_nr].getProperty("support_interface_angles", "value")) + "°\n"
                setting_data += ";Support Use Towers: " + str(mycura.getProperty("support_use_towers", "value")) + "\n"
                setting_data += ";Support Tower Diameter: " + str(mycura.getProperty("support_tower_diameter", "value")) + "mm\n"
                setting_data += ";Dropdown Support Mesh: " + str(mycura.getProperty("support_mesh_drop_down", "value")) + "\n"

        #Bed Adhesion Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("adhesion_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Bed Adhesion]\n"
            setting_data += ";Prime Blob Enable: " + str(mycura.getProperty("prime_blob_enable", "value")) + "\n"
            setting_data += ";Adhesion Type: " + str(mycura.getProperty("adhesion_type", "value")) + "\n"
            if str(mycura.getProperty("adhesion_type", "value")) != "none":
                setting_data += ";Adhesion Extruder Number: " + str(adhesion_extruder_nr) + "\n"
                try:
                    setting_data += ";Adhesion Skirt/Brim Extruder: " + str(skirt_brim_extruder_nr) + "\n"
                except:
                    pass
                setting_data += ";Adhesion Skirt Height: " + str(extruder[adhesion_extruder_nr].getProperty("skirt_height", "value")) + " layer(s)\n"
                setting_data += ";Adhesion Skirt Gap: " + str(extruder[adhesion_extruder_nr].getProperty("skirt_gap", "value")) + "mm\n"
                setting_data += ";Adhesion Brim Width: " + str(extruder[adhesion_extruder_nr].getProperty("brim_width", "value")) + "mm\n"
                setting_data += ";Adhesion Brim Gap: " + str(extruder[adhesion_extruder_nr].getProperty("brim_gap", "value")) + "mm\n"
                setting_data += ";Brim Replaces Support: " + str(mycura.getProperty("brim_replaces_support", "value")) + "\n"
                setting_data += ";Brim Outside Only: " + str(mycura.getProperty("brim_outside_only", "value")) + "\n"
                setting_data += ";Raft Margin: " + str(extruder[skirt_brim_extruder_nr].getProperty("raft_margin", "value")) + "mm\n"
                setting_data += ";Raft Air Gap: " + str(mycura.getProperty("raft_airgap", "value")) + "mm\n"
                setting_data += ";Raft Speed: " + str(mycura.getProperty("raft_speed", "value")) + "mm/sec\n"

        #Dual Extrusion Settings-------------------------------------------------------
        if (bool(self.getSettingValueByKey("dualext_set")) or all_or_some == "all_settings") and machine_extruder_count > 1:
            setting_data += ";\n;  [Dual Extrusion]\n"
            setting_data += ";Initial Extruder Nr: " + str(extruderMgr.getInitialExtruderNr()) + "\n"
            setting_data += ";Prime Tower Enable: " + str(mycura.getProperty("prime_tower_enable", "value")) + "\n"
            if bool(mycura.getProperty("prime_tower_enable", "value")):
                setting_data += ";  Prime Tower Size: " + str(mycura.getProperty("prime_tower_size", "value")) + "\n"
                setting_data += ";  Prime Tower Min Volume: " + str(mycura.getProperty("prime_tower_min_volume", "value")) + "mm³\n"
                setting_data += ";  Prime Tower X Pos: " + str(mycura.getProperty("prime_tower_position_x", "value")) + "\n"
                setting_data += ";  Prime Tower Y Pos: " + str(mycura.getProperty("prime_tower_position_y", "value")) + "\n"
                setting_data += ";  Prime Tower Wipe Enabled: " + str(mycura.getProperty("prime_tower_wipe_enabled", "value")) + "\n"
                setting_data += ";  Prime Tower Brim: " + str(mycura.getProperty("prime_tower_brim_enable", "value")) + "\n"
            setting_data += ";Ooze Shield Enable: " + str(mycura.getProperty("ooze_shield_enabled", "value")) + "\n"
            if bool(mycura.getProperty("ooze_shield_enabled", "value")):
                setting_data += ";  Ooze Shield Angle: " + str(mycura.getProperty("ooze_shield_angle", "value")) + "°\n"
                setting_data += ";  Ooze Shield Distance: " + str(mycura.getProperty("ooze_shield_dist", "value")) + "mm\n"
            setting_data += ";Extruder Switch Retraction Distance: " + str(mycura.getProperty("switch_extruder_retraction_amount", "value")) + "mm\n"
            setting_data += ";Extruder Switch Retraction Speed: " + str(mycura.getProperty("switch_extruder_retraction_speeds", "value")) + "mm/sec\n"
            setting_data += ";Extruder Switch Extra Prime: " + str(mycura.getProperty("switch_extruder_extra_prime_amount", "value")) + "mm³\n"

        #Mesh Fixes Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("meshfix_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Mesh Fixes]\n"
            setting_data += ";Union Overlapping Volumes: " + str(mycura.getProperty("meshfix_union_all", "value")) + "\n"
            setting_data += ";Remove All Holes: " + str(mycura.getProperty("meshfix_union_all_remove_holes", "value")) + "\n"
            setting_data += ";Extensive Stitching: " + str(mycura.getProperty("meshfix_extensive_stitching", "value")) + "\n"
            setting_data += ";Keep Disconnected Faces: " + str(mycura.getProperty("meshfix_keep_open_polygons", "value")) + "\n"
            setting_data += ";Merged Mesh Overlap: " + str(mycura.getProperty("multiple_mesh_overlap", "value")) + "\n"
            setting_data += ";Remove Mesh Intersection: " + str(mycura.getProperty("carve_multiple_volumes", "value")) + "\n"
            setting_data += ";Alternate Mesh Removal: " + str(mycura.getProperty("alternate_carve_order", "value")) + "\n"
            setting_data += ";Remove Empty First Layers: " + str(mycura.getProperty("remove_empty_first_layers", "value")) + "\n"
            setting_data += ";Maximum Resolution: " + str(mycura.getProperty("meshfix_maximum_resolution", "value")) + "\n"
            setting_data += ";Maximum Travel Resolution: " + str(mycura.getProperty("meshfix_maximum_travel_resolution", "value")) + "\n"
            setting_data += ";Maximum Deviation: " + str(mycura.getProperty("meshfix_maximum_deviation", "value")) + "\n"
            setting_data += ";Maximum Extrusion Area Deviation: " + str(mycura.getProperty("meshfix_maximum_extrusion_area_deviation", "value")) + "\n"

        #Special Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("special_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Special Modes]\n"
            setting_data += ";Print Sequence: " + str(mycura.getProperty("print_sequence", "value")) + "\n"
            setting_data += ";Mold Enabled: " + str(mycura.getProperty("mold_enabled", "value")) + "\n"
            if bool(mycura.getProperty("mold_enabled", "value")):
                setting_data += ";Mold Width: " + str(mycura.getProperty("mold_width", "value")) + "mm\n"
                setting_data += ";Mold Roof Height: " + str(mycura.getProperty("mold_roof_height", "value")) + "mm\n"
                setting_data += ";Mold Angle: " + str(mycura.getProperty("mold_angle", "value")) + "°\n"
            setting_data += ";Surface Mode: " + str(mycura.getProperty("magic_mesh_surface_mode", "value")) + "\n"
            setting_data += ";Spiralize: " + str(mycura.getProperty("magic_spiralize", "value")) + "\n"
            if bool(mycura.getProperty("magic_spiralize", "value")):
                setting_data += ";Smooth Spiralized Contours : " + str(mycura.getProperty("smooth_spiralized_contours", "value")) + "\n"
            setting_data += ";Relative Extrusion: " + str(mycura.getProperty("relative_extrusion", "value")) + "\n"

        #Experimental Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("experimental_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Experimental]\n"
            setting_data += ";Interlock Enable: " + str(mycura.getProperty("interlocking_enable", "value")) + "\n"
            if bool(mycura.getProperty("interlocking_enable", "value")):
                setting_data += ";  Interlock Beam Width: " + str(mycura.getProperty("interlocking_beam_width", "value")) + "mm\n"
                setting_data += ";  Interlock Orientation: " + str(mycura.getProperty("interlocking_orientation", "value")) + "\n"
                setting_data += ";  Interlock Beam Layer Count: " + str(mycura.getProperty("interlocking_beam_layer_count", "value")) + "\n"
                setting_data += ";  Interlock Depth: " + str(mycura.getProperty("interlocking_depth", "value")) + "mm\n"
                setting_data += ";  Interlock Avoid: " + str(mycura.getProperty("interlocking_boundary_avoidance", "value")) + "\n"
            setting_data += ";Draft Shield Enable: " + str(mycura.getProperty("draft_shield_enabled", "value")) + "\n"
            if bool(mycura.getProperty("draft_shield_enabled", "value")):
                setting_data += ";  Draft Shield Distance: " + str(mycura.getProperty("draft_shield_dist", "value")) + "mm\n"
                setting_data += ";  Draft Shield Height: " + str(mycura.getProperty("draft_shield_height", "value")) + "mm\n"
            setting_data += ";Make Overhang Printable: " + str(mycura.getProperty("conical_overhang_enabled", "value")) + "\n"
            setting_data += ";Coasting Enable: " + str(mycura.getProperty("coasting_enable", "value")) + "\n"
            setting_data += ";Fuzzy Skin Enable: " + str(mycura.getProperty("magic_fuzzy_skin_enabled", "value")) + "\n"
            setting_data += ";Flow Rate Compensation: " + str(mycura.getProperty("flow_rate_extrusion_offset_factor", "value")) + "%\n"
            setting_data += ";Adaptive Layers: " + str(mycura.getProperty("adaptive_layer_height_enabled", "value")) + "\n"
            if bool(mycura.getProperty("adaptive_layer_height_enabled", "value")):
                setting_data += ";  Adaptive Height Variation: " + str(mycura.getProperty("adaptive_layer_height_variation", "value")) + "\n"
                setting_data += ";  Adaptive Height Step: " + str(mycura.getProperty("adaptive_layer_height_variation_step", "value")) + "\n"
                setting_data += ";  Adaptive Height Threshold: " + str(mycura.getProperty("adaptive_layer_height_threshold", "value")) + "\n"
            setting_data += ";Bridge Settings Enabled: " + str(mycura.getProperty("bridge_settings_enabled", "value")) + "\n"
            if bool(mycura.getProperty("bridge_settings_enabled", "value")):
                setting_data += ";  Bridge Wall Min Length: " + str(mycura.getProperty("bridge_wall_min_length", "value")) + "\n"
                setting_data += ";  Bridge Skin Supt Threshold: " + str(mycura.getProperty("bridge_skin_support_threshold", "value")) + "\n"
                setting_data += ";  Bridge Sparse Infill Max Density: " + str(mycura.getProperty("bridge_sparse_infill_max_density", "value")) + "%\n"
                setting_data += ";  Bridge Wall Coast: " + str(mycura.getProperty("bridge_wall_coast", "value")) + "\n"
                setting_data += ";  Bridge Wall Speed: " + str(mycura.getProperty("bridge_wall_speed", "value")) + "mm/sec\n"
                setting_data += ";  Bridge Wall Matl Flow: " + str(mycura.getProperty("bridge_wall_material_flow", "value")) + "%\n"
                setting_data += ";  Bridge Skin Speed: " + str(mycura.getProperty("bridge_skin_speed", "value")) + "mm/sec\n"
                setting_data += ";  Bridge Skin Matl Flow: " + str(mycura.getProperty("bridge_skin_material_flow", "value")) + "%\n"
                setting_data += ";  Bridge Skin Density: " + str(mycura.getProperty("bridge_skin_density", "value")) + "%\n"
                setting_data += ";  Bridge Fan Speed: " + str(mycura.getProperty("bridge_fan_speed", "value")) + "%\n"
                setting_data += ";  Bridge Enable More Layers: " + str(mycura.getProperty("bridge_enable_more_layers", "value")) + "\n"
                if bool(mycura.getProperty("bridge_enable_more_layers", "value")):
                    setting_data += ";    Bridge Skin Speed 2: " + str(mycura.getProperty("bridge_skin_speed_2", "value")) + "mm/sec\n"
                    setting_data += ";    Bridge Skin Matl Flow 2: " + str(mycura.getProperty("bridge_skin_material_flow_2", "value")) + "%\n"
                    setting_data += ";    Bridge Skin Density 2: " + str(mycura.getProperty("bridge_skin_density_2", "value")) + "%\n"
                    setting_data += ";    Bridge Fan Speed 2: " + str(mycura.getProperty("bridge_fan_speed_2", "value")) + "%\n"
                    setting_data += ";      Bridge Skin Speed 3: " + str(mycura.getProperty("bridge_skin_speed_3", "value")) + "mm/sec\n"
                    setting_data += ";      Bridge Skin Matl Flow 3: " + str(mycura.getProperty("bridge_skin_material_flow_3", "value")) + "%\n"
                    setting_data += ";      Bridge Skin Density 3: " + str(mycura.getProperty("bridge_skin_density_3", "value")) + "%\n"
                    setting_data += ";      Bridge Fan Speed 3: " + str(mycura.getProperty("bridge_fan_speed_3", "value")) + "%\n"
            setting_data += ";Alternate Wall Directions: " + str(mycura.getProperty("material_alternate_walls", "value")) + "\n"

        #PostProcessor Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("postprocess_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Post-Processors]\n"
            scripts_list = mycura.getMetaDataEntry("post_processing_scripts")
            for script_str in scripts_list.split("\n"):
                script_str = script_str.replace(r"\\\n", "\n;  ").replace("\n;  \n;  ", "\n")
                setting_data += ";" + str(script_str)
        #End of Settings-------------------------------------------------------------------------------
        setting_data += ";\n;  <<< End of Cura Settings >>>\n;\n"
        data[len(data)-1] += setting_data

        return data