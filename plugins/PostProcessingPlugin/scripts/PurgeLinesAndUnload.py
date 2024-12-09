# August 2024 - GregValiant (Greg Foresi)
#
#  NOTE: You may have purge lines in your startup, or you may use this script, you should not do both.  The script will attempt to comment out existing StartUp purge lines.
# 'Add Purge Lines to StartUp' Allows the user to determine where the purge lines are on the build plate, or to not use purge lines if a print extends to the limits of the build surface.  Any Purge lines currently in the StartUp should be removed before using this script.
# The setting 'Purge Line Length' is only avaialble for rectangular beds because I was too lazy to calculate the 45° arcs.
# 'Move to Start' takes an orthogonal path around the periphery before moving in to the print start location.  It eliminates strings across the print area.
# 'Adjust Starting E' is a correction in the E location before the skirt/brim starts.  The user can make an adjustment so that the skirt / brim / raft starts where it should.
# 'Unload' adds code to the Ending Gcode that will unload the filament from the machine.  The unlaod distance is broken into chunks to avoid overly long E distances.
#  Added extra moves to account for Cura adding a "Travel to Prime Tower" move that can cross the middle of the build surface.

from ..Script import Script
from UM.Application import Application
from UM.Message import Message
import re
import os
from UM.Logger import Logger

