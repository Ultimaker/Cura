# August 2024 - Designed by: GregValiant (Greg Foresi).  Straightened out by: Hellaholic
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

import math
from ..Script import Script
from UM.Application import Application
from UM.Message import Message
import re
from UM.Logger import Logger
from enum import Enum


class Location(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    REAR = "rear"
    FRONT = "front"


class Position(tuple, Enum):
    LEFT_FRONT = ("left", "front")
    RIGHT_FRONT = ("right", "front")
    LEFT_REAR = ("left", "rear")
    RIGHT_REAR = ("right", "rear")


class PurgeLinesAndUnload(Script):

    def __init__(self):
        super().__init__()
        self.global_stack = Application.getInstance().getGlobalContainerStack()
        self.extruder = self.global_stack.extruderList
        self.end_purge_location = None
        self.speed_travel = None
        # This will be True when there are more than 4 'machine_disallowed_areas'
        self.show_warning = False
        self.disallowed_areas = self.global_stack.getProperty("machine_disallowed_areas", "value")
        self.extruder = self.global_stack.extruderList
        self.extruder_count = self.global_stack.getProperty("machine_extruder_count", "value")
        self.bed_shape = self.global_stack.getProperty("machine_shape", "value")
        self.origin_at_center = self.global_stack.getProperty("machine_center_is_zero", "value")
        self.machine_width = self.global_stack.getProperty("machine_width", "value")
        self.machine_depth = self.global_stack.getProperty("machine_depth", "value")
        self.machine_left = 1.0
        self.machine_right = self.machine_width - 1.0
        self.machine_front = 1.0
        self.machine_back = self.machine_depth - 1.0
        self.start_x = None
        self.start_y = None

    def initialize(self) -> None:
        super().initialize()
        # Get the StartUp Gcode from Cura and attempt to catch if it contains purge lines.  Message the user if an extrusion is in the startup.
        startup_gcode = self.global_stack.getProperty("machine_start_gcode", "value")
        start_lines = startup_gcode.splitlines()
        for line in start_lines:
            if "G1" in line and " E" in line and (" X" in line or " Y" in line):
                Message(title="[Purge Lines and Unload]",
                        text="It appears that there are 'purge lines' in the StartUp Gcode. Using the 'Add Purge Lines' function of this script will comment them out.").show()
                break
        # 'is_rectangular' is used to disable half-length purge lines for elliptic beds.
        self._instance.setProperty("is_rectangular", "value", True if self.global_stack.getProperty("machine_shape", "value") == "rectangular" else False)
        self._instance.setProperty("move_to_prime_tower", "value", True if self.global_stack.getProperty("machine_extruder_count", "value") > 1 else False)
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
                        "left": "On left edge (Xmin)",
                        "right": "On right edge (Xmax)",
                        "front": "On front edge (Ymin)",
                        "rear": "On back edge (Ymax)"},
                    "default_value": "left",
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
                "border_distance":
                {
                    "label": "    Border Distance",
                    "description": "This is the distance from the build plate edge to the first purge line. '0' works for most printers but you might want the lines further inboard.  The allowable range is -12 to 12.  ⚠️ Negative numbers are allowed for printers that have 'Disallowed Areas'.  You must use due caution when using a negative value.",
                    "type": "int",
                    "unit": "mm  ",
                    "default_value": 0,
                    "minimum_value": -12,
                    "maximum_value": 12,
                    "enabled": "add_purge_lines"
                },
                "prime_blob_enable":
                {
                    "label": "    Start with Prime Blob️​",
                    "description": "Enable a stationary purge before starting the purge lines.  Available only when purge line location is 'left' or 'front'",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "add_purge_lines and purge_line_location in ['front', 'left']"
                },
                "prime_blob_distance":
                {
                    "label": "        Blob Distance️​",
                    "description": "How many mm's of filament should be extruded for the blob.",
                    "type": "int",
                    "default_value": 0,
                    "unit": "mm  ",
                    "enabled": "add_purge_lines and prime_blob_enable and purge_line_location in ['front', 'left']"
                },
                "prime_blob_loc_x":
                {
                    "label": "        Blob Location X",
                    "description": "The 'X' position to put the prime blob. 'Origin at Center' printers might require a negative value here.  Keep in mind that purge lines always start in the left front, or the right rear.  Pay attention or the nozzle can sit down into the prime blob.",
                    "type": "int",
                    "default_value": 0,
                    "unit": "mm  ",
                    "enabled": "add_purge_lines and prime_blob_enable and purge_line_location in ['front', 'left']"
                },
                "prime_blob_loc_y":
                {
                    "label": "        Blob location Y",
                    "description": "The 'Y' position to put the prime blob. 'Origin at Center' printers might require a negative value here.  Keep in mind that purge lines always start in the left front, or the right rear.  Pay attention or the nozzle can sit down into the prime blob.",
                    "type": "int",
                    "default_value": 0,
                    "unit": "mm  ",
                    "enabled": "add_purge_lines and prime_blob_enable and purge_line_location in ['front', 'left']"
                },
                "move_to_start":
                {
                    "label": "Circle around to layer start  ⚠️​",
                    "description": "Depending on where the 'Layer Start X' and 'Layer Start Y' are for the print, the opening travel move can pass across the print area and leave a string there.  This option will generate an orthogonal path that moves the nozzle around the edges of the build plate and then comes in to the Start Point.  || ⚠️​ || The nozzle can drop to Z0.0 and touch the build plate at each stop in order to 'nail down the string'.  The nozzle always raises after the touch-down.  It will not drag on the bed.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": true
                },
                "move_to_start_min_z":
                {
                    "label": "    Minimum Z height ⚠️​",
                    "description": "When moving to the start position, the nozzle can touch down on the build plate at each stop (Z = 0.0).  That will stick the string to the build plate at each direction change so it doesn't pull across the print area.  Some printers may not respond well to Z=0.0.  You may set a minimum Z height here (min is 0.0 and max is 0.50).  The string must stick or it defeats the purpose of moving around the periphery.",
                    "type": "float",
                    "default_value": 0.0,
                    "minimum_value": 0.0,
                    "maximum_value": 0.5,
                    "enabled": "move_to_start"
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
                    "description": "When printing something fine that has a lot of retractions in a short space (like lettering or spires) right before the unload, the filament can get hung up in the hot end and unload can fail.  A quick purge will soften the end of the filament so it will retract correctly.  This 'quick purge' will take place at the last position of the nozzle.",
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
        # The function also retrieves extruder settings used later in the script
        # 't0_has_offsets' is used to exit 'Add Purge Lines' and 'Circle around...' because the script is not compatible with machines with the right nozzle as the primary nozzle.
        self.t0_has_offsets = False
        self.init_ext_nr = self._get_initial_tool()
        # Adjust the usable size of the bed per any 'disallowed areas'
        self._get_build_plate_extents()
        # The start location changes according to which quadrant the nozzle is in at the beginning
        self.end_purge_location = self._get_real_start_point(data[1])
        self.border_distance = self.getSettingValueByKey("border_distance")
        self.prime_blob_enable = self.getSettingValueByKey("prime_blob_enable")
        if self.prime_blob_enable:
            self.prime_blob_distance = self.getSettingValueByKey("prime_blob_distance")
        else:
            self.prime_blob_distance = 0
        # Set the minimum Z to stick the string to the build plate when Move to Start is selected.
        self.touchdown_z = self.getSettingValueByKey("move_to_start_min_z")
        
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
                msg_text = ("The printer has ( " + str(len(self.disallowed_areas))
                            + " ) 'disallowed areas'.  That can cause the area available for the purge lines to be small.\nOpen the Gcode file for preview in Cura and check the purge line location to insure it is acceptable.")
            else:
                msg_text = "Open the Gcode file for preview in Cura.  Make sure the 'Purge Lines' don't run underneath something else and are acceptable."
            Message(title="[Purge Lines and Unload]", text=msg_text).show()
        return data

    def _get_real_start_point(self, first_section: str) -> tuple:
        last_x, last_y = 0.0, 0.0
        start_quadrant = Position.LEFT_FRONT

        for line in first_section.split("\n"):
            if line.startswith(";") and not line.startswith(";LAYER_COUNT") or not line:
                continue

            if line.startswith("G28"):
                last_x, last_y = 0.0, 0.0
            elif line[:3] in {"G0 ", "G1 "}:
                last_x = self.getValue(line, "X") if " X" in line else last_x
                last_y = self.getValue(line, "Y") if " Y" in line else last_y
            elif "LAYER_COUNT" in line:
                break

        midpoint_x, midpoint_y = (0.0, 0.0) if self.origin_at_center else (
            self.machine_width / 2, self.machine_depth / 2)

        if last_x <= midpoint_x and last_y <= midpoint_y:
            start_quadrant = Position.LEFT_FRONT
        elif last_x > midpoint_x and last_y <= midpoint_y:
            start_quadrant = Position.RIGHT_FRONT
        elif last_x > midpoint_x and last_y > midpoint_y:
            start_quadrant = Position.RIGHT_REAR
        elif last_x <= midpoint_x and last_y > midpoint_y:
            start_quadrant = Position.LEFT_REAR

        return start_quadrant

    """
    For some multi-extruder printers.
    Takes into account a 'Move to Prime Tower' if there is one and adds orthogonal travel moves to get there.
    'Move to Prime Tower' does not require that the prime tower is enabled,
    only that 'machine_extruder_start_position_?' is in the definition file.
    """

    def _move_to_prime_tower(self, first_section: str) -> str:
        if self.extruder_count == 1:
            return first_section
        adjustment_lines = ""
        move_to_prime_present = False
        prime_tower_x = self.global_stack.getProperty("prime_tower_position_x", "value")
        prime_tower_y = self.global_stack.getProperty("prime_tower_position_y", "value")
        prime_tower_loc = self._prime_tower_quadrant(prime_tower_x, prime_tower_y)
        # Shortstop an error if Start Location comes through as None
        if self.end_purge_location is None:
            self.end_purge_location = Position.LEFT_FRONT
        if prime_tower_loc != self.end_purge_location:
            startup = first_section[1].split("\n")
            for index, line in enumerate(startup):
                if ";LAYER_COUNT:" in line:
                    try:
                        if startup[index + 1].startswith("G0"):
                            prime_move = startup[index + 1] + " ; Move to Prime Tower"
                            adjustment_lines = self._move_to_location("Prime Tower", prime_tower_loc)
                            startup[index + 1] = adjustment_lines + prime_move + "\n;---------------------[End of Prime Tower moves]\n" + startup[index]
                            startup.pop(index)
                            first_section[1] = "\n".join(startup)
                            move_to_prime_present = True
                    except IndexError:
                        pass
        # The start_location changes to the prime tower location in case 'Move to Start' is enabled.
        if move_to_prime_present:
            self.end_purge_location = prime_tower_loc
        return first_section

    # Determine the quadrant that the prime tower rests in so the orthogonal moves can be calculated
    def _prime_tower_quadrant(self, prime_tower_x: float, prime_tower_y: float) -> tuple:
        midpoint_x, midpoint_y = (0.0, 0.0) if self.origin_at_center else (
            self.machine_width / 2, self.machine_depth / 2)

        if prime_tower_x < midpoint_x and prime_tower_y < midpoint_y:
            return Position.LEFT_FRONT
        elif prime_tower_x > midpoint_x and prime_tower_y < midpoint_y:
            return Position.RIGHT_FRONT
        elif prime_tower_x > midpoint_x and prime_tower_y > midpoint_y:
            return Position.RIGHT_REAR
        elif prime_tower_x < midpoint_x and prime_tower_y > midpoint_y:
            return Position.LEFT_REAR
        else:
            return Position.LEFT_FRONT  # return Default in case of no match

    def _move_to_location(self, location_name: str, location: tuple) -> str:
        """
        Compare the input tuple (B) with the end purge location (A) and describe the move from A to B.
        Parameters:
            location_name (str): A descriptive name for the target location.
            location (tuple): The target tuple (e.g., ("right", "front")).
        Returns:
            str: G-code for the move from A to B or an empty string if no move is required.
        """
        # Validate input
        if len(self.end_purge_location) != 2 or len(location) != 2:
            raise ValueError("Both locations must be tuples of length 2.")

        # Extract components
        start_side, start_depth = self.end_purge_location
        target_side, target_depth = location
        # Start of the moves and a comment to highlight the move
        moves = [f";MESH:NONMESH---------[Circle around to {location_name}]    Start from: {str(start_side)} {str(start_depth)}    Go to: {target_side} {target_depth}\nG0 F600 Z2 ; Move up\n"]

        # Helper function to add G-code for moves
        def add_move(axis: str, position: float) -> None:
            moves.append(
                f"G0 F{self.speed_travel} {axis}{position} ; Start move\n"
                f"G0 F600 Z{self.touchdown_z} ; Nail down the string\n"
                f"G0 F600 Z2 ; Move up\n"
            )

        # Move to a corner
        if start_side == Location.LEFT:
            moves.append(f"G0 F{self.speed_travel} X{self.machine_left + 6} ; Init move\n")
        elif start_side == Location.RIGHT:
            moves.append(f"G0 F{self.speed_travel} X{self.machine_right - 6} ; Init move\n")
        if start_depth == Location.FRONT:
            add_move("Y", self.machine_front + 6)
        elif start_depth == Location.REAR:
            add_move("Y", self.machine_back - 6)
        # Compare sides
        if start_side != target_side:
            if target_side == Location.RIGHT:
                add_move("X", self.machine_right)
            else:
                add_move("X", self.machine_left)
        # Compare positions
        if start_depth != target_depth:
            if target_depth == Location.REAR:
                add_move("Y", self.machine_back)
            else:
                add_move("Y", self.machine_front)
        if len(moves) == 1:
            moves.append(f"G0 F{self.speed_travel} Y{self.start_y} ; Move to start Y\n")
        # Combine moves into a single G-code string and return
        return "".join(moves)

    def _get_build_plate_extents(self):
        """
            Machine disallowed areas can be ordered at the whim of the definition author and cannot be counted on when parsed
            This determines a simple rectangle that will be available for the purge lines.  For some machines (Ex: UM3) it can be a small rectangle.
            If there are "extruder offsets" then use them to adjust the 'machine_right' and 'machine_back' independent of any disallowed areas.
        """
        if self.bed_shape == "rectangular":
            if self.disallowed_areas:
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
                        if mid_x > x > left_x:
                            left_x = x
                        if mid_x < x < right_x:
                            right_x = x
                        y = corner[1]
                        if mid_y < y < front_y:
                            front_y = y
                        if mid_y > y > back_y:
                            back_y = y
                if self.origin_at_center:
                    self.machine_left = round(left_x, 2)
                    self.machine_right = round(right_x, 2)
                    self.machine_front = round(front_y, 2)
                    self.machine_back = round(back_y, 2)
                else:
                    self.machine_left = round(left_x + self.machine_width / 2, 2)
                    self.machine_right = round(right_x + self.machine_width / 2, 2)
                    self.machine_front = round((self.machine_depth / 2) - front_y, 2)
                    self.machine_back = round((self.machine_depth / 2) - back_y, 2)
            else:
                if self.origin_at_center:
                    self.machine_left = round(-(self.machine_width / 2), 2)
                    self.machine_right = round((self.machine_width / 2) - self.nozzle_offset_x, 2)
                    self.machine_front = round(-(self.machine_depth / 2) + self.nozzle_offset_y, 2)
                    self.machine_back = round((self.machine_depth / 2) - self.nozzle_offset_y, 2)
                else:
                    self.machine_left = 0
                    self.machine_right = self.machine_width - self.nozzle_offset_x
                    if self.nozzle_offset_y >= 0:
                        self.machine_front = 0
                        self.machine_back = self.machine_depth - self.nozzle_offset_y
                    elif self.nozzle_offset_y < 0:
                        self.machine_front = abs(self.nozzle_offset_y)
                        self.machine_back = self.machine_depth
        return

    # Add Purge Lines to the user defined position on the build plate
    def _add_purge_lines(self, data: str):
        if self.t0_has_offsets:
            data[0] += ";  [Purge Lines and Unload]  'Add Purge Lines' did not run because the assumed primary nozzle (T0) has tool offsets.\n"
            Message(title = "[Purge Lines and Unload]", text = "'Add Purge Lines' did not run because the assumed primary nozzle (T0) has tool offsets").show()
            return data

        def calculate_purge_volume(line_width, purge_length, volume_per_mm):
            return round((line_width * 0.3 * purge_length) * 1.25 / volume_per_mm, 5)
        
        def adjust_for_prime_blob_gcode(retract_speed, retract_distance):
            """Generates G-code lines for prime blob adjustment."""
            gcode_lines = [
                f"G1 F{retract_speed} E{retract_distance} ; Unretract",
                "G92 E0 ; Reset extruder\n"
            ]
            return "\n".join(gcode_lines)

        purge_location = self.getSettingValueByKey("purge_line_location")
        purge_extrusion_full = True if self.getSettingValueByKey("purge_line_length") == "purge_full" else False
        purge_str = ";TYPE:CUSTOM----------[Purge Lines]\nG0 F600 Z2 ; Move up\nG92 E0 ; Reset extruder\n"
        purge_str += self._get_blob_code()
        # Normal cartesian printer with origin at the left front corner
        if self.bed_shape == "rectangular" and not self.origin_at_center:
            if purge_location == Location.LEFT:
                purge_len = int(self.machine_back - 20) if purge_extrusion_full else int((self.machine_back - self.machine_front) / 2)
                y_stop = int(self.machine_back - 10) if purge_extrusion_full else int(self.machine_depth / 2)
                purge_volume = calculate_purge_volume(self.init_line_width, purge_len, self.mm3_per_mm)
                purge_str = purge_str.replace("Lines", "Lines at MinX")
                # Travel to the purge start
                purge_str += f"G0 F{self.speed_travel} X{self.machine_left + self.border_distance} Y{self.machine_front + 10} ; Move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                if self.prime_blob_enable:
                    purge_str += adjust_for_prime_blob_gcode(self.retract_speed, self.retract_dist)
                # Purge two lines
                purge_str += f"G1 F{self.print_speed} X{self.machine_left + self.border_distance} Y{y_stop} E{purge_volume} ; First line\n"
                purge_str += f"G0 X{self.machine_left + 3 + self.border_distance} Y{y_stop} ; Move over\n"
                purge_str += f"G1 F{self.print_speed} X{self.machine_left + 3 + self.border_distance} Y{self.machine_front + 10} E{round(purge_volume * 2, 5)} ; Second line\n"
                # Retract if enabled
                purge_str += f"G1 F{int(self.retract_speed)} E{round(purge_volume * 2 - self.retract_dist, 5)} ; Retract\n" if self.retraction_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                # Wipe
                purge_str += f"G0 F{self.print_speed} X{self.machine_left + 3 + self.border_distance} Y{self.machine_front + 20} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 X{self.machine_left + 3 + self.border_distance} Y{self.machine_front + 35} ; Wipe\n"
                self.end_purge_location = Position.LEFT_FRONT
            elif purge_location == Location.RIGHT:
                purge_len = int(self.machine_depth - 20) if purge_extrusion_full else int((self.machine_back - self.machine_front) / 2)
                y_stop = int(self.machine_front + 10) if purge_extrusion_full else int(self.machine_depth / 2)
                purge_volume = calculate_purge_volume(self.init_line_width, purge_len, self.mm3_per_mm)
                purge_str = purge_str.replace("Lines", "Lines at MaxX")
                # Travel to the purge start
                purge_str += f"G0 F{self.speed_travel} X{self.machine_right - self.border_distance} ; Move\nG0 Y{self.machine_back - 10} ; Move\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                if self.prime_blob_enable:
                    purge_str += adjust_for_prime_blob_gcode(self.retract_speed, self.retract_dist)
                # Purge two lines
                purge_str += f"G1 F{self.print_speed} X{self.machine_right - self.border_distance} Y{y_stop} E{purge_volume} ; First line\n"
                purge_str += f"G0 X{self.machine_right - 3 - self.border_distance} Y{y_stop} ; Move over\n"
                purge_str += f"G1 F{self.print_speed} X{self.machine_right - 3 - self.border_distance} Y{self.machine_back - 10} E{purge_volume * 2} ; Second line\n"
                # Retract if enabled
                purge_str += f"G1 F{int(self.retract_speed)} E{round(purge_volume * 2 - self.retract_dist, 5)} ; Retract\n" if self.retraction_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                # Wipe
                purge_str += f"G0 F{self.print_speed} X{self.machine_right - 3 - self.border_distance} Y{self.machine_back - 20} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 X{self.machine_right - 3 - self.border_distance} Y{self.machine_back - 35} ; Wipe\n"
                self.end_purge_location = Position.RIGHT_REAR
            elif purge_location == Location.FRONT:
                purge_len = int(self.machine_width) - self.nozzle_offset_x - 20 if purge_extrusion_full else int(
                    (self.machine_right - self.machine_left) / 2)
                x_stop = int(self.machine_right - 10) if purge_extrusion_full else int(self.machine_width / 2)
                purge_volume = calculate_purge_volume(self.init_line_width, purge_len, self.mm3_per_mm)
                purge_str = purge_str.replace("Lines", "Lines at MinY")
                # Travel to the purge start
                purge_str += f"G0 F{self.speed_travel} X{self.machine_left + 10} Y{self.machine_front + self.border_distance} ; Move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                if self.prime_blob_enable:
                    purge_str += adjust_for_prime_blob_gcode(self.retract_speed, self.retract_dist)
                # Purge two lines
                purge_str += f"G1 F{self.print_speed} X{x_stop} Y{self.machine_front + self.border_distance} E{purge_volume} ; First line\n"
                purge_str += f"G0 X{x_stop} Y{self.machine_front + 3 + self.border_distance} ; Move over\n"
                purge_str += f"G1 F{self.print_speed} X{self.machine_left + 10} Y{self.machine_front + 3 + self.border_distance} E{purge_volume * 2} ; Second line\n"
                # Retract if enabled
                purge_str += f"G1 F{int(self.retract_speed)} E{round(purge_volume * 2 - self.retract_dist, 5)} ; Retract\n" if self.retraction_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                # Wipe
                purge_str += f"G0 F{self.print_speed} X{self.machine_left + 20} Y{self.machine_front + 3 + self.border_distance} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 X{self.machine_left + 35} Y{self.machine_front + 3 + self.border_distance} ; Wipe\n"
                self.end_purge_location = Position.LEFT_FRONT
            elif purge_location == Location.REAR:
                purge_len = int(self.machine_width - 20) if purge_extrusion_full else int(
                    (self.machine_right - self.machine_left) / 2)
                x_stop = int(self.machine_left + 10) if purge_extrusion_full else int(self.machine_width / 2)
                purge_volume = calculate_purge_volume(self.init_line_width, purge_len, self.mm3_per_mm)
                purge_str = purge_str.replace("Lines", "Lines at MaxY")
                # Travel to the purge start
                purge_str += f"G0 F{self.speed_travel} Y{self.machine_back - self.border_distance} ; Ortho Move to back\n"
                purge_str += f"G0 X{self.machine_right - 10} ; Ortho move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                if self.prime_blob_enable:
                    purge_str += adjust_for_prime_blob_gcode(self.retract_speed, self.retract_dist)
                # Purge two lines
                purge_str += f"G1 F{self.print_speed} X{x_stop} Y{self.machine_back - self.border_distance} E{purge_volume} ; First line\n"
                purge_str += f"G0 X{x_stop} Y{self.machine_back - 3 - self.border_distance} ; Move over\n"
                purge_str += f"G1 F{self.print_speed} X{self.machine_right - 10} Y{self.machine_back - 3 - self.border_distance} E{purge_volume * 2} ; Second line\n"
                # Retract if enabled
                purge_str += f"G1 F{int(self.retract_speed)} E{round(purge_volume * 2 - self.retract_dist, 5)} ; Retract\n" if self.retraction_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait 1 second\n"
                # Wipe
                purge_str += f"G0 F{self.print_speed} X{self.machine_right - 20} Y{self.machine_back - 3 - self.border_distance} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 X{self.machine_right - 35} Y{self.machine_back - 3 - self.border_distance} ; Wipe\n"
                self.end_purge_location = Position.RIGHT_REAR
        # Some cartesian printers (BIBO, Weedo, MethodX, etc.) are Origin at Center
        elif self.bed_shape == "rectangular" and self.origin_at_center:
            if purge_location == Location.LEFT:
                purge_len = int(self.machine_back - self.machine_front - 20) if purge_extrusion_full else abs(
                    int(self.machine_front - 10))
                y_stop = int(self.machine_back - 10) if purge_extrusion_full else 0
                purge_volume = calculate_purge_volume(self.init_line_width, purge_len, self.mm3_per_mm)
                # Travel to the purge start
                purge_str += f"G0 F{self.speed_travel} X{self.machine_left + self.border_distance} Y{self.machine_front + 10} ; Move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                if self.prime_blob_enable:
                    purge_str += adjust_for_prime_blob_gcode(self.retract_speed, self.retract_dist)
                # Purge two lines
                purge_str += f"G1 F{self.print_speed} X{self.machine_left + self.border_distance} Y{y_stop} E{purge_volume} ; First line\n"
                purge_str += f"G0 X{self.machine_left + 3 + self.border_distance} Y{y_stop} ; Move over\n"
                purge_str += f"G1 F{self.print_speed} X{self.machine_left + 3 + self.border_distance} Y{self.machine_front + 10} E{round(purge_volume * 2, 5)} ; Second line\n"
                # Retract if enabled
                purge_str += f"G1 F{int(self.retract_speed)} E{round(purge_volume * 2 - self.retract_dist, 5)} ; Retract\n" if self.retraction_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                # Wipe
                purge_str += f"G0 F{self.print_speed} X{self.machine_left + 3 + self.border_distance} Y{self.machine_front + 20} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 X{self.machine_left + 3 + self.border_distance} Y{self.machine_front + 35} ; Wipe\n"
                self.end_purge_location = Position.LEFT_FRONT
            elif purge_location == Location.RIGHT:
                purge_len = int(self.machine_back - 20) if purge_extrusion_full else int(
                    (self.machine_back - self.machine_front) / 2)
                y_stop = int(self.machine_front + 10) if purge_extrusion_full else 0
                purge_volume = calculate_purge_volume(self.init_line_width, purge_len, self.mm3_per_mm)
                # Travel to the purge start
                purge_str += f"G0 F{self.speed_travel} X{self.machine_right - self.border_distance} Z2 ; Move\nG0 Y{self.machine_back - 10} Z2 ; Move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                if self.prime_blob_enable:
                    purge_str += adjust_for_prime_blob_gcode(self.retract_speed, self.retract_dist)
                # Purge two lines
                purge_str += f"G1 F{self.print_speed} X{self.machine_right - self.border_distance} Y{y_stop} E{purge_volume} ; First line\n"
                purge_str += f"G0 X{self.machine_right - 3 - self.border_distance} Y{y_stop} ; Move over\n"
                purge_str += f"G1 F{self.print_speed} X{self.machine_right - 3 - self.border_distance} Y{self.machine_back - 10} E{purge_volume * 2} ; Second line\n"
                # Retract if enabled
                purge_str += f"G1 F{int(self.retract_speed)} E{round(purge_volume * 2 - self.retract_dist, 5)} ; Retract\n" if self.retraction_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                # Wipe
                purge_str += f"G0 F{self.print_speed} X{self.machine_right - 3 - self.border_distance} Y{self.machine_back - 20} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 X{self.machine_right - 3 - self.border_distance} Y{self.machine_back - 35} ; Wipe\n"
                self.end_purge_location = Position.RIGHT_REAR
            elif purge_location == Location.FRONT:
                purge_len = int(self.machine_right - self.machine_left - 20) if purge_extrusion_full else int(
                    (self.machine_right - self.machine_left) / 2)
                x_stop = int(self.machine_right - 10) if purge_extrusion_full else 0
                purge_volume = calculate_purge_volume(self.init_line_width, purge_len, self.mm3_per_mm)
                # Travel to the purge start
                purge_str += f"G0 F{self.speed_travel} X{self.machine_left + 10} Z2 ; Move\nG0 Y{self.machine_front + self.border_distance} Z2 ; Move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                if self.prime_blob_enable:
                    purge_str += adjust_for_prime_blob_gcode(self.retract_speed, self.retract_dist)
                # Purge two lines
                purge_str += f"G1 F{self.print_speed} X{x_stop} Y{self.machine_front + self.border_distance} E{purge_volume} ; First line\n"
                purge_str += f"G0 X{x_stop} Y{self.machine_front + 3 + self.border_distance} ; Move over\n"
                purge_str += f"G1 F{self.print_speed} X{self.machine_left + 10} Y{self.machine_front + 3 + self.border_distance} E{purge_volume * 2} ; Second line\n"
                # Retract if enabled
                purge_str += f"G1 F{int(self.retract_speed)} E{round(purge_volume * 2 - self.retract_dist, 5)} ; Retract\n" if self.retraction_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                # Wipe
                purge_str += f"G0 F{self.print_speed} X{self.machine_left + 20} Y{self.machine_front + 3 + self.border_distance} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 X{self.machine_left + 35} Y{self.machine_front + 3 + self.border_distance} ; Wipe\n"
                self.end_purge_location = Position.LEFT_FRONT
            elif purge_location == Location.REAR:
                purge_len = int(self.machine_right - self.machine_left - 20) if purge_extrusion_full else abs(
                    int(self.machine_right - 10))
                x_stop = int(self.machine_left + 10) if purge_extrusion_full else 0
                purge_volume = calculate_purge_volume(self.init_line_width, purge_len, self.mm3_per_mm)
                # Travel to the purge start
                purge_str += f"G0 F{self.speed_travel} Y{self.machine_back - self.border_distance} Z2; Ortho Move to back\n"
                purge_str += f"G0 X{self.machine_right - 10} Z2 ; Ortho Move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                if self.prime_blob_enable:
                    purge_str += adjust_for_prime_blob_gcode(self.retract_speed, self.retract_dist)
                # Purge two lines
                purge_str += f"G1 F{self.print_speed} X{x_stop} Y{self.machine_back - self.border_distance} E{purge_volume} ; First line\n"
                purge_str += f"G0 X{x_stop} Y{self.machine_back - 3 - self.border_distance} ; Move over\n"
                purge_str += f"G1 F{self.print_speed} X{self.machine_right - 10} Y{self.machine_back - 3 - self.border_distance} E{purge_volume * 2} ; Second line\n"
                # Retract if enabled
                purge_str += f"G1 F{int(self.retract_speed)} E{round(purge_volume * 2 - self.retract_dist, 5)} ; Retract\n" if self.retraction_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                # Wipe
                purge_str += f"G0 F{self.print_speed} X{self.machine_right - 20} Y{self.machine_back - 3 - self.border_distance} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 X{self.machine_right - 35} Y{self.machine_back - 3 - self.border_distance} ; Wipe\n"
                self.end_purge_location = Position.RIGHT_REAR
        # Elliptic printers with Origin at Center
        elif self.bed_shape == "elliptic":
            if purge_location in [Location.LEFT, Location.RIGHT]:
                radius_1 = round((self.machine_width / 2) - 1, 2)
            else:  # For purge_location in [Location.FRONT, Location.REAR]
                radius_1 = round((self.machine_depth / 2) - 1, 2)
            purge_len = int(radius_1) * math.pi / 4
            purge_volume = calculate_purge_volume(self.init_line_width, purge_len, self.mm3_per_mm)
            if purge_location == Location.LEFT:
                # Travel to the purge start
                purge_str += f"G0 F{self.speed_travel} X-{round(radius_1 * .707, 2)} Y-{round(radius_1 * .707, 2)} ; Travel\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                # Purge two arcs
                purge_str += f"G2 F{self.print_speed} X-{round(radius_1 * .707, 2)} Y{round(radius_1 * .707, 2)} I{round(radius_1 * .707, 2)} J{round(radius_1 * .707, 2)} E{purge_volume} ; First Arc\n"
                purge_str += f"G0 X-{round((radius_1 - 3) * .707, 2)} Y{round((radius_1 - 3) * .707, 2)} ; Move Over\n"
                purge_str += f"G3 F{self.print_speed} X-{round((radius_1 - 3) * .707, 2)} Y-{round((radius_1 - 3) * .707, 2)} I{round((radius_1 - 3) * .707, 2)} J-{round((radius_1 - 3) * .707, 2)} E{purge_volume * 2} ; Second Arc\n"
                purge_str += f"G1 X-{round((radius_1 - 3) * .707 - 25, 2)} E{round(purge_volume * 2 + 1, 5)} ; Move Over\n"
                # Retract if enabled
                purge_str += f"G1 F{int(self.retract_speed)} E{round((purge_volume * 2 + 1) - self.retract_dist, 5)} ; Retract\n" if self.retraction_enable else ""
                purge_str += "G0 F600 Z5 ; Move Up\nG4 S1 ; Wait 1 Second\n"
                # Wipe
                purge_str += f"G0 F{self.print_speed} X-{round((radius_1 - 3) * .707 - 15, 2)} Z0.3 ; Slide Over\n"
                purge_str += f"G0 F{self.print_speed} X-{round((radius_1 - 3) * .707, 2)} ; Wipe\n"
                self.end_purge_location = Position.LEFT_FRONT
            elif purge_location == Location.RIGHT:
                # Travel to the purge start
                purge_str += f"G0 F{self.speed_travel} X{round(radius_1 * .707, 2)} Y-{round(radius_1 * .707, 2)} ; Travel\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                # Purge two arcs
                purge_str += f"G3 F{self.print_speed} X{round(radius_1 * .707, 2)} Y{round(radius_1 * .707, 2)} I-{round(radius_1 * .707, 2)} J{round(radius_1 * .707, 2)} E{purge_volume} ; First Arc\n"
                purge_str += f"G0 X{round((radius_1 - 3) * .707, 2)} Y{round((radius_1 - 3) * .707, 2)} ; Move Over\n"
                purge_str += f"G2 F{self.print_speed} X{round((radius_1 - 3) * .707, 2)} Y-{round((radius_1 - 3) * .707, 2)} I-{round((radius_1 - 3) * .707, 2)} J-{round((radius_1 - 3) * .707, 2)} E{purge_volume * 2} ; Second Arc\n"
                purge_str += f"G1 X{round((radius_1 - 3) * .707 - 25, 2)} E{round(purge_volume * 2 + 1, 5)} ; Move Over\n"
                # Retract if enabled
                purge_str += f"G1 F{int(self.retract_speed)} E{round((purge_volume * 2 + 1) - self.retract_dist, 5)} ; Retract\n" if self.retraction_enable else ""
                purge_str += "G0 F600 Z5 ; Move Up\nG4 S1 ; Wait 1 Second\n"
                # Wipe
                purge_str += f"G0 F{self.print_speed} X{round((radius_1 - 3) * .707 - 15, 2)} Z0.3 ; Slide Over\n"
                purge_str += f"G0 F{self.print_speed} X{round((radius_1 - 3) * .707, 2)} ; Wipe\n"
                self.end_purge_location = Position.RIGHT_REAR
            elif purge_location == Location.FRONT:
                # Travel to the purge start
                purge_str += f"G0 F{self.speed_travel} X-{round(radius_1 * .707, 2)} Y-{round(radius_1 * .707, 2)} ; Travel\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                # Purge two arcs
                purge_str += f"G3 F{self.print_speed} X{round(radius_1 * .707, 2)} Y-{round(radius_1 * .707, 2)} I{round(radius_1 * .707, 2)} J{round(radius_1 * .707, 2)} E{purge_volume} ; First Arc\n"
                purge_str += f"G0 X{round((radius_1 - 3) * .707, 2)} Y-{round((radius_1 - 3) * .707, 2)} ; Move Over\n"
                purge_str += f"G2 F{self.print_speed} X-{round((radius_1 - 3) * .707, 2)} Y-{round((radius_1 - 3) * .707, 2)} I-{round((radius_1 - 3) * .707, 2)} J{round((radius_1 - 3) * .707, 2)} E{purge_volume * 2} ; Second Arc\n"
                purge_str += f"G1 Y-{round((radius_1 - 3) * .707 - 25, 2)} E{round(purge_volume * 2 + 1, 5)} ; Move Over\n"
                # Retract if enabled
                purge_str += f"G1 F{int(self.retract_speed)} E{round((purge_volume * 2 + 1) - self.retract_dist, 5)} ; Retract\n" if self.retraction_enable else ""
                purge_str += "G0 F600 Z5 ; Move Up\nG4 S1 ; Wait 1 Second\n"
                # Wipe
                purge_str += f"G0 F{self.print_speed} Y-{round((radius_1 - 3) * .707 - 15, 2)} Z0.3 ; Slide Over\n"
                purge_str += f"G0 F{self.print_speed} Y-{round((radius_1 - 3) * .707, 2)} ; Wipe\n"
                self.end_purge_location = Position.LEFT_FRONT
            elif purge_location == Location.REAR:
                # Travel to the purge start
                purge_str += f"G0 F{self.speed_travel} X{round(radius_1 * .707, 2)} Y{round(radius_1 * .707, 2)} ; Travel\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                # Purge two arcs
                purge_str += f"G3 F{self.print_speed} X-{round(radius_1 * .707, 2)} Y{round(radius_1 * .707, 2)} I-{round(radius_1 * .707, 2)} J-{round(radius_1 * .707, 2)} E{purge_volume} ; First Arc\n"
                purge_str += f"G0 X-{round((radius_1 - 3) * .707, 2)} Y{round((radius_1 - 3) * .707, 2)} ; Move Over\n"
                purge_str += f"G2 F{self.print_speed} X{round((radius_1 - 3) * .707, 2)} Y{round((radius_1 - 3) * .707, 2)} I{round((radius_1 - 3) * .707, 2)} J-{round((radius_1 - 3) * .707, 2)} E{purge_volume * 2} ; Second Arc\n"
                purge_str += f"G1 Y{round((radius_1 - 3) * .707 - 25, 2)} E{round(purge_volume * 2 + 1, 5)} ; Move Over\n"
                # Retract if enabled
                purge_str += f"G1 F{int(self.retract_speed)} E{round((purge_volume * 2 + 1) - self.retract_dist, 5)} ; Retract\n" if self.retraction_enable else ""
                purge_str += "G0 F600 Z5\nG4 S1 ; Wait 1 Second\n"
                # Wipe
                purge_str += f"G0 F{self.print_speed} Y{round((radius_1 - 3) * .707 - 15, 2)} Z0.3 ; Slide Over\n"
                purge_str += f"G0 F{self.print_speed} Y{round((radius_1 - 3) * .707, 2)} ; Wipe\n"
                self.end_purge_location = Position.RIGHT_REAR

        # Common ending for purge_str
        purge_str += "G0 F600 Z2 ; Move Z\n;---------------------[End of Purge]"

        # Comment out any existing purge lines in data
        startup = data[1].split("\n")
        for index, line in enumerate(startup):
            if "G1" in line and " E" in line and (" X" in line or " Y" in line):
                next_line = index
                try:
                    while not startup[next_line].startswith("G92 E0"):
                        startup[next_line] = ";" + startup[next_line]
                        next_line += 1
                except IndexError:
                    break
        data[1] = "\n".join(startup)

        # Find the insertion location in data
        purge_str = self._format_string(purge_str)
        startup_section = data[1].split("\n")
        insert_index = len(startup_section) - 1
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
        return data

    # Travel moves around the bed periphery to keep strings from crossing the footprint of the model.
    def _move_to_start(self, data: str) -> str:
        if self.t0_has_offsets:
            data[0] += ";  [Purge Lines and Unload] 'Circle Around to Layer Start' did not run because the assumed primary nozzle (T0) has tool offsets.\n"
            Message(title = "[Purge Lines and Unload]", text = "'Circle Around to Layer Start' did not run because the assumed primary nozzle (T0) has tool offsets.").show()
            return data
        self.start_x = None
        self.start_y = None
        move_str = None
        layer = data[2].split("\n")
        for line in layer:
            if line.startswith("G0") and " X" in line and " Y" in line:
                self.start_x = self.getValue(line, "X")
                self.start_y = self.getValue(line, "Y")
                break
        self.start_x = self.start_x or 0
        self.start_y = self.start_y or 0
        if self.end_purge_location is None:
            self.end_purge_location = Position.LEFT_FRONT
        midpoint_x = self.machine_width / 2
        midpoint_y = self.machine_depth / 2
        if not self.origin_at_center:
            if float(self.start_x) <= float(midpoint_x):
                x_target = Location.LEFT
            else:
                x_target = Location.RIGHT
            if float(self.start_y) <= float(midpoint_y):
                y_target = Location.FRONT
            else:
                y_target = Location.REAR
        else:
            if float(self.start_x) <= 0:
                x_target = Location.LEFT
            else:
                x_target = Location.RIGHT
            if float(self.start_y) <= 0:
                y_target = Location.FRONT
            else:
                y_target = Location.REAR
        target_location = (x_target, y_target)
        if self.bed_shape == "rectangular":
            move_str = self._move_to_location("Layer Start", target_location)
        elif self.bed_shape == "elliptic" and self.origin_at_center:
            move_str = f";MESH:NONMESH---------[Travel to Layer Start]\nG0 F600 Z2 ; Move up\n"
            radius = self.machine_width / 2
            offset_sin = round(2 ** .5 / 2 * radius, 2)
            if target_location == Position.LEFT_FRONT:
                move_str += f"G0 F{self.speed_travel} X-{offset_sin} Z2 ; Move\nG0 Y-{offset_sin} Z2 ; Move to start\n"
            elif target_location == Position.LEFT_REAR:
                if self.end_purge_location == Position.LEFT_REAR:
                    move_str += f"G2 X0 Y{offset_sin} I{offset_sin} J{offset_sin} ; Move around to start\n"
                else:
                    move_str += f"G0 F{self.speed_travel} X-{offset_sin} Z2 ; Ortho move\nG0 Y{offset_sin} Z2 ; Ortho move\n"
            elif target_location == Position.RIGHT_FRONT:
                move_str += f"G0 F{self.speed_travel} X{offset_sin} Z2 ; Ortho move\nG0 Y-{offset_sin} Z2 ; Ortho move\n"
            elif target_location == Position.RIGHT_REAR:
                move_str += f"G0 F{self.speed_travel} X{offset_sin} Z2 ; Ortho move\nG0 Y{offset_sin} Z2 ; Ortho move\n"
        move_str += ";---------------------[End of layer start travels]"
        # Add the move_str to the end of the StartUp section and move 'LAYER_COUNT' to the end.
        startup = data[1].split("\n")
        move_str = self._format_string(move_str)
        if move_str.startswith("\n"):
            move_str = move_str[1:]
        startup.append(move_str)
        # Move the 'LAYER_COUNT' line so it's at the end of data[1]
        for index, line in enumerate(startup):
            if "LAYER_COUNT" in line:
                lay_count = startup.pop(index) + "\n"
                startup.append(lay_count)
                break

        data[1] = "\n".join(startup)
        # Remove any double-spaced lines
        data[1] = data[1].replace("\n\n", "\n")
        return data

    # Unloading a large amount of filament in a single command can trip the 'Overlong Extrusion' warning in some firmware.  Unloads longer than 150mm are split into individual 150mm segments.
    def _unload_filament(self, data: str) -> str:
        extrude_speed = 3000
        quick_purge_speed = round(float(self.nozzle_size) * 500)
        if self.material_diameter > 2: quick_purge_speed *= .38 # Adjustment for 2.85 filament
        retract_amount = self.extruder[0].getProperty("retraction_amount", "value")
        quick_purge_amount = retract_amount + 5 if retract_amount < 2.0 else retract_amount * 2
        unload_distance = self.getSettingValueByKey("unload_distance")
        quick_purge = self.getSettingValueByKey("unload_quick_purge")
        lines = data[-1].split("\n")
        for index, line in enumerate(lines):
            # Unload the filament just before the hot end turns off.
            if line.startswith("M104") and "S0" in line:
                filament_str = (
                    "M83 ; [Unload] Relative extrusion\n"
                    "M400 ; Complete all moves\n"
                )
                if quick_purge:
                    filament_str += f"G1 F{quick_purge_speed} E{quick_purge_amount} ; Quick Purge before unload\n"
                if unload_distance > 150:
                    filament_str += "".join(
                        f"G1 F{extrude_speed} E-150 ; Unload some\n"
                        for _ in range(unload_distance // 150)
                    )
                    remaining_unload = unload_distance % 150
                    if remaining_unload > 0:
                        filament_str += f"G1 F{extrude_speed} E-{remaining_unload} ; Unload the remainder\n"
                else:
                    filament_str += f"G1 F{extrude_speed} E-{unload_distance} ; Unload\n"
                filament_str += (
                    "M82 ; Absolute Extrusion\n"
                    "G92 E0 ; Reset Extruder\n"
                )
                lines[index] = filament_str + line
                break
        data[-1] = "\n".join(lines)
        return data

    # Make an adjustment to the starting E location so the skirt/brim/raft starts out when the nozzle starts out.
    def _adjust_starting_e(self, data: str) -> str:
        if not self.extruder[0].getProperty("retraction_enable", "value"):
            return data
        adjust_amount = self.getSettingValueByKey("adjust_e_loc_to")
        lines = data[1].split("\n")
        lines.reverse()
        if self.global_stack.getProperty("machine_firmware_retract", "value"):
            search_pattern = r"G10"
        else:
            search_pattern = r"G1 F(\d*) E-(\d.*)"
        for index, line in enumerate(lines):
            if re.search(search_pattern, line):
                lines[index] = re.sub(search_pattern, f"G92 E{adjust_amount}", line)
                lines.reverse()
                data[1] = "\n".join(lines)
                break
        return data

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
                temp_lines[temp_index] = temp_line.replace(temp_line.split(";")[0], temp_line.split(";")[0] + str(
                    " " * (gap_len - len(temp_line.split(";")[0]))), 1)
            # This formats lines that are commented out but contain additional comments Ex:  ;M420 ; leveling mesh
            elif temp_line.startswith(";") and ";" in temp_line[1:]:
                temp_lines[temp_index] = temp_line[1:].replace(temp_line[1:].split(";")[0],
                                                               ";" + temp_line[1:].split(";")[0] + str(" " * (
                                                                   gap_len - 1 - len(
                                                                        temp_line[1:].split(";")[0]))), 1)
        any_gcode_str = "\n".join(temp_lines)
        return any_gcode_str

    def _get_initial_tool(self) -> int:
        # Get the Initial Extruder
        num = Application.getInstance().getExtruderManager().getInitialExtruderNr()
        if num is None or num == -1:
            num = 0
        # If there is an extruder offset X then it will be used to adjust the "machine_right" and a Y offset will adjust the "machine_back"
        if self.extruder_count > 1 and bool(self.global_stack.getProperty("machine_use_extruder_offset_to_offset_coords", "value")):
            self.nozzle_offset_x = self.extruder[1].getProperty("machine_nozzle_offset_x", "value")
            self.nozzle_offset_y = self.extruder[1].getProperty("machine_nozzle_offset_y", "value")
        else:
            self.nozzle_offset_x = 0.0
            self.nozzle_offset_y = 0.0
        self.material_diameter = self.extruder[num].getProperty("material_diameter", "value")
        self.nozzle_size = self.extruder[num].getProperty("machine_nozzle_size", "value")
        self.init_line_width = self.extruder[num].getProperty("skirt_brim_line_width", "value")
        self.print_speed = round(self.extruder[num].getProperty("speed_print", "value") * 60 * .75)
        self.speed_travel = round(self.extruder[num].getProperty("speed_travel", "value") * 60)
        self.retract_dist = self.extruder[num].getProperty("retraction_amount", "value")
        self.retraction_enable = self.extruder[num].getProperty("retraction_enable", "value")
        self.retract_speed = self.extruder[num].getProperty("retraction_retract_speed", "value") * 60
        self.mm3_per_mm = (self.material_diameter / 2) ** 2 * math.pi
        # Don't add purge lines if 'T0' has offsets.
        t0_x_offset = self.extruder[0].getProperty("machine_nozzle_offset_x", "value")
        t0_y_offset = self.extruder[0].getProperty("machine_nozzle_offset_y", "value")
        if t0_x_offset or t0_y_offset:
            self.t0_has_offsets = True
        return num

    def _get_blob_code(self) -> str:
        if not self.prime_blob_enable or self.prime_blob_distance == 0 or self.getSettingValueByKey("purge_line_location") not in ["front", "left"]:
            return ""
        # Set extruder speed for 1.75 filament
        speed_blob = round(float(self.nozzle_size) * 500)
        # Adjust speed if 2.85 filament
        if self.material_diameter > 2: speed_blob *= .4
        blob_x = self.getSettingValueByKey("prime_blob_loc_x")
        blob_y = self.getSettingValueByKey("prime_blob_loc_y")
        blob_string = "G0 F1200 Z20 ; Move up\n"
        blob_string += f"G0 F{self.speed_travel} X{blob_x} Y{blob_y} ; Move to blob location\n"
        blob_string += f"G1 F{speed_blob} E{self.prime_blob_distance} ; Blob\n"
        blob_string += f"G1 F{self.retract_speed} E{self.prime_blob_distance - self.retract_dist} ; Retract\n"
        blob_string += "G92 E0 ; Reset extruder\n"
        blob_string += "M300 P500 S600 ; Beep\n"
        blob_string += "G4 S2 ; Wait\n"
        return blob_string
