# August 2024 - GregValiant (Greg Foresi)
#
#  NOTE: You may have purge lines in your startup, or you may use this script, you should not do both.  The script will attempt to comment out existing StartUp purge lines.
# 'Add Purge Lines to StartUp' Allows the user to determine where the purge lines are on the build plate, or to not use purge lines if a print extends to the limits of the build surface.
#    This script will attempt to recognize and comment out purge lines in the StartUp Gcode but they should be removed if using this script.
# The setting 'Purge Line Length' is only avaialble for rectangular beds because I was too lazy to calculate the 45° arcs.
# 'Move to Start' takes an orthogonal path around the periphery before moving in to the print start location.  It eliminates strings across the print area.
# 'Adjust Starting E' is a correction in the E location before the skirt/brim starts.  The user can make an adjustment so that the skirt / brim / raft starts where it should.
# 'Unload' adds code to the Ending Gcode that will unload the filament from the machine.  The unlaod distance is broken into chunks to avoid overly long E distances.
#  Added extra moves to account for Cura adding a "Travel to Prime Tower" move that can cross the middle of the build surface.
#  Added ability to take 'disallowed areas' into account.

from ..Script import Script
from UM.Application import Application
from UM.Message import Message
import re
from UM.Logger import Logger

class PurgeLinesAndUnload(Script):

    def initialize(self) -> None:
        super().initialize()
        # Get the StartUp Gcode from Cura and attempt to catch if it contains purge lines.  Message the user if an extrusion is in the startup.
        self.curaApp = Application.getInstance().getGlobalContainerStack()
        startup_gcode = self.curaApp.getProperty("machine_start_gcode", "value")
        start_lines = startup_gcode.splitlines()
        for line in start_lines:
            if "G1" in line and " E" in line and (" X" in line or " Y" in line):
                Message(title = "[Purge Lines and Unload]", text = "It appears that there are 'purge lines' in the StartUp Gcode.  Using the 'Add Purge Lines' function of this script will comment them out.").show()
                break
        # 'is rectangular' is used to disable half-length purge lines for elliptic beds.
        self._instance.setProperty("is_rectangular", "value", True if self.curaApp.getProperty("machine_shape", "value") == "rectangular" else False)
        self._instance.setProperty("move_to_prime_tower", "value", True if self.curaApp.getProperty("machine_extruder_count", "value") > 1 else False)
        self.extruder = self.curaApp.extruderList
        #This is set in 'Add Purge Lines' and is used by 'Move to Start' to indicate which corner the nozzle is in after the purge lines
        self.start_location = "LF"
        # Set the default E adjustment
        self._instance.setProperty("adjust_e_loc_to", "value", -abs(round(float(self.extruder[0].getProperty("retraction_amount", "value")), 1)))

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
                "unload_quick_purge":                
                {
                    "label": "    Quick purge before unload",
                    "description": "When printing something fine that has a lot of retractions in a short space (like lettering or spires) right before the unload, the filament can get hung up in the hot end and unload can fail.  A quick purge will soften the end of the filament so it will retract correctly.  This 'quick puge' will take place at the last position of the nozzle.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_unload"
                },
                "move_to_prime_tower":
                {
                    "label": "Hidden setting",
                    "description": "Hidden setting that enables 'move_to_prime_tower' for multi extruder machines.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": false
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
        # Exit if the Gcode has already been processed.
        for num in range(0, len(data)):
            layer = data[num].split("\n")
            for line in layer:
                if ";LAYER:" in line:
                    break
                elif "PurgeLinesAndUnload" in line:
                    Logger.log("i", "[Add Purge Lines and Unload Filament] has already run on this gcode.")
                    return data
        # This will be True when there are more than 4 'machine_disallowed_areas'
        self.show_warning = False
        self.disallowed_areas = self.curaApp.getProperty("machine_disallowed_areas", "value")
        self.extruder = self.curaApp.extruderList
        self.extruder_count = self.curaApp.getProperty("machine_extruder_count", "value")
        self.bed_shape = self.curaApp.getProperty("machine_shape", "value")
        self.origin_at_center = self.curaApp.getProperty("machine_center_is_zero", "value")
        self.machine_width = self.curaApp.getProperty("machine_width", "value")
        self.machine_depth = self.curaApp.getProperty("machine_depth", "value")
        self.machine_left = 1.0
        self.machine_right = self.machine_width - 1.0
        self.machine_front = 1.0
        self.machine_back = self.machine_depth - 1.0
        # Adjust the usable size of the bed per any 'disallowed areas'
        max_print_size = self._get_build_plate_extents()
        self.speed_travel = self.extruder[0].getProperty("speed_travel", "value") * 60
        # The start location changes according to which quadrant the nozzle is in at the beginning
        self.start_location = self._get_real_start_point(data[1])

        # Run the selected procedures
        # Mapping settings to corresponding methods
        procedures = {
            "add_purge_lines": self._add_purge_lines,
            "move_to_prime_tower": self._move_to_prime_tower,
            "move_to_start": self._move_to_start,
            "adjust_starting_e": self._adjust_starting_e,
            "enable_unload": self._unload_filament
        }
        # Run selected procedures
        for setting, method in procedures.items():
            if self.getSettingValueByKey(setting):
                method(data)
        # Format the startup and ending gcodes
        data[1] = self._format_string(data[1])
        data[-1] = self._format_string(data[-1])
        if self.getSettingValueByKey("add_purge_lines"):
            if self.show_warning:
                msg_text = "The printer has ( " + str(len(self.disallowed_areas)) + " ) 'disallowed areas'.  That can cause the area available for the purge lines to be small.\nOpen the Gcode file for preview in Cura and check the purge line location to insure it is acceptable."
            else:
                msg_text = "Open the Gcode file for preview in Cura.  Make sure the 'Purge Lines' don't run underneath something else and are acceptable."            
            Message(title = "[Purge Lines and Unload]", text = msg_text).show()
        return data

    def _get_real_start_point(self, first_section: str) -> str:
        last_x = 0.0
        last_y = 0.0
        start_quadrant = "LF"
        startup = first_section.split("\n")
        for line in startup:
            if (line.startswith(";") and not line.startswith(";LAYER_COUNT")) or line == "":
                continue
            if line.startswith("G28"):
                last_x = 0
                last_y = 0
            elif line[:3] in ["G0 ", "G1 "]:
                if " X" in line:
                    last_x = self.getValue(line, "X")
                if " Y" in line:
                    last_y = self.getValue(line, "Y")
            # Stop at the Layer Count line to exclude a possible move to the prime tower
            elif "LAYER_COUNT" in line:
                break
        if self.bed_shape == "rectangular" and not self.origin_at_center:
            midpoint_x = self.machine_width / 2
            midpoint_y = self.machine_depth / 2
        elif self.origin_at_center:
            midpoint_x = 0.0
            midpoint_y = 0.0
        if last_x <= midpoint_x and last_y <= midpoint_y:
            start_quadrant = "LF"
        elif last_x > midpoint_x and last_y < midpoint_y:
            start_quadrant = "RF"
        elif last_x > midpoint_x and last_y > midpoint_y:
            start_quadrant = "RR"
        elif last_x < midpoint_x and last_y > midpoint_y:
            start_quadrant = "LR"
        return start_quadrant

    # For some multi-extruder printers.  Takes into account a 'Move to Prime Tower' if there is one and adds orthogonal travel moves to get there.
    # 'Move to Prime Tower' does not require that the prime tower is enabled, only that 'machine_extruder_start_position_?' is in the definition file.
    def _move_to_prime_tower(self, first_section: str) -> str:
        if self.extruder_count == 1:
            return first_section
        adjustment_lines = ""
        move_to_prime_present = False
        prime_tower_x = self.curaApp.getProperty("prime_tower_position_x", "value")
        prime_tower_y = self.curaApp.getProperty("prime_tower_position_y", "value")
        prime_tower_loc = self._prime_tower_quadrant(prime_tower_x, prime_tower_y)
        # Shortstop an error if Start Location comes through as None
        if self.start_location == None:
            self.start_location = "LF"
        if prime_tower_loc != self.start_location:
            startup = first_section[1].split("\n")
            for index, line in enumerate(startup):
                if ";LAYER_COUNT:" in line:
                    try:
                        if startup[index + 1].startswith("G0"):
                            prime_move = startup[index + 1] + " ; Move to Prime Tower"
                            adjustment_lines = self._get_adjustment_lines(prime_tower_loc)
                            startup[index + 1] = adjustment_lines + prime_move + "\n" + startup[index]
                            startup.pop(index)
                            first_section[1] = "\n".join(startup)
                            move_to_prime_present = True
                    except:
                        pass
        # The start_location changes to the prime tower location in case 'Move to Start' is enabled.
        if move_to_prime_present:
            self.start_location = prime_tower_loc
        return first_section

    # Determine the quadrant that the prime tower rests in so the orthogonal moves can be calculated
    def _prime_tower_quadrant(self, prime_tower_x: float, prime_tower_y: float):
        if not self.origin_at_center:
            midpoint_x = self.machine_width / 2
            midpoint_y = self.machine_depth / 2
            max_x = self.machine_width - 1
            min_x = 1
            max_y = self.machine_depth - 1
            min_y = 1
        elif self.origin_at_center:
            midpoint_x = 0
            midpoint_y = 0
            max_x = (self.machine_width / 2) - 1
            min_x = -abs((self.machine_width / 2) - 1)
            max_y = (self.machine_depth / 2) - 1
            min_y = -abs((self.machine_depth / 2) - 1)
        if prime_tower_x < midpoint_x and prime_tower_y < midpoint_y:
            self.prime_tower_location = "LF"
        elif prime_tower_x > midpoint_x and prime_tower_y < midpoint_y:
            self.prime_tower_location = "RF"
        elif prime_tower_x > midpoint_x and prime_tower_y > midpoint_y:
            self.prime_tower_location = "RR"
        elif prime_tower_x < midpoint_x and prime_tower_y > midpoint_y:
            self.prime_tower_location = "LR"
        return self.prime_tower_location

    # This puts the 'Move to Prime' tower lines together when they are required
    def _get_adjustment_lines(self, prime_tower_loc: str):
        adj_lines = ";MESH:NONMESH---------[Move to Prime Tower]"
        if self.start_location == "LF":
            if prime_tower_loc == "RF":
                adj_lines += f"\nG0 F{self.speed_travel} X{self.machine_right} ; Start move\nG0 F600 Z0 ; Nail down the string\nG0 F600 Z2 ; Move up\n"
            if prime_tower_loc == "RR":
                adj_lines += f"\nG0 F{self.speed_travel} X{self.machine_right} ; Start move\nG0 F600 Z0 ; Nail down the string\nG0 F600 Z2 ; Move up\n"
            if prime_tower_loc == "LR":
                adj_lines += f"\nG0 F{self.speed_travel} Y{self.machine_back} ; Start move\nG0 F600 Z0 ; Nail down the string\nG0 F600 Z2 ; Move up\n"
        elif self.start_location == "RR":
            if prime_tower_loc == "LF":
                adj_lines += f"\nG0 F{self.speed_travel} X{self.machine_left} ; Start move\nG0 F600 Z0 ; Nail down the string\nG0 F600 Z2 ; Move up\n"
            if prime_tower_loc == "RF":
                adj_lines += f"\nG0 F{self.speed_travel} Y{self.machine_front} ; Start move\nG0 F600 Z0 ; Nail down the string\nG0 F600 Z2 ; Move up\n"
            if prime_tower_loc == "LR":
                adj_lines += f"\nG0 F{self.speed_travel} X{self.machine_left} ; Start move to Prime Tower\nG0 F600 Z0 ; Nail down the string\nG0 F600 Z2 ; Move up\n"
        return adj_lines

    def _get_build_plate_extents(self) -> float:
        # Machine disallwed areas can be ordered at the whim of the definition author and cannot be counted on when parsed
        # This determines a simple rectangle that will be available for the purge lines.  For some machines (Ex: UM3) it can be a small rectangle.
        if self.bed_shape == "rectangular":
            if self.disallowed_areas != []:
                if len(self.disallowed_areas) > 4:
                    self.show_warning = True
                mid_x = 0
                mid_y = 0
                left_x = -(self.machine_width / 2)
                right_x = (self.machine_width / 2)
                front_y = (self.machine_depth / 2)
                back_y = -(self.machine_depth / 2)
                for rect in self.disallowed_areas:
                    for corner in rect:
                        x = corner[0]
                        if x < mid_x and x > left_x:
                            left_x = x
                        if x > mid_x and x < right_x:
                            right_x = x
                        y = corner[1]
                        if y > mid_y and y < front_y:
                            front_y = y
                        if y < mid_y and y > back_y:
                            back_y = y
                if self.origin_at_center:
                    self.machine_left = round(left_x + 1, 2)
                    self.machine_right = round(right_x - 1, 2)
                    self.machine_front = round(front_y - 1, 2)
                    self.machine_back = round(back_y + 1, 2)
                else:
                    self.machine_left = round(left_x + 1 + self.machine_width / 2, 2)
                    self.machine_right = round(right_x - 1 + self.machine_width / 2, 2)
                    self.machine_front = round((self.machine_depth / 2) - front_y - 1, 2)
                    self.machine_back = round((self.machine_depth / 2) - back_y + 1       , 2)             
            else:
                if self.origin_at_center:
                    self.machine_left = round(-(self.machine_width/2) + 1, 2)
                    self.machine_right = round((self.machine_width/2) - 1, 2)
                    self.machine_front = round(-(self.machine_depth/2) + 1, 2)
                    self.machine_back = round((self.machine_depth/2) - 1, 2)
                else:
                    self.machine_left = 1
                    self.machine_right = self.machine_width - 1
                    self.machine_front = 1
                    self.machine_back = self.machine_depth - 1                    
        return

    # Add Purge Lines to the user defined position on the build plate
    def _add_purge_lines(self, data_1: str):
        retract_dist = self.extruder[0].getProperty("retraction_amount", "value")
        retract_enable = self.extruder[0].getProperty("retraction_enable", "value")
        retract_speed = self.extruder[0].getProperty("retraction_retract_speed", "value") * 60
        material_diameter = self.extruder[0].getProperty("material_diameter", "value")
        mm3_per_mm = (material_diameter / 2)**2 * 3.14159
        init_line_width = self.extruder[0].getProperty("skirt_brim_line_width", "value")
        where_at = self.getSettingValueByKey("purge_line_location")
        print_speed = round(self.extruder[0].getProperty("speed_print", "value") * 60 * .75)
        purge_extrusion_full = True if self.getSettingValueByKey("purge_line_length") == "purge_full" else False
        purge_str = ";TYPE:CUSTOM----------[Purge Lines]\nG0 F600 Z2 ; Move up\nG92 E0 ; Reset extruder\n"

        # Normal cartesian printer with origin at the left front corner
        if self.bed_shape == "rectangular" and not self.origin_at_center:
            if where_at == "purge_left":
                purge_len = int(self.machine_back - 20) if purge_extrusion_full else int((self.machine_back - self.machine_front) / 2)
                y_stop = int(self.machine_back - 10) if purge_extrusion_full else int(self.machine_depth / 2)
                purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
                purge_str = purge_str.replace("Lines", "Lines at MinX")
                purge_str += f"G0 F{self.speed_travel} X{self.machine_left} Y{self.machine_front + 10} ; Move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G1 F{print_speed} X{self.machine_left} Y{y_stop} E{purge_volume} ; First line\n"
                purge_str += f"G0 X{self.machine_left + 3} Y{y_stop} ; Move over\n"
                purge_str += f"G1 F{print_speed} X{self.machine_left + 3} Y{self.machine_front + 10} E{round(purge_volume * 2,5)} ; Second line\n"
                purge_str += f"G1 F{int(retract_speed)} E{round(purge_volume * 2 - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                purge_str += f"G0 F{print_speed} X{self.machine_left + 3} Y{self.machine_front + 20} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 X{self.machine_left + 3} Y{self.machine_front + 35} ; Wipe\n"
                self.start_location = "LF"
            elif where_at == "purge_right":
                purge_len = int(self.machine_depth - 20) if purge_extrusion_full else int((self.machine_back - self.machine_front) / 2)
                y_stop = int(self.machine_front + 10) if purge_extrusion_full else int(self.machine_depth / 2)
                purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
                purge_str = purge_str.replace("Lines", "Lines at MaxX")
                purge_str += f"G0 F{self.speed_travel} X{self.machine_right} ; Move\nG0 Y{self.machine_back - 10} ; Move\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G1 F{print_speed} X{self.machine_right} Y{y_stop} E{purge_volume} ; First line\n"
                purge_str += f"G0 X{self.machine_right - 3} Y{y_stop} ; Move over\n"
                purge_str += f"G1 F{print_speed} X{self.machine_right - 3} Y{self.machine_back - 10} E{purge_volume * 2} ; Second line\n"
                purge_str += f"G1 F{int(retract_speed)} E{round(purge_volume * 2 - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                purge_str += f"G0 F{print_speed} X{self.machine_right - 3} Y{self.machine_back - 20} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 X{self.machine_right - 3} Y{self.machine_back - 35} ; Wipe\n"
                self.start_location = "RR"
            elif where_at == "purge_bottom":
                purge_len = int(self.machine_width) - 20 if purge_extrusion_full else int((self.machine_right - self.machine_left) / 2)
                x_stop = int(self.machine_right - 10) if purge_extrusion_full else int(self.machine_width/2)
                purge_str = purge_str.replace("Lines", "Lines at MinY")
                purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
                purge_str += f"G0 F{self.speed_travel} X{self.machine_left + 10} Y{self.machine_front} ; Move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G1 F{print_speed} X{x_stop} Y{self.machine_front} E{purge_volume} ; First line\n"
                purge_str += f"G0 X{x_stop} Y{self.machine_front + 3} ; Move over\n"
                purge_str += f"G1 F{print_speed} X{self.machine_left + 10} Y{self.machine_front + 3} E{purge_volume * 2} ; Second line\n"
                purge_str += f"G1 F{int(retract_speed)} E{round(purge_volume * 2 - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                purge_str += f"G0 F{print_speed} X{self.machine_left + 20} Y{self.machine_front + 3} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 X{self.machine_left + 35} Y{self.machine_front + 3} ; Wipe\n"
                self.start_location = "LF"
            elif where_at == "purge_top":
                purge_len = int(self.machine_width - 20) if purge_extrusion_full else int((self.machine_right - self.machine_left)/2)
                x_stop = int(self.machine_left + 10) if purge_extrusion_full else int(self.machine_width/2)
                purge_str = purge_str.replace("Lines", "Lines at MaxY")
                purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
                purge_str += f"G0 F{self.speed_travel} Y{self.machine_back} ; Ortho Move to back\n"
                purge_str += f"G0 X{self.machine_right - 10} ; Ortho move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G1 F{print_speed} X{x_stop} Y{self.machine_back} E{purge_volume} ; First line\n"
                purge_str += f"G0 X{x_stop} Y{self.machine_back - 3} ; Move over\n"
                purge_str += f"G1 F{print_speed} X{self.machine_right - 10} Y{self.machine_back - 3} E{purge_volume * 2} ; Second line\n"
                purge_str += f"G1 F{int(retract_speed)} E{round(purge_volume * 2 - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait 1 second\n"
                purge_str += f"G0 F{print_speed} X{self.machine_right - 20} Y{self.machine_back - 3} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 X{self.machine_right - 35} Y{self.machine_back - 3} ; Wipe\n"
                self.start_location = "RR"

        # Some cartesian printers (BIBO, Weedo, MethodX, etc.) are Origin at Center
        elif self.bed_shape == "rectangular" and self.origin_at_center:
            if where_at == "purge_left":
                purge_len = int(self.machine_back - self.machine_front-20) if purge_extrusion_full else abs(int(self.machine_front - 10))
                y_stop = int(self.machine_back - 10) if purge_extrusion_full else 0
                purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
                purge_str += f"G0 F{self.speed_travel} X{self.machine_left} Y{self.machine_front + 10} ; Move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G1 F{print_speed} X{self.machine_left} Y{y_stop} E{purge_volume} ; First line\n"
                purge_str += f"G0 X{self.machine_left + 3} Y{y_stop} ; Move over\n"
                purge_str += f"G1 F{print_speed} X{self.machine_left + 3} Y{self.machine_front + 10} E{round(purge_volume * 2, 5)} ; Second line\n"
                purge_str += f"G1 F{int(retract_speed)} E{round(purge_volume * 2 - retract_dist, 5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                purge_str += f"G0 F{print_speed} X{self.machine_left + 3} Y{self.machine_front + 20} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 X{self.machine_left + 3} Y{self.machine_front + 35} ; Wipe\n"
                self.start_location = "LF"
            elif where_at == "purge_right":
                purge_len = int(self.machine_back - 20) if purge_extrusion_full else int((self.machine_back - self.machine_front)/2)
                y_stop = int(self.machine_front + 10) if purge_extrusion_full else 0
                purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
                purge_str += f"G0 F{self.speed_travel} X{self.machine_right} Z2 ; Move\nG0 Y{self.machine_back - 10} Z2 ; Move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G1 F{print_speed} X{self.machine_right} Y{y_stop} E{purge_volume} ; First line\n"
                purge_str += f"G0 X{self.machine_right - 3} Y{y_stop} ; Move over\n"
                purge_str += f"G1 F{print_speed} X{self.machine_right - 3} Y{self.machine_back - 10} E{purge_volume * 2} ; Second line\n"
                purge_str += f"G1 F{int(retract_speed)} E{round(purge_volume * 2 - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                purge_str += f"G0 F{print_speed} X{self.machine_right - 3} Y{self.machine_back - 20} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 F{self.speed_travel} X{self.machine_right - 3} Y{self.machine_back - 35} ; Wipe\n"
                self.start_location = "RR"
            elif where_at == "purge_bottom":
                purge_len = int(self.machine_right - self.machine_left - 20) if purge_extrusion_full else int((self.machine_right - self.machine_left) / 2)
                x_stop = int(self.machine_right - 10) if purge_extrusion_full else 0
                purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
                purge_str += f"G0 F{self.speed_travel} X{self.machine_left + 10} Z2 ; Move\nG0 Y{self.machine_front} Z2 ; Move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G1 F{print_speed} X{x_stop} Y{self.machine_front} E{purge_volume} ; First line\n"
                purge_str += f"G0 X{x_stop} Y{self.machine_front + 3} ; Move over\n"
                purge_str += f"G1 F{print_speed} X{self.machine_left + 10} Y{self.machine_front + 3} E{purge_volume * 2} ; Second line\n"
                purge_str += f"G1 F{int(retract_speed)} E{round(purge_volume * 2 - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                purge_str += f"G0 F{print_speed} X{self.machine_left + 20} Y{self.machine_front + 3} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 F{print_speed} X{self.machine_left + 35} Y{self.machine_front + 3} ; Wipe\n"
                self.start_location = "LF"
            elif where_at == "purge_top":
                purge_len = int(self.machine_right - self.machine_left - 20) if purge_extrusion_full else abs(int(self.machine_right - 10))
                x_stop = int(self.machine_left + 10) if purge_extrusion_full else 0
                purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
                purge_str += f"G0 F{self.speed_travel} Y{self.machine_back} Z2; Ortho Move to back\n"
                purge_str += f"G0 X{self.machine_right - 10} Z2 ; Ortho Move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G1 F{print_speed} X{x_stop} Y{self.machine_back} E{purge_volume} ; First line\n"
                purge_str += f"G0 X{x_stop} Y{self.machine_back - 3} ; Move over\n"
                purge_str += f"G1 F{print_speed} X{self.machine_right - 10} Y{self.machine_back - 3} E{purge_volume * 2} ; Second line\n"
                purge_str += f"G1 F{int(retract_speed)} E{round(purge_volume * 2 - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                purge_str += f"G0 F{print_speed} X{self.machine_right - 20} Y{self.machine_back - 3} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 F{print_speed} X{self.machine_right - 35} Y{self.machine_back - 3} ; Wipe\n"
                self.start_location = "RR"

        # Elliptic printers with Origin at Center
        elif self.bed_shape == "elliptic":
            if where_at in ["purge_left","purge_right"]:
                radius_1 = round((self.machine_width / 2) - 1,2)
            elif where_at in ["purge_bottom", "purge_top"]:
                radius_1 = round((self.machine_depth / 2) - 1,2)
            purge_len = int(radius_1) * 3.14159 / 4
            purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
            if where_at == "purge_left":
                purge_str += f"G0 F{self.speed_travel} X-{round(radius_1 * .707, 2)} Y-{round(radius_1 * .707,2)} ; Travel\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G2 F{print_speed} X-{round(radius_1 * .707,2)} Y{round(radius_1 * .707,2)} I{round(radius_1 * .707,2)} J{round(radius_1 * .707,2)} E{purge_volume} ; First Arc\n"
                purge_str += f"G0 X-{round((radius_1 - 3) * .707,2)} Y{round((radius_1 - 3) * .707,2)} ; Move Over\n"
                purge_str += f"G3 F{print_speed} X-{round((radius_1 - 3) * .707,2)} Y-{round((radius_1 - 3) * .707,2)} I{round((radius_1 - 3) * .707,2)} J-{round((radius_1 - 3) * .707,2)} E{purge_volume * 2} ; Second Arc\n"
                purge_str += f"G1 X-{round((radius_1 - 3) * .707 - 25,2)} E{round(purge_volume * 2 + 1,5)} ; Move Over\n"
                purge_str += f"G1 F{int(retract_speed)} E{round((purge_volume * 2 + 1) - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z5 ; Move Up\nG4 S1 ; Wait 1 Second\n"
                purge_str += f"G0 F{print_speed} X-{round((radius_1 - 3) * .707 - 15,2)} Z0.3 ; Slide Over\n"
                purge_str += f"G0 F{print_speed} X-{round((radius_1 - 3) * .707,2)} ; Wipe\n"
                self.start_location = "LF"
            elif where_at == "purge_right":
                purge_str += f"G0 F{self.speed_travel} X{round(radius_1 * .707, 2)} Y-{round(radius_1 * .707,2)} ; Travel\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G3 F{print_speed} X{round(radius_1 * .707,2)} Y{round(radius_1 * .707,2)} I-{round(radius_1 * .707,2)} J{round(radius_1 * .707,2)} E{purge_volume} ; First Arc\n"
                purge_str += f"G0 X{round((radius_1 - 3) * .707,2)} Y{round((radius_1 - 3) * .707,2)} ; Move Over\n"
                purge_str += f"G2 F{print_speed} X{round((radius_1 - 3) * .707,2)} Y-{round((radius_1 - 3) * .707,2)} I-{round((radius_1 - 3) * .707,2)} J-{round((radius_1 - 3) * .707,2)} E{purge_volume * 2} ; Second Arc\n"
                purge_str += f"G1 X{round((radius_1 - 3) * .707 - 25,2)} E{round(purge_volume * 2 + 1,5)} ; Move Over\n"
                purge_str += f"G1 F{int(retract_speed)} E{round((purge_volume * 2 + 1) - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z5 ; Move Up\nG4 S1 ; Wait 1 Second\n"
                purge_str += f"G0 F{print_speed} X{round((radius_1 - 3) * .707 - 15,2)} Z0.3 ; Slide Over\n"
                purge_str += f"G0 F{print_speed} X{round((radius_1 - 3) * .707,2)}\n"
                self.start_location = "RR"
            elif where_at == "purge_bottom":
                purge_str += f"G0 F{self.speed_travel} X-{round(radius_1 * .707, 2)} Y-{round(radius_1 * .707,2)} ; Travel\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G3 F{print_speed} X{round(radius_1 * .707,2)} Y-{round(radius_1 * .707,2)} I{round(radius_1 * .707,2)} J{round(radius_1 * .707,2)} E{purge_volume} ; First Arc\n"
                purge_str += f"G0 X{round((radius_1 - 3) * .707,2)} Y-{round((radius_1 - 3) * .707,2)} ; Move Over\n"
                purge_str += f"G2 F{print_speed} X-{round((radius_1 - 3) * .707,2)} Y-{round((radius_1 - 3) * .707,2)} I-{round((radius_1 - 3) * .707,2)} J{round((radius_1 - 3) * .707,2)} E{purge_volume * 2} ; Second Arc\n"
                purge_str += f"G1 Y-{round((radius_1 - 3) * .707 - 25,2)} E{round(purge_volume * 2 + 1, 5)} ; Move Over\n"
                purge_str += f"G1 F{int(retract_speed)} E{round((purge_volume * 2 + 1) - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z5 ; Move Up\nG4 S1 ; Wait 1 Second\n"
                purge_str += f"G0 F{print_speed} Y-{round((radius_1 - 3) * .707 - 15,2)} Z0.3 ; Slide Over\n"
                purge_str += f"G0 F{print_speed} Y-{round((radius_1 - 3) * .707,2)}\n"
                self.start_location = "LF"
            elif where_at == "purge_top":
                purge_str += f"G0 F{self.speed_travel} X{round(radius_1 * .707, 2)} Y{round(radius_1 * .707,2)} ; Travel\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G3 F{print_speed} X-{round(radius_1 * .707,2)} Y{round(radius_1 * .707,2)} I-{round(radius_1 * .707,2)} J-{round(radius_1 * .707,2)} E{purge_volume} ; First Arc\n"
                purge_str += f"G0 X-{round((radius_1 - 3) * .707,2)} Y{round((radius_1 - 3) * .707,2)} ; Move Over\n"
                purge_str += f"G2 F{print_speed} X{round((radius_1 - 3) * .707,2)} Y{round((radius_1 - 3) * .707,2)} I{round((radius_1 - 3) * .707,2)} J-{round((radius_1 - 3) * .707,2)} E{purge_volume * 2} ; Second Arc\n"
                purge_str += f"G1 Y{round((radius_1 - 3) * .707 - 25,2)} E{round(purge_volume * 2 + 1,5)} ; Move Over\n"
                purge_str += f"G1 F{int(retract_speed)} E{round((purge_volume * 2 + 1) - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z5\nG4 S1\n"
                purge_str += f"G0 F{print_speed} Y{round((radius_1 - 3) * .707 - 15,2)} Z0.3 ; Slide Over\n"
                purge_str += f"G0 F{print_speed} Y{round((radius_1 - 3) * .707,2)}\n"
                self.start_location = "RR"

        # Common ending for purge_str
        purge_str += "G0 F600 Z2 ; Move Z\n;---------------------[End of Purge]"

        # Comment out any existing purge lines in data_1
        startup = data_1[1].split("\n")
        for index, line in enumerate(startup):
            if "G1"in line and " E" in line and (" X" in line or " Y" in line):
                next_line = index
                try:
                    while not startup[next_line].startswith ("G92 E0"):
                        startup[next_line] = ";" + startup[next_line]
                        next_line += 1
                except:
                    break
        data_1[1] = "\n".join(startup)

        # Find the insertion location in data_1
        purge_str = self._format_string(purge_str)
        startup_section = data_1[1].split("\n")
        insert_index = len(startup_section)-1
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
        data_1[1] = "\n".join(startup_section)
        return data_1

    # Travel moves around the bed periphery to keep strings from crossing the footprint of the model.
    def _move_to_start(self, data: str) -> str:
        start_x = None
        start_y = None
        layer = data[2].split("\n")
        for line in layer:
            if line.startswith("G0") and " X" in line and " Y" in line:
                start_x = self.getValue(line, "X")
                start_y = self.getValue(line, "Y")
                break
        if start_x == None: start_x = 0
        if start_y == None: start_y = 0
        if self.start_location == None:
            self.start_location = "LF"
        move_str = f";MESH:NONMESH---------[Travel to Layer Start]\nG0 F600 Z2 ; Move up\n"
        midpoint_x = self.machine_width / 2
        midpoint_y = self.machine_depth / 2
        if not self.origin_at_center:
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

        # Depending on which quadrant the XY layer start is, move around the periphery before coming in to the start position
        if self.bed_shape == "rectangular" and not self.origin_at_center:
            if self.start_location == "LF":
                if goto_str == "LtFrt":
                    move_str += f"G0 F{self.speed_travel} X{self.machine_right - 5} ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{self.speed_travel} Y{self.machine_front + 5} ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                elif goto_str == "RtFrt":
                    move_str += f"G0 F{self.speed_travel} X{self.machine_left + 5} Z2; Ortho Move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{self.speed_travel} Y{self.machine_front + 5} Z2 ; Ortho Move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{self.speed_travel} X{start_x} ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                elif goto_str == "LtBk":
                    move_str += f"G0 F{self.speed_travel} X{self.machine_left + 5} ; Ortho Move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{self.speed_travel} Y{self.machine_front + 5} Z2 ; Move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{self.speed_travel} Y{start_y} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                elif goto_str == "RtBk":
                    move_str += f"G0 F{self.speed_travel} X{self.machine_left + 5} ; Move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{self.speed_travel} Y{self.machine_front + 5} Z2 ; Move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{self.speed_travel} X{self.machine_right - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{self.speed_travel} Y{start_y} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
            elif self.start_location == "RR":
                if goto_str == "LtFrt":
                    move_str += f"G0 F{self.speed_travel} X{self.machine_left + 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{self.speed_travel} Y{self.machine_front + 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                elif goto_str == "RtFrt":
                    move_str += f"G0 F{self.speed_travel} X{start_x} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{self.speed_travel} Y{self.machine_front + 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                elif goto_str == "LtBk":
                    move_str += f"G0 F{self.speed_travel} X{self.machine_left + 5} Z2 ; Move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                elif goto_str == "RtBk":
                    move_str += f"G0 F{self.speed_travel} X{self.machine_right - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{self.speed_travel} Y{start_y} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"

        elif self.bed_shape == "rectangular" and self.origin_at_center:
            if self.start_location == "LF":
                if goto_str == "LtFrt":
                    move_str += f"G0 F{self.speed_travel} X{self.machine_left + 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{self.speed_travel} Y{self.machine_back - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                elif goto_str == "RtFrt":
                    move_str += f"G0 F{self.speed_travel} X{self.machine_right - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{self.speed_travel} Y{self.machine_back - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                elif goto_str == "LtBk":
                    move_str += f"G0 F{self.speed_travel} X{self.machine_right - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{self.speed_travel} Y{self.machine_back - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                elif goto_str == "RtBk":
                    move_str += f"G0 F{self.speed_travel} X{self.machine_right - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{self.speed_travel} Y{self.machine_back - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
            elif self.start_location == "RR":
                if goto_str == "LtFrt":
                    move_str += f"G0 F{self.speed_travel} X{self.machine_right - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{self.speed_travel} Y{self.machine_back - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                elif goto_str == "RtFrt":
                    move_str += f"G0 F{self.speed_travel} X{self.machine_right - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{self.speed_travel} Y{self.machine_back - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                elif goto_str == "LtBk":
                    move_str += f"G0 F{self.speed_travel} X{self.machine_right - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{self.speed_travel} Y{self.machine_back - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                elif goto_str == "RtBk":
                    move_str += f"G0 F{self.speed_travel} X{self.machine_right - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"
                    move_str += f"G0 F{self.speed_travel} Y{self.machine_back - 5} Z2 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z2 ; Move up\n"

        elif self.bed_shape == "elliptic" and self.origin_at_center:
            radius = self.machine_width / 2
            offset_sin = round(2**.5 / 2 * radius, 2)
            if self.start_location == "LR":
                if goto_str == "LtFrt":
                    move_str += f"G0 F{self.speed_travel} X-{offset_sin} Z2 ; Move\nG0 Y-{offset_sin} Z2 ; Move to start\n"
                elif goto_str == "LtBk":
                    move_str += f"G2 X0 Y{offset_sin} I{offset_sin} J{offset_sin} ; Move around to start\n"
                elif goto_str == "RtFrt":
                    move_str += f"G0 F{self.speed_travel} X{offset_sin} Z2 ; Ortho move\nG0 Y-{offset_sin} Z2 ; Ortho move\n"
                elif goto_str == "RtBk":
                    move_str += f"G0 F{self.speed_travel} X{offset_sin} Z2 ; Ortho move\nG0 Y{offset_sin} Z2 ; Ortho move\n"
            elif self.start_location == "RR":
                if goto_str == "LtFrt":
                    move_str += f"G0 F{self.speed_travel} X-{offset_sin} Z2 ; Move\nG0 Y-{offset_sin} Z2 ; Move to start\n"
                elif goto_str == "LtBk":
                    move_str += f"G0 F{self.speed_travel} X-{offset_sin} Z2 ; Ortho move\nG0 Y{offset_sin} Z2 ; Ortho move\n"
                elif goto_str == "RtFrt":
                    move_str += f"G0 F{self.speed_travel} X{offset_sin} Z2 ; Ortho move\nG0 Y-{offset_sin} Z2 ; Ortho move\n"
                elif goto_str == "RtBk":
                    move_str += f"G0 F{self.speed_travel} X{offset_sin} Z2 ; Ortho move\nG0 Y{offset_sin} Z2 ; Ortho move\n"
            elif self.start_location == "LF":
                if goto_str == "LtFrt":
                    move_str += f"G0 F{self.speed_travel} X-{offset_sin} Z2 ; Move\nG0 Y-{offset_sin} Z2 ; Move to start\n"
                elif goto_str == "LtBk":
                    move_str += f"G0 F{self.speed_travel} X-{offset_sin} Z2 ; Ortho move\nG0 Y{offset_sin} Z2 ; Ortho move\n"
                elif goto_str == "RtFrt":
                    move_str += f"G0 F{self.speed_travel} X{offset_sin} Z2 ; Ortho move\nG0 Y-{offset_sin} Z2 ; Ortho move\n"
                elif goto_str == "RtBk":
                    move_str += f"G0 F{self.speed_travel} X{offset_sin} Z2 ; Ortho move\nG0 Y{offset_sin} Z2 ; Ortho move\n"
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

    # Unloading a large amount of filament in a single command can trip the 'Overlong Extrusion' warning in some firmware.  Unloads longer than 150mm are split into individual 150mm segments.
    def _unload_filament(self, data: str) -> str:
        extrude_speed = 3000
        quick_purge_speed = 240
        retract_amount = self.extruder[0].getProperty("retraction_amount", "value")
        if retract_amount < 2.0:
            quick_purge_amount = retract_amount + 5
        else:
            quick_purge_amount = retract_amount * 2
        unload_distance = self.getSettingValueByKey("unload_distance")
        quick_purge = self.getSettingValueByKey("unload_quick_purge")
        lines = data[len(data) - 1].split("\n")
        for index, line in enumerate(lines):
            # Unload the filament just before the hot end turns off.
            if line.startswith("M104") and "S0" in line:
                filament_str = "M83 ; [Unload] Relative extrusion\nM400 ; Complete all moves\n"
                if quick_purge:
                    filament_str += f"G1 F{quick_purge_speed} E{quick_purge_amount} ; Quick Purge before unload\n"
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
        retract_enabled = self.extruder[0].getProperty("retraction_enable", "value")
        if not retract_enabled:
            return
        adjust_amt = self.getSettingValueByKey("adjust_e_loc_to")
        lines = data[1].split("\n")
        lines.reverse()
        if self.curaApp.getProperty("machine_firmware_retract", "value"):
            search_pattern = "G10"
        else:
            search_pattern = "G1 F(\d*) E-(\d.*)"
        for index, line in enumerate(lines):
            if re.search(search_pattern, line):
                lines[index] = re.sub(search_pattern, f"G92 E{adjust_amt}", line)
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