class PurgeLinesAndUnload(Script):

    def initialize(self) -> None:
        super().initialize()
        # Get the StartUp Gcode from Cura and attempt to catch if it contains purge lines.  Message the user if an extrusion is in the startup.
        curaApp = Application.getInstance().getGlobalContainerStack()
        startup_gcode = curaApp.getProperty("machine_start_gcode", "value")
        start_lines = startup_gcode.splitlines()
        for line in start_lines:
            if line.startswith("G1") and " E" in line and (" X" in line or " Y" in line):
                Message(title = "[Purge Lines and Unload]", text = "It appears that there are 'purge lines' in the StartUp Gcode.  Using the 'Add Purge Lines' function of this script will comment them out.").show()
                break
        self._instance.setProperty("is_rectangular", "value", True if curaApp.getProperty("machine_shape", "value") == "rectangular" else False)
        self._extruder = curaApp.extruderList
        #This is set in 'Add Purge Lines' and is used by 'Move to Start' to indicate which corner the nozzle is in after the purge lines
        self._purge_end_loc = None
        # Set the default E adjustment
        self._instance.setProperty("adjust_e_loc_to", "value", -abs(round(float(self._extruder[0].getProperty("retraction_amount", "value")), 1)))

    def getSettingDataString(self):
        return """{
            "name": "Purge Lines and Unload Filament",
            "key": "PurgeLinesAndUnload",
            "metadata": {},
            "version": 2,
            "settings":
            {
            "add_purge_lines":
                {
                    "label": "Add Purge Lines to StartUp",
                    "description": "The purge lines can be left, right, front or back.  If there are purge lines present in the StartUp Gcode remove them or comment them out before using this script.  You don't want to double dip.",
                    "type": "bool",
                    "default_value": false,
                    "value": false,
                    "enabled": true
                },
                "purge_line_location":
                {
                    "label": "    Purge Line Location",
                    "description": "What edge of the build plate should have the purge lines.  If the printer is 'Elliptical' then it is assumed to be an 'Origin At Center' printer and the purge lines are 90° arcs.",
                    "type": "enum",
                    "options": {
                        "purge_left": "On left edge (Xmin)",
                        "purge_right": "On right edge (Xmax)",
                        "purge_bottom": "On front edge (Ymin)",
                        "purge_top": "On back edge (Ymax)"},
                    "default_value": "purge_left",
                    "enabled": "add_purge_lines"
                },
                "purge_line_length":
                {
                    "label": "    Purge Line Length",
                    "description": "Select 'Full' for the entire Height or Width of the build plate.  Select 'Half' for shorter purge lines.  NOTE: This has no effect on elliptic beds.",
                    "type": "enum",
                    "options": {
                        "purge_full": "Full",
                        "purge_half": "Half"},
                    "default_value": "purge_full",
                    "enabled": "add_purge_lines and is_rectangular"
                },
                "move_to_start":
                {
                    "label": "Circle around to layer start",
                    "description": "Depending on where the 'Layer Start X' and 'Layer Start Y' are for the print, the opening travel move can pass across the print area and leave a string there.  This option will generate an orthogonal path that moves the nozzle around the edges of the build plate and then comes in to the Start Point.  The nozzle will drop and touch the build plate at each stop in order to nail down the string so it doesn't follow in a straight line.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": true
                },
                "adjust_starting_e":
                {
                    "label": "Adjust Starting E location",
                    "description": "If there is a retraction after the purge lines in the Startup Gcode (like the 'Add Purge Lines' script here does) then often the skirt does not start where the nozzle starts.  It is because Cura always adds a retraction prior to the print starting which results in a double retraction.  Enabling this will allow you to adjust the starting E location and tune it so the skirt/brim/model starts right where it should.  To fix a blob enter a positive number.  To fix a 'dry start' enter a negative number.",
                    "type": "bool",
                    "default_value": false,
                    "value": false,
                    "enabled": true
                },
                "adjust_e_loc_to":
                {
                    "label": "    Starting E location",
                    "description": "This is usually a negative amount and often equal to the '-Retraction Distance'.  This 'G92 E' adjustment changes where the printer 'thinks' the end of the filament is in relation to the nozzle.  It replaces the retraction that Cura adds prior to the start of 'LAYER:0'.  If retraction is not enabled then this setting has no effect.",
                    "type": "float",
                    "unit": "mm  ",
                    "default_value": -6.5,
                    "enabled": "adjust_starting_e"
                },
                "enable_unload":
                {
                    "label": "Unload filament at print end",
                    "description": "Adds an unload script to the Ending Gcode section.  It goes in just ahead of the M104 S0.  This scripts always unloads the active extruder.  If the unload distance is greater than 150mm it will be broken into chunks to avoid tripping the excessive extrusion warning in some firmware.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": true
                },
                "unload_distance":
                {
                    "label": "    Unload Distance",
                    "description": "The amount of filament to unload.  Bowden printers usually require a significant amount and direct drives not as much.",
                    "type": "int",
                    "default_value": 440,
                    "unit": "mm  ",
                    "enabled": "enable_unload"
                },
                "is_rectangular":
                {
                    "label": "Bed is rectangular",
                    "description": "Hidden setting that disables 'purge line length' for elliptical beds.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": false
                }
            }
        }"""

    def execute(self, data):
        # Run the selected procedures
        if self.getSettingValueByKey("add_purge_lines"):
            self._add_purge_lines(data)
        if self.getSettingValueByKey("move_to_start"):
            self._move_to_start(data)
        if self.getSettingValueByKey("adjust_starting_e"):
            self._adjust_starting_e(data)
        if self.getSettingValueByKey("enable_unload"):
            self._unload_filament(data)
        # Format the startup and ending gcodes
        data[1] = self._format_string(data[1])
        data[len(data) - 1] = self._format_string(data[len(data) - 1])
        return data

    # Add Purge Lines to the user defined position on the build plate
    def _add_purge_lines(self, data: str):
        curaApp = Application.getInstance().getGlobalContainerStack()
        retract_dist = self._extruder[0].getProperty("retraction_amount", "value")
        retract_enable = self._extruder[0].getProperty("retraction_enable", "value")
        retract_speed = self._extruder[0].getProperty("retraction_retract_speed", "value") * 60
        bed_shape = str(curaApp.getProperty("machine_shape", "value"))
        origin_at_center = bool(curaApp.getProperty("machine_center_is_zero", "value"))
        machine_width = curaApp.getProperty("machine_width", "value")
        machine_depth = curaApp.getProperty("machine_depth", "value")
        material_diameter = self._extruder[0].getProperty("material_diameter", "value")
        mm3_per_mm = (material_diameter / 2)**2 * 3.14159
        init_line_width = self._extruder[0].getProperty("skirt_brim_line_width", "value")
        where_at = self.getSettingValueByKey("purge_line_location")
        travel_speed = self._extruder[0].getProperty("speed_travel", "value") * 60
        print_speed = round(self._extruder[0].getProperty("speed_print", "value") * 60 * .75)
        purge_extrusion_full = True if self.getSettingValueByKey("purge_line_length") == "purge_full" else False
        purge_str = ";TYPE:CUSTOM----------[Purge Lines]\nG0 F600 Z2 ; Move up\nG92 E0 ; Reset extruder\n"

        # Normal cartesian printer with origin at the left front corner
        if bed_shape == "rectangular" and not origin_at_center:
            if where_at == "purge_left":
                purge_len = int(machine_depth) - 20 if purge_extrusion_full else int(machine_depth / 2)
                y_stop = int(machine_depth - 10) if purge_extrusion_full else int(machine_depth / 2)
                purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
                purge_str = purge_str.replace("Lines", "Lines at MinX")
                purge_str += f"G0 F{travel_speed} X0 Y10 ; Move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G1 F{print_speed} X0 Y{y_stop} E{purge_volume} ; First line\n"
                purge_str += f"G0 X3 Y{y_stop} ; Move over\n"
                purge_str += f"G1 F{print_speed} X3 Y10 E{round(purge_volume * 2,5)} ; Second line\n"
                purge_str += f"G1 F{int(retract_speed)} E{round(purge_volume * 2 - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                purge_str += f"G0 F{print_speed} X3 Y20 Z0.3 ; Slide over and down\n"
                purge_str += "G0 X3 Y35 ; Wipe\n"
                self._purge_end_loc = "LF"
            elif where_at == "purge_right":
                purge_len = int(machine_depth) - 20 if purge_extrusion_full else int(machine_depth / 2)
                y_stop = 10 if purge_extrusion_full else int(machine_depth / 2)
                purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
                purge_str = purge_str.replace("Lines", "Lines at MaxX")
                purge_str += f"G0 F{travel_speed} X{machine_width} ; Move\nG0 Y{machine_depth - 10} ; Move\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G1 F{print_speed} X{machine_width} Y{y_stop} E{purge_volume} ; First line\n"
                purge_str += f"G0 X{machine_width - 3} Y{y_stop} ; Move over\n"
                purge_str += f"G1 F{print_speed} X{machine_width - 3} Y{machine_depth - 10} E{purge_volume * 2} ; Second line\n"
                purge_str += f"G1 F{int(retract_speed)} E{round(purge_volume * 2 - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                purge_str += f"G0 F{print_speed} X{machine_width - 3} Y{machine_depth - 20} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 X{machine_width - 3} Y{machine_depth - 35} ; Wipe\n"
                self._purge_end_loc = "RR"
            elif where_at == "purge_bottom":
                purge_len = int(machine_width) - 20 if purge_extrusion_full else int(machine_width / 2)
                x_stop = int(machine_width - 10) if purge_extrusion_full else int(machine_width / 2)
                purge_str = purge_str.replace("Lines", "Lines at MinY")
                purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
                purge_str += f"G0 F{travel_speed} X10 Y0 ; Move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G1 F{print_speed} X{x_stop} Y0 E{purge_volume} ; First line\n"
                purge_str += f"G0 X{x_stop} Y3 ; Move over\n"
                purge_str += f"G1 F{print_speed} X10 Y3 E{purge_volume * 2} ; Second line\n"
                purge_str += f"G1 F{int(retract_speed)} E{round(purge_volume * 2 - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                purge_str += f"G0 F{print_speed} X20 Y3 Z0.3 ; Slide over and down\n"
                purge_str += "G0 X35 Y3 ; Wipe\n"
                self._purge_end_loc = "LF"
            elif where_at == "purge_top":
                purge_len = int(machine_width - 20) if purge_extrusion_full else int(machine_width / 2)
                x_stop = 10 if purge_extrusion_full else int(machine_width / 2)
                purge_str = purge_str.replace("Lines", "Lines at MaxY")
                purge_len = int(machine_width) - 20
                purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
                purge_str += f"G0 F{travel_speed} Y{machine_depth} ; Ortho Move to back\n"
                purge_str += f"G0 X{machine_width - 10} ; Ortho move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G1 F{print_speed} X{x_stop} Y{machine_depth} E{purge_volume} ; First line\n"
                purge_str += f"G0 X{x_stop} Y{machine_depth - 3} ; Move over\n"
                purge_str += f"G1 F{print_speed} X{machine_width - 10} Y{machine_depth - 3} E{purge_volume * 2} ; Second line\n"
                purge_str += f"G1 F{int(retract_speed)} E{round(purge_volume * 2 - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait 1 second\n"
                purge_str += f"G0 F{print_speed} X{machine_width - 20} Y{machine_depth - 3} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 X{machine_width - 35} Y{machine_depth - 3} ; Wipe\n"
                self._purge_end_loc = "RR"

        # Some cartesian printers (BIBO, Weedo, etc.) are Origin at Center
        elif bed_shape == "rectangular" and origin_at_center:
            if where_at == "purge_left":
                purge_len = int(machine_depth - 20) if purge_extrusion_full else int(machine_depth / 2)
                y_stop = int((machine_depth / 2) - 10) if purge_extrusion_full else 0
                purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
                purge_str += f"G0 F{travel_speed} X-{machine_width / 2} Y-{(machine_depth / 2) - 10} ; Move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G1 F{print_speed} X-{machine_width / 2} Y{y_stop} E{purge_volume} ; First line\n"
                purge_str += f"G0 X-{(machine_width / 2) - 3} Y{y_stop} ; Move over\n"
                purge_str += f"G1 F{print_speed} X-{(machine_width / 2) - 3} Y-{(machine_depth / 2) - 10} E{round(purge_volume * 2, 5)} ; Second line\n"
                purge_str += f"G1 F{int(retract_speed)} E{round(purge_volume * 2 - retract_dist, 5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                purge_str += f"G0 F{print_speed} X-{(machine_width / 2) - 3} Y-{(machine_depth / 2) - 20} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 X-{(machine_width / 2) - 3} Y-{(machine_depth / 2) - 35} ; Wipe\n"
                self._purge_end_loc = "LF"
            elif where_at == "purge_right":
                purge_len = int(machine_depth - 20) if purge_extrusion_full else int(machine_depth / 2)
                y_stop = int((machine_depth / 2) - 10) if purge_extrusion_full else 0
                purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
                purge_str += f"G0 F{travel_speed} X{machine_width / 2} Z2 ; Move\nG0 Y{(machine_depth / 2) - 10} Z2 ; Move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G1 F{print_speed} X{machine_width / 2} Y-{y_stop} E{purge_volume} ; First line\n"
                purge_str += f"G0 X{(machine_width / 2) - 3} Y-{y_stop} ; Move over\n"
                purge_str += f"G1 F{print_speed} X{(machine_width / 2) - 3} Y{(machine_depth / 2) - 10} E{purge_volume * 2} ; Second line\n"
                purge_str += f"G1 F{int(retract_speed)} E{round(purge_volume * 2 - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                purge_str += f"G0 F{print_speed} X{(machine_width / 2) - 3} Y{(machine_depth / 2) - 20} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 F{travel_speed} X{(machine_width / 2) - 3} Y{(machine_depth / 2) - 35} ; Wipe\n"
                self._purge_end_loc = "RR"
            elif where_at == "purge_bottom":
                purge_len = int(machine_width - 20) if purge_extrusion_full else int(machine_width / 2)
                x_stop = int((machine_width / 2) - 10) if purge_extrusion_full else 0
                purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
                purge_str += f"G0 F{travel_speed} X-{machine_width / 2 - 10} Z2 ; Move\nG0 Y-{machine_depth / 2} Z2 ; Move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G1 F{print_speed} X{x_stop} Y-{machine_depth / 2} E{purge_volume} ; First line\n"
                purge_str += f"G0 X{x_stop} Y-{machine_depth / 2 - 3} ; Move over\n"
                purge_str += f"G1 F{print_speed} X-{machine_width / 2 - 10} Y-{machine_depth / 2 - 3} E{purge_volume * 2} ; Second line\n"
                purge_str += f"G1 F{int(retract_speed)} E{round(purge_volume * 2 - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                purge_str += f"G0 F{print_speed} X-{(machine_width / 2) - 20} Y-{(machine_depth / 2) - 3} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 F{print_speed} X-{(machine_width / 2) - 35} Y-{(machine_depth / 2) - 3} ; Wipe\n"
                self._purge_end_loc = "LF"
            elif where_at == "purge_top":
                purge_len = int(machine_width - 20) if purge_extrusion_full else int(machine_width / 2)
                x_stop = int((machine_width / 2) - 10) if purge_extrusion_full else 0
                purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
                purge_str += f"G0 F{travel_speed} Y{machine_depth / 2} Z2; Ortho Move to back\n"
                purge_str += f"G0 X{machine_width / 2 - 10} Z2 ; Ortho Move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G1 F{print_speed} X-{x_stop} Y{machine_depth / 2} E{purge_volume} ; First line\n"
                purge_str += f"G0 X-{x_stop} Y{machine_depth / 2 - 3} ; Move over\n"
                purge_str += f"G1 F{print_speed} X{machine_width / 2 - 10} Y{machine_depth / 2 - 3} E{purge_volume * 2} ; Second line\n"
                purge_str += f"G1 F{int(retract_speed)} E{round(purge_volume * 2 - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                purge_str += f"G0 F{print_speed} X{machine_width / 2 - 20} Y{machine_depth / 2 - 3} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 F{print_speed} X{machine_width / 2 - 35} Y{machine_depth / 2 - 3} ; Wipe\n"
                self._purge_end_loc = "RR"

        # Elliptic printers with Origin at Center
        elif bed_shape == "elliptic":
            if where_at in ["purge_left","purge_right"]:
                radius_1 = round((machine_width / 2) - 1,2)
            elif where_at in ["purge_bottom", "purge_top"]:
                radius_1 = round((machine_depth / 2) - 1,2)
            purge_len = int(radius_1) * 3.14159 / 4
            purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
            if where_at == "purge_left":
                purge_str += f"G0 F{travel_speed} X-{round(radius_1 * .707, 2)} Y-{round(radius_1 * .707,2)} ; Travel\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G2 F{print_speed} X-{round(radius_1 * .707,2)} Y{round(radius_1 * .707,2)} I{round(radius_1 * .707,2)} J{round(radius_1 * .707,2)} E{purge_volume} ; First Arc\n"
                purge_str += f"G0 X-{round((radius_1 - 3) * .707,2)} Y{round((radius_1 - 3) * .707,2)} ; Move Over\n"
                purge_str += f"G3 F{print_speed} X-{round((radius_1 - 3) * .707,2)} Y-{round((radius_1 - 3) * .707,2)} I{round((radius_1 - 3) * .707,2)} J-{round((radius_1 - 3) * .707,2)} E{purge_volume * 2} ; Second Arc\n"
                purge_str += f"G1 X-{round((radius_1 - 3) * .707 - 25,2)} E{round(purge_volume * 2 + 1,5)} ; Move Over\n"
                purge_str += f"G1 F{int(retract_speed)} E{round((purge_volume * 2 + 1) - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z5 ; Move Up\nG4 S1 ; Wait 1 Second\n"
                purge_str += f"G0 F{print_speed} X-{round((radius_1 - 3) * .707 - 15,2)} Z0.3 ; Slide Over\n"
                purge_str += f"G0 F{print_speed} X-{round((radius_1 - 3) * .707,2)} ; Wipe\n"
                self.purge_end_loc = "LF"
            elif where_at == "purge_right":
                purge_str += f"G0 F{travel_speed} X{round(radius_1 * .707, 2)} Y-{round(radius_1 * .707,2)} ; Travel\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G3 F{print_speed} X{round(radius_1 * .707,2)} Y{round(radius_1 * .707,2)} I-{round(radius_1 * .707,2)} J{round(radius_1 * .707,2)} E{purge_volume} ; First Arc\n"
                purge_str += f"G0 X{round((radius_1 - 3) * .707,2)} Y{round((radius_1 - 3) * .707,2)} ; Move Over\n"
                purge_str += f"G2 F{print_speed} X{round((radius_1 - 3) * .707,2)} Y-{round((radius_1 - 3) * .707,2)} I-{round((radius_1 - 3) * .707,2)} J-{round((radius_1 - 3) * .707,2)} E{purge_volume * 2} ; Second Arc\n"
                purge_str += f"G1 X{round((radius_1 - 3) * .707 - 25,2)} E{round(purge_volume * 2 + 1,5)} ; Move Over\n"
                purge_str += f"G1 F{int(retract_speed)} E{round((purge_volume * 2 + 1) - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z5 ; Move Up\nG4 S1 ; Wait 1 Second\n"
                purge_str += f"G0 F{print_speed} X{round((radius_1 - 3) * .707 - 15,2)} Z0.3 ; Slide Over\n"
                purge_str += f"G0 F{print_speed} X{round((radius_1 - 3) * .707,2)}\n"
                self.purge_end_loc = "RR"
            elif where_at == "purge_bottom":
                purge_str += f"G0 F{travel_speed} X-{round(radius_1 * .707, 2)} Y-{round(radius_1 * .707,2)} ; Travel\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G3 F{print_speed} X{round(radius_1 * .707,2)} Y-{round(radius_1 * .707,2)} I{round(radius_1 * .707,2)} J{round(radius_1 * .707,2)} E{purge_volume} ; First Arc\n"
                purge_str += f"G0 X{round((radius_1 - 3) * .707,2)} Y-{round((radius_1 - 3) * .707,2)} ; Move Over\n"
                purge_str += f"G2 F{print_speed} X-{round((radius_1 - 3) * .707,2)} Y-{round((radius_1 - 3) * .707,2)} I-{round((radius_1 - 3) * .707,2)} J{round((radius_1 - 3) * .707,2)} E{purge_volume * 2} ; Second Arc\n"
                purge_str += f"G1 Y-{round((radius_1 - 3) * .707 - 25,2)} E{round(purge_volume * 2 + 1, 5)} ; Move Over\n"
                purge_str += f"G1 F{int(retract_speed)} E{round((purge_volume * 2 + 1) - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z5 ; Move Up\nG4 S1 ; Wait 1 Second\n"
                purge_str += f"G0 F{print_speed} Y-{round((radius_1 - 3) * .707 - 15,2)} Z0.3 ; Slide Over\n"
                purge_str += f"G0 F{print_speed} Y-{round((radius_1 - 3) * .707,2)}\n"
                self.purge_end_loc = "LF"
            elif where_at == "purge_top":
                purge_str += f"G0 F{travel_speed} X{round(radius_1 * .707, 2)} Y{round(radius_1 * .707,2)} ; Travel\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G3 F{print_speed} X-{round(radius_1 * .707,2)} Y{round(radius_1 * .707,2)} I-{round(radius_1 * .707,2)} J-{round(radius_1 * .707,2)} E{purge_volume} ; First Arc\n"
                purge_str += f"G0 X-{round((radius_1 - 3) * .707,2)} Y{round((radius_1 - 3) * .707,2)} ; Move Over\n"
                purge_str += f"G2 F{print_speed} X{round((radius_1 - 3) * .707,2)} Y{round((radius_1 - 3) * .707,2)} I{round((radius_1 - 3) * .707,2)} J-{round((radius_1 - 3) * .707,2)} E{purge_volume * 2} ; Second Arc\n"
                purge_str += f"G1 Y{round((radius_1 - 3) * .707 - 25,2)} E{round(purge_volume * 2 + 1,5)} ; Move Over\n"
                purge_str += f"G1 F{int(retract_speed)} E{round((purge_volume * 2 + 1) - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z5\nG4 S1\n"
                purge_str += f"G0 F{print_speed} Y{round((radius_1 - 3) * .707 - 15,2)} Z0.3 ; Slide Over\n"
                purge_str += f"G0 F{print_speed} Y{round((radius_1 - 3) * .707,2)}\n"
                self.purge_end_loc = "RR"

        # Common ending for purge_str
        purge_str += "G0 F600 Z2 ; Move Z\n;---------------------[End of Purge]"

        # If there is a move to the prime tower location after purging then it needs to be accounted for
        if curaApp.getProperty("machine_extruder_count", "value") > 1:
            data[1] = self._move_to_prime_tower(data[1], bed_shape, origin_at_center, machine_width, machine_depth, travel_speed)

        # Comment out any existing purge lines in Data[1]
        startup = data[1].split("\n")
        for index, line in enumerate(startup):
            if line.startswith("G1") and " E" in line and (" X" in line or " Y" in line):
                next_line = index
                try:
                    while not startup[next_line].startswith ("G92 E0"):
                        startup[next_line] = ";" + startup[next_line]
                        next_line += 1
                except:
                    break
        data[1] = "\n".join(startup)

        # Find the insertion location in data[1]
        purge_str = self._format_string(purge_str)
        startup_section = data[1].split("\n")
        for num in range(len(startup_section) - 1, 0, -1):
            # In Absolute Extrusion mode - insert above the last G92 E0 line
            if "G92 E0" in startup_section[num]:
                insert_index = num
                break
            # In Relative Extrusion mode - insert above the M83 line
            elif "M83" in startup_section[num]:
                insert_index = num
                break
        startup_section.insert(insert_index, purge_str)
        data[1] = "\n".join(startup_section)
        return

    # Travel moves around the bed periphery to keep strings from crossing the footprint of the model.
    def _move_to_start(self, data: str) -> str:
        curaApp = Application.getInstance().getGlobalContainerStack()
        bed_shape = str(curaApp.getProperty("machine_shape", "value"))
        origin_at_center = bool(curaApp.getProperty("machine_center_is_zero", "value"))
        machine_width = curaApp.getProperty("machine_width", "value")
        machine_depth = curaApp.getProperty("machine_depth", "value")
        if curaApp.getProperty("machine_extruder_count", "value") > 1:
            self._purge_end_loc = self._get_real_start_point(data[1], bed_shape, origin_at_center, machine_width, machine_depth)
        layer = data[2].split("\n")
        start_x = None
        start_y = None
        for line in layer:
            if line.startswith("G0") and " X" in line and " Y" in line:
                start_x = self.getValue(line, "X")
                start_y = self.getValue(line, "Y")
                break
        if start_x == None: start_x = 0
        if start_y == None: start_y = 0
        if self._purge_end_loc == None:
            purge_end_loc = "LF"
        else:
            purge_end_loc = self._purge_end_loc
        travel_speed = round(self._extruder[0].getProperty("speed_travel", "value") * 60)
        move_str = f";MESH:NONMESH---------[Travel to Layer Start]\nG0 F600 Z2 ; Move up\n"
        midpoint_x = machine_width / 2
        midpoint_y = machine_depth / 2
        if not origin_at_center:
            if float(start_x) <= float(midpoint_x):
                goto_str = "Lt"
            else:
                goto_str = "Rt"
            if float(start_y) <= float(midpoint_y):
                goto_str += "Frt"
            else:
                goto_str += "Bk"
        else:
            if float(start_x) <= 0:
                goto_str = "Lt"
            else:
                goto_str = "Rt"
            if float(start_y) <= 0:
                goto_str += "Frt"
            else:
                goto_str += "Bk"

        # If purge lines was not selected, and the printer is multi-extruder, there may be a move to the purge tower that needs to be considered
        if not self.getSettingValueByKey("add_purge_lines"):
            if curaApp.getProperty("machine_extruder_count", "value") > 1:
                data[1] = self._move_to_prime_tower(data[1], bed_shape, origin_at_center, machine_width, machine_depth, travel_speed)

        # Depending on which quadrant the XY layer start is, move around the periphery before coming in to the start position
        if bed_shape == "rectangular" and not origin_at_center:
            if purge_end_loc == "LF":
                if goto_str == "LtFrt":
                    move_str += f"G0 F{travel_speed} X5 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y5 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                elif goto_str == "RtFrt":
                    move_str += f"G0 F{travel_speed} X5 Z2; Ortho Move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y5 Z2 ; Ortho Move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{travel_speed} X{start_x} ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                elif goto_str == "LtBk":
                    move_str += f"G0 F{travel_speed} X5 ; Ortho Move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y5 Z2 ; Move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y{start_y} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                elif goto_str == "RtBk":
                    move_str += f"G0 F{travel_speed} X5 ; Move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y5 Z2 ; Move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{travel_speed} X{machine_width - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y{start_y} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
            elif purge_end_loc == "RR":
                if goto_str == "LtFrt":
                    move_str += f"G0 F{travel_speed} X5 Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y5 Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                elif goto_str == "RtFrt":
                    move_str += f"G0 F{travel_speed} X{start_x} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y5 Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                elif goto_str == "LtBk":
                    move_str += f"G0 F{travel_speed} X5 Z2 ; Move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                elif goto_str == "RtBk":
                    move_str += f"G0 F{travel_speed} X{machine_width - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y{start_y} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"

        elif bed_shape == "rectangular" and origin_at_center:
            if purge_end_loc == "LF":
                if goto_str == "LtFrt":
                    move_str += f"G0 F{travel_speed} X-{machine_width / 2 - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y-{machine_depth / 2 - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                elif goto_str == "RtFrt":
                    move_str += f"G0 F{travel_speed} X{machine_width / 2 - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y-{machine_depth / 2 - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                elif goto_str == "LtBk":
                    move_str += f"G0 F{travel_speed} X-{machine_width / 2 - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y{machine_depth / 2 - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                elif goto_str == "RtBk":
                    move_str += f"G0 F{travel_speed} X{machine_width / 2 - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y{machine_depth / 2 - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
            elif purge_end_loc == "RR":
                if goto_str == "LtFrt":
                    move_str += f"G0 F{travel_speed} X{machine_width / 2 - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y-{machine_depth / 2 - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                elif goto_str == "RtFrt":
                    move_str += f"G0 F{travel_speed} X{machine_width / 2 - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y-{machine_depth / 2 - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                elif goto_str == "LtBk":
                    move_str += f"G0 F{travel_speed} X-{machine_width / 2 - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y{machine_depth / 2 - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                elif goto_str == "RtBk":
                    move_str += f"G0 F{travel_speed} X{machine_width / 2 - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y{machine_depth / 2 - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"

        elif bed_shape == "elliptic" and origin_at_center:
            radius = machine_width / 2
            offset_sin = round(2**.5 / 2 * radius, 2)
            if purge_end_loc == "LR":
                if goto_str == "LtFrt":
                    move_str += f"G0 F{travel_speed} X-{offset_sin} Z2 ; Move\nG0 Y-{offset_sin} Z2 ; Move to start\n"
                elif goto_str == "LtBk":
                    move_str += f"G2 X0 Y{offset_sin} I{offset_sin} J{offset_sin} ; Move around to start\n"
                elif goto_str == "RtFrt":
                    move_str += f"G0 F{travel_speed} X{offset_sin} Z2 ; Ortho move\nG0 Y-{offset_sin} Z2 ; Ortho move\n"
                elif goto_str == "RtBk":
                    move_str += f"G0 F{travel_speed} X{offset_sin} Z2 ; Ortho move\nG0 Y{offset_sin} Z2 ; Ortho move\n"
            elif purge_end_loc == "RR":
                if goto_str == "LtFrt":
                    move_str += f"G0 F{travel_speed} X-{offset_sin} Z2 ; Move\nG0 Y-{offset_sin} Z2 ; Move to start\n"
                elif goto_str == "LtBk":
                    move_str += f"G0 F{travel_speed} X-{offset_sin} Z2 ; Ortho move\nG0 Y{offset_sin} Z2 ; Ortho move\n"
                elif goto_str == "RtFrt":
                    move_str += f"G0 F{travel_speed} X{offset_sin} Z2 ; Ortho move\nG0 Y-{offset_sin} Z2 ; Ortho move\n"
                elif goto_str == "RtBk":
                    move_str += f"G0 F{travel_speed} X{offset_sin} Z2 ; Ortho move\nG0 Y{offset_sin} Z2 ; Ortho move\n"
            elif purge_end_loc == "LF":
                if goto_str == "LtFrt":
                    move_str += f"G0 F{travel_speed} X-{offset_sin} Z2 ; Move\nG0 Y-{offset_sin} Z2 ; Move to start\n"
                elif goto_str == "LtBk":
                    move_str += f"G0 F{travel_speed} X-{offset_sin} Z2 ; Ortho move\nG0 Y{offset_sin} Z2 ; Ortho move\n"
                elif goto_str == "RtFrt":
                    move_str += f"G0 F{travel_speed} X{offset_sin} Z2 ; Ortho move\nG0 Y-{offset_sin} Z2 ; Ortho move\n"
                elif goto_str == "RtBk":
                    move_str += f"G0 F{travel_speed} X{offset_sin} Z2 ; Ortho move\nG0 Y{offset_sin} Z2 ; Ortho move\n"
        move_str += ";---------------------[End of layer start travels]"
        # Add the move_str to the end of the StartUp section and move 'LAYER_COUNT' to the end.
        startup = data[1].split("\n")
        for index, line in enumerate(startup):
            if "LAYER_COUNT" in line:
                lay_count = startup.pop(index) + "\n"
                break
        move_str = self._format_string(move_str)
        if move_str.startswith("\n"):
            move_str = move_str[1:]
        startup.append(move_str)
        startup.append(lay_count)
        data[1] = "\n".join(startup)
        # Remove any double spaced lines
        data[1] = data[1].replace("\n\n", "\n")
        return

    # Unloading a large amount of filament in a single command can trip the 'Overlong Extrusion' warning in some firmware.  Unloads longer than 150mm are split into chunks.
    def _unload_filament(self, data: str) -> str:
        extrude_speed = 3000
        unload_distance = self.getSettingValueByKey("unload_distance")
        lines = data[len(data) - 1].split("\n")
        for index, line in enumerate(lines):
            # Unload the filament just before the hot end turns off.
            if line.startswith("M104") and "S0" in line:
                filament_str = "M83 ; [Unload] Relative extrusion\nM400 ; Complete all moves\n"
                if unload_distance > 150:
                    temp_unload = unload_distance
                    while temp_unload > 150:
                        filament_str += "G1 F" + str(int(extrude_speed)) + " E-150 ; Unload some\n"
                        temp_unload -= 150
                    if 0 < temp_unload <= 150:
                        filament_str += "G1 F" + str(int(extrude_speed)) + " E-" + str(temp_unload) + " ; Unload the remainder\nM82 ; Absolute Extrusion\nG92 E0 ; Reset Extruder\n"
                else:
                    filament_str += "G1 F" + str(int(extrude_speed)) + " E-" + str(unload_distance) + " ; Unload\nM82 ; Absolute Extrusion\nG92 E0 ; Reset Extruder\n"
                break
        lines[index] = filament_str + lines[index]
        data[len(data) - 1] = "\n".join(lines)
        return

    # Make an adjustment to the starting E location so the skirt/brim/raft starts out when the nozzle starts out.
    def _adjust_starting_e(self, data: str) -> str:
        curaApp = Application.getInstance().getGlobalContainerStack()
        retract_enabled = self._extruder[0].getProperty("retraction_enable", "value")
        if not retract_enabled:
            return
        adjust_amt = self.getSettingValueByKey("adjust_e_loc_to")
        lines = data[1].split("\n")
        lines.reverse()
        for index, line in enumerate(lines):
            if re.search("G1 F(\d*) E-(\d.*)", line) is not None:
                lines[index] = re.sub("G1 F(\d*) E-(\d.*)", f"G92 E{adjust_amt}", line)
                lines.reverse()
                data[1] = "\n".join(lines)
                break
        return

    # Format the purge or travel-to-start strings.  No reason they shouldn't look nice.
    def _format_string(self, any_gcode_str: str):
        temp_lines = any_gcode_str.split("\n")
        gap_len = 0
        for temp_line in temp_lines:
            if ";" in temp_line and not temp_line.startswith(";"):
                if gap_len - len(temp_line.split(";")[0]) + 1 < 0:
                    gap_len = len(temp_line.split(";")[0]) + 1
        if gap_len < 30: gap_len = 30
        for temp_index, temp_line in enumerate(temp_lines):
            if ";" in temp_line and not temp_line.startswith(";"):
                temp_lines[temp_index] = temp_line.replace(temp_line.split(";")[0], temp_line.split(";")[0] + str(" " * (gap_len - len(temp_line.split(";")[0]))),1)
            # This formats lines that are commented out but contain additional comments Ex:  ;M420 ; leveling mesh
            elif temp_line.startswith(";") and ";" in temp_line[1:]:
                temp_lines[temp_index] = temp_line[1:].replace(temp_line[1:].split(";")[0], ";" + temp_line[1:].split(";")[0] + str(" " * (gap_len - 1 - len(temp_line[1:].split(";")[0]))),1)
        any_gcode_str = "\n".join(temp_lines)
        return any_gcode_str

    # Get the actual layer start point of the print before adding movements
    def _get_real_start_point(self, first_section: str, bed_shape: str, origin_at_center: bool, machine_width: int, machine_depth: int):
        startup = first_section.split("\n")
        last_line = startup[len(startup) - 1]
        last_x = None
        if last_line[:3] in ("G0 ", "G1 ") and " X" in last_line and " Y" in last_line:
            last_x = self.getValue(last_line, "X")
            last_y = self.getValue(last_line, "Y")
        if last_x == None:
            return self._purge_end_loc
        else:
            if bed_shape == "rectangular" and not origin_at_center:
                midpoint_x = machine_width / 2
                midpoint_y = machine_depth / 2
            elif bed_shape in ("rectangular", "elliptic") and origin_at_center:
                midpoint_x = 0
                midpoint_y = 0
            if last_x < midpoint_x and last_y < midpoint_y:
                return "LF"
            if last_x > midpoint_x and last_y < midpoint_y:
                return "RF"
            if last_x > midpoint_x and last_y > midpoint_y:
                return "RR"
            if last_x < midpoint_x and last_y > midpoint_y:
                return "LR"

    # Multi-extruders may get a move to the prime tower just before layer 0 starts.  The adjusted lines move around the periphery instead of across the middle.
    def _get_adjustment_lines(self, prime_tower_loc: str, purge_end_loc: str, bed_shape: str, origin_at_center: bool, machine_width: int, machine_depth: int, travel_speed: int):
        adj_lines = ""
        if not origin_at_center:
            midpoint_x = machine_width / 2
            midpoint_y = machine_depth / 2
            max_x = machine_width - 7
            min_x = 7
            max_y = machine_depth - 7
            min_y = 7
        elif origin_at_center:
            midpoint_x = 0
            midpoint_y = 0
            max_x = (machine_width / 2) - 7
            min_x = -abs((machine_width / 2) - 7)
            max_y = (machine_depth / 2) - 7
            min_y = -abs((machine_depth / 2) - 7)
        if purge_end_loc == "LF":
            if prime_tower_loc == "LF":
                adj_lines = ""
            if prime_tower_loc == "RF":
                adj_lines = f"G0 F{travel_speed} X{max_x} ; Move to edge\nG0 F600 Z0 ; nail down the string\nG0 F600 Z2 ; move up\n"
            if prime_tower_loc == "RR":
                adj_lines = f"G0 F{travel_speed} X{max_x} ; Move to edge\nG0 F600 Z0 ; nail down the string\nG0 F600 Z2 ; move up\n"
            if prime_tower_loc == "LR":
                adj_lines = f"G0 F{travel_speed} Y{max_y} ; Move to edge\nG0 F600 Z0 ; nail down the string\nG0 F600 Z2 ; move up\n"
        elif purge_end_loc == "RR":
            if prime_tower_loc == "LF":
                adj_lines = f"G0 F{travel_speed} X{min_x} ; Move to edge\nG0 F600 Z0 ; nail down the string\nG0 F600 Z2 ; move up\n"
            if prime_tower_loc == "RF":
                adj_lines = f"G0 F{travel_speed} Y{min_y} ; Move to edge\nG0 F600 Z0 ; nail down the string\nG0 F600 Z2 ; move up\n"
            if prime_tower_loc == "RR":
                adj_lines = ""
            if prime_tower_loc == "LR":
                adj_lines = f"G0 F{travel_speed} X{min_x} ; Move to edge\nG0 F600 Z0 ; nail down the string\nG0 F600 Z2 ; move up\n"
        return adj_lines

    # Determine the quadrant that the prime tower rests in so the adjustments can be calculated
    def _prime_tower_quadrant(self, prime_tower_x, prime_tower_y, bed_shape, origin_at_center, machine_width, machine_depth):
        if not origin_at_center:
            midpoint_x = machine_width / 2
            midpoint_y = machine_depth / 2
            max_x = machine_width - 7
            min_x = 7
            max_y = machine_depth - 7
            min_y = 7
        elif origin_at_center:
            midpoint_x = 0
            midpoint_y = 0
            max_x = (machine_width / 2) - 7
            min_x = -abs((machine_width / 2) - 7)
            max_y = (machine_depth / 2) - 7
            min_y = -abs((machine_depth / 2) - 7)
        if prime_tower_x < midpoint_x and prime_tower_y < midpoint_y:
            prime_tower_location = "LF"
        elif prime_tower_x > midpoint_x and prime_tower_y < midpoint_y:
            prime_tower_location = "RF"
        elif prime_tower_x > midpoint_x and prime_tower_y > midpoint_y:
            prime_tower_location = "RR"
        elif prime_tower_x < midpoint_x and prime_tower_y > midpoint_y:
            prime_tower_location = "LR"
        return prime_tower_location

    # For some multi-extruder printers.  Takes into account a 'Move to Prime Tower' if there is one and adds orthononal travel moves to get there.
    def _move_to_prime_tower(self, startup_gcode: str, bed_shape: str, origin_at_center: bool, machine_width: int, machine_depth: int, travel_speed: int):
        adjustment_lines = ""
        curaApp = Application.getInstance().getGlobalContainerStack()
        prime_tower_x = curaApp.getProperty("prime_tower_position_x", "value")
        prime_tower_y = curaApp.getProperty("prime_tower_position_y", "value")
        prime_tower_loc = self._prime_tower_quadrant(prime_tower_x, prime_tower_y, bed_shape, origin_at_center, machine_width, machine_depth)
        if self._purge_end_loc == None:
            self._purge_end_loc = "LF"
        if prime_tower_loc != self._purge_end_loc:
            startup = startup_gcode.split("\n")
            for index, line in enumerate(startup):
                if ";LAYER_COUNT:" in line:
                    try:
                        if startup[index + 1].startswith("G0"):
                            prime_move = startup[index + 1] + " ; move to Prime Tower"
                            adjustment_lines = self._get_adjustment_lines(prime_tower_loc, self._purge_end_loc, bed_shape, origin_at_center, machine_width, machine_depth, travel_speed)
                            startup[index + 1] = adjustment_lines + prime_move
                            startup_gcode = "\n".join(startup)
                    except:
                        pass
        return startup_gcode