# Copyright (c) 2026 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.
"""
Changelog:
- Revised by GregValiant 10-17-2022
    - Changed "extrude" line to before the nozzle moves back to the print (if not Repetier or Griffin).
    - Add M104 option for Resume temperature
- Revised by GregValiant (Greg Foresi) 04-01-25
    - Changes and additions:
        - Added more 'Pause Command' options for alternate firmware
        - Added 'Unload' option (prior to pause) and 'Reload' and 'Purge' options (after the pause).
        - Added 'Reason for Pause' options.
            ~If 'Reason_for_pause' == 'Filament Change' then Unload, Reload, and Purge become available.
            ~If 'Reason for Pause' == 'All Others' then the filament change options are hidden as they are not required.
        - Added 'Multiple Pause Layers' option.
            ~This works when all pauses will have the same settings.  Delimit the layer numbers with commas.
                ~~If pauses require different settings then add another instance of the script.
            ~Multiple messages can be added (also delimited by commas).  Each message will be assigned to the equivalent pause layer.
                ~~Example:  For pause layers 15,23,48 the messages could be:  White,Red,Blue
        - Added support for "Firmware Retraction"
        - Added 'One at a Time' support.
            ~Pauses can be at different layers in different parts.
            ~All pause layers must be listed (use the Cura Preview layer numbers).
            ~A pause at 'Layer:5' will only result in a pause at the first layer:5 encountered whereas pauses at '15,23,67' might be in different models.
            ~Models can be skipped, or have pauses at different layers than other models, and some models could be entirely different colors or material.
        - Added 'Flow Rate' option for 'Redo Layer'.
            ~Redo Layer will not run if in One-at-a-Time mode.
        - Multi-extruder printers now use the Cura settings of the active tool at the pause (retraction distance, retract and prime speeds, etc.)
        - The 'Stepper Timeout' has been de-confused.
    - Obsolete:
        - The retraction option is removed.  Retractions are added if required (and if retraction is enabled).
"""

from ..Script import Script
import re
from UM.Application import Application
from UM.Logger import Logger
from typing import Tuple
from UM.Message import Message

class PauseAtHeight(Script):

    # Pause Constants:
    MAXIMUM_E_CHUNK = 150
    FILAMENT_RATIO = 0.38  # Ratio of filament volume/mm between 1.75 and 2.85. Affects purge speeds.
    MAX_SAFE_E_SPEED = 100  # mm/s - firmware safety limit
    DEFAULT_PURGE_SPEED_MULTIPLIER = 500  # mm/min per mm nozzle diameter based on nozzle area
    PURGE_SPEED_CONSTANT = 1000  # multiplier for the purge speed flow adjustment based on nozzle area, E speed, and conversion from mm/sec to mm/min 
    BOWDEN_PURGE_OFFSET = 2.5  # retraction distance multiplier for bowden systems
    DIRECT_DRIVE_ADJUSTMENT = 7  # retraction adder for DD systems
    RELOAD_FAST_PERCENTAGE = 0.9  # 90% of reload amount at high speed and remainder at purge speed.

    #  Alter some settings per the configuration of the printer and user
    def initialize(self) -> None:
        """
        Adjusts the script settings depending on the Cura setup and Machine settings.
        """
        super().initialize()
        # Set up some defaults when loading.
        self.global_stack = Application.getInstance().getGlobalContainerStack()
        if self.global_stack is None or self._instance is None:
            return

        for key in ["machine_name", "machine_gcode_flavor"]:
            self._instance.setProperty(key, "value", self.global_stack.getProperty(key, "value"))

        machine_extruder_count = int(self.global_stack.getProperty("machine_extruder_count", "value"))
        self._instance.setProperty("tool_temp_overide_enable", "value", machine_extruder_count > 1)
        self._instance.setProperty("tool_temp_overide", "value", machine_extruder_count > 1)

        extruder = self.global_stack.extruderList
        standby_temperature = extruder[0].getProperty("material_standby_temperature", "value")
        resume_print_temperature = extruder[0].getProperty("material_print_temperature", "value")
        self._instance.setProperty("standby_temperature", "value", standby_temperature)
        self._instance.setProperty("resume_print_temperature", "value", resume_print_temperature)

        unload_reload_speed = int(self.global_stack.getProperty("machine_max_feedrate_e", "value"))
        # If Cura has the max E speed at 299792458000 knock it down to something reasonable
        if unload_reload_speed > self.MAX_SAFE_E_SPEED:
            unload_reload_speed = self.MAX_SAFE_E_SPEED

        # Set the machine limits to catch user typos
        self._instance.setProperty("unload_reload_speed", "value", unload_reload_speed)
        self._machine_width = int(self.global_stack.getProperty("machine_width", "value"))
        self._machine_depth = int(self.global_stack.getProperty("machine_depth", "value"))
        self._machine_height = int(self.global_stack.getProperty("machine_height", "value"))
        origin_at_center = bool(self.global_stack.getProperty("machine_center_is_zero", "value"))
        # Make an E-speed adjustment for printers that use 2.85 filament
        if extruder[0].getProperty("material_diameter", "value") > 2:
            self.DEFAULT_PURGE_SPEED_MULTIPLIER *= self.FILAMENT_RATIO
            self.PURGE_SPEED_CONSTANT *= self.FILAMENT_RATIO
        if not origin_at_center:
            self._instance.setProperty("x_max_value", "value", self._machine_width)
            self._instance.setProperty("y_max_value", "value", self._machine_depth)
            self._instance.setProperty("x_min_value", "value", 0)
            self._instance.setProperty("y_min_value", "value", 0)
        else:
            self._instance.setProperty("x_max_value", "value", round(self._machine_width/2))
            self._instance.setProperty("y_max_value", "value", round(self._machine_depth/2))
            self._instance.setProperty("x_min_value", "value", -abs(round(self._machine_width/2,1)))
            self._instance.setProperty("y_min_value", "value", -abs(round(self._machine_depth/2,1)))

    def getSettingDataString(self) -> str:
        return """{
            "name": "Pause at Height",
            "key": "PauseAtHeight",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "enable_pause_at_height":
                {
                    "label": "Enable the Pause script",
                    "description": "When disabled the script will not run.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                },
                "pause_at":
                {
                    "label": "'By Height' or 'By Layer'",
                    "description": "Select the pause search criteria.  'By Height' will pause at the layer that the particular height is reached, or the next layer if there is no exact match.  'By Height' does not allow multiple pauses when in One-at-a-Time mode.",
                    "type": "enum",
                    "options": {
                        "layer_no": "By Layer",
                        "height": "By Height"
                        },
                    "default_value": "layer_no",
                    "enabled": "enable_pause_at_height"
                },
                "pause_layer":
                {
                    "label": "Pause at End of layer(s)",
                    "description": "Enter the number of the LAST layer you want to finish prior to the pause. Use the layer numbers from the Cura preview.  If you want to use these exact same settings for more than one pause then use a comma to delimit the layer numbers.  If the settings are different then you must add another instance of PauseAtLayerOrHeight.",
                    "type": "str",
                    "value": "25",
                    "enabled": "enable_pause_at_height and pause_at == 'layer_no'"
                },
                "pause_height":
                {
                    "label": "Pause at Height(s)",
                    "description": "Enter the Height to pause at. The pause will occur at the layer where the height is reached (or exceeded if there is no exact match).  Example: enter 25.43 and the pause will occur at the start of the layer where Z>=25.43. If you want to use these exact same settings for more than one pause then use a comma to delimit the heights.  If the settings are different then you must add another instance of PauseAtLayerOrHeight.",
                    "type": "str",
                    "default_value": "37.5",
                    "enabled": "enable_pause_at_height and pause_at == 'height'"
                },
                "pause_method":
                {
                    "label": "Pause Command",
                    "description": "The gcode command to use to pause the print.  This is firmware dependent.  'M0 w/message(Marlin)' is firmware dependent but may show the LCD message if there is one.  'M0 (Marlin)' is the plain 'M0' command",
                    "type": "enum",
                    "options": {
                        "marlin": "M0 w/message(Marlin)",
                        "marlin2": "M0 (Marlin)",
                        "griffin": "M0 (Griffin,firmware retract)",
                        "bq": "M25 (BQ)",
                        "reprap": "M226 (RepRap)",
                        "repetier": "@pause (Repet/Octo)",
                        "alt_octo": "M125 (alt Octo)",
                        "raise_3d": "M2000 (raise3D)",
                        "klipper": "PAUSE (Klipper)",
                        "g_4": "G4 (dwell)",
                        "custom": "Custom Command"
                        },
                    "default_value": "marlin",
                    "value": "\\\"griffin\\\" if machine_gcode_flavor==\\\"Griffin\\\" else \\\"reprap\\\" if machine_gcode_flavor==\\\"RepRap (RepRap)\\\" else \\\"repetier\\\" if machine_gcode_flavor==\\\"Repetier\\\" else \\\"bq\\\" if \\\"BQ\\\" in machine_name or \\\"Flying Bear Ghost 4S\\\" in machine_name  else \\\"marlin\\\"",
                    "enabled": "enable_pause_at_height"
                },
                "g4_dwell_time":
                {
                    "label": "    G4 dwell time (in minutes)",
                    "description": "The amount of time to pause for. 'G4 S' is a 'hard' number.  You cannot make it shorter at the printer.  At the end of the dwell time - the printer will restart by itself.",
                    "type": "float",
                    "default_value": 5.0,
                    "minimum_value": 0.5,
                    "maximum_value_warning": 30.0,
                    "unit": "minutes   ",
                    "enabled": "enable_pause_at_height and pause_method == 'g_4'"
                },
                "custom_pause_command":
                {
                    "label": "    Custom Pause Command",
                    "description": "If none of the the stock options work with your printer you can enter a custom command here.  If you use 'M600' for the filament change you must include any other parameters.  Check the gcode carefully.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "enable_pause_at_height and pause_method == 'custom'"
                },
                "reason_for_pause":
                {
                    "label": "Reason for Pause",
                    "description": "Filament changes allow for the unload / load / purge sequence.  Other reasons (Ex: inserting nuts or magnets) don't require those.",
                    "type": "enum",
                    "options": {"reason_filament": "Filament Change", "reason_other": "All Others"},
                    "default_value": "reason_filament",
                    "enabled": "enable_pause_at_height"
                },
                "unload_amount":
                {
                    "label": "     Unload Amount",
                    "description": "How much filament must be retracted to unload for the filament change.  This number will be split into segments in the gcode as a single command might trip the 'excessive extrusion' warning in the firmware.",
                    "unit": "mm   ",
                    "type": "int",
                    "value": 95,
                    "default_value": 95,
                    "enabled": "enable_pause_at_height and pause_method != 'griffin' and reason_for_pause == 'reason_filament'"
                },
                "enable_quick_purge":
                {
                    "label": "    Quick purge before unload",
                    "description": "This can insure that the filament will unload by softening the tip so it can do the long retraction.  This purge is fixed length and will be 'retraction distance x 2.5' for bowden printers or 'retraction distance + 7' for direct drive printers.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "enable_pause_at_height and pause_method != 'griffin' and reason_for_pause == 'reason_filament' and unload_amount > 0"
                },
                "reload_amount":
                {
                    "label": "     Reload Amount",
                    "description": "The length of filament to load before the purge.  90% of this distance will be fast and the final 10% at the purge speed.  If you prefer to reload up to the nozzle by hand then set this to '0'.",
                    "unit": "mm   ",
                    "type": "int",
                    "value": 70,
                    "default_value": 70,
                    "enabled": "enable_pause_at_height and pause_method != 'griffin' and reason_for_pause == 'reason_filament'"
                },
                "unload_reload_speed":
                {
                    "label": "     Unload and Reload Speed",
                    "description": "How fast to unload or reload the filament in mm/sec.",
                    "unit": "mm/s   ",
                    "type": "int",
                    "value": 50,
                    "default_value": 50,
                    "enabled": "enable_pause_at_height and pause_method not in ['griffin', 'repetier'] and reason_for_pause == 'reason_filament' and pause_at == 'layer_no' and (reload_amount + unload_amount) != 0"
                },
                "purge_amount":
                {
                    "label": "     Purge Amount",
                    "description": "The amount of filament to be extruded after the pause. For most printers this is the amount to purge to complete a color change at the nozzle.  For Ultimaker2's this is to compensate for the retraction after the change. In that case 128+ is recommended.",
                    "unit": "mm   ",
                    "type": "int",
                    "value": 35,
                    "default_value": 35,
                    "enabled": "enable_pause_at_height and pause_method != 'griffin' and reason_for_pause == 'reason_filament'"
                },
                "extra_prime_amount":
                {
                    "label": "Extra Prime Amount",
                    "description": "Sometimes a little more is needed to account for oozing during a pause.  At .2 layer height and .4 line width - 0.10mm of 1.75 filament of 'Extra Prime' is 3mm of extrusion.  0.10mm of 2.85 filament of 'Extra Prime' would be 8mm of extrusion.  Plan accordingly.",
                    "unit": "mm   ",
                    "type": "str",
                    "value": "0.30",
                    "default_value": "0.30",
                    "enabled": "enable_pause_at_height and pause_method != 'griffin' and reason_for_pause == 'reason_other'"
                },
                "hold_steppers_on":
                {
                    "label": "Keep motors engaged",
                    "description": "Keep the steppers engaged so they don't lose position.  If this is unchecked then the Stepper Disarm time will be the default disarm time within the printer (often 2 minutes).",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "enable_pause_at_height and pause_method != 'griffin'"
                },
                "disarm_timeout":
                {
                    "label": "    Stepper disarm timeout",
                    "description": "After this amount of time (in minutes) the steppers will disarm (meaning that they will lose their positions). The behavior of a setting of '0' is dependent on the firmware.  It might mean 'disarm immediately' or 'never disarm'.  You would need to test it.",
                    "type": "int",
                    "default_value": 60,
                    "minimum_value": 0,
                    "maximum_value_warning": 120,
                    "unit": "minutes   ",
                    "enabled": "enable_pause_at_height and hold_steppers_on and pause_method != 'griffin'"
                },
                "head_park_enabled":
                {
                    "label": "Park the PrintHead",
                    "description": "Move the head to a safe location when pausing (necessary for filament changes with nozzle purges, or just to move it out of the way to make insertions into the print). Leave this unchecked if your printer handles parking for you.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "enable_pause_at_height and pause_method != 'griffin'"
                },
                "head_park_x":
                {
                    "label": "     Park PrintHead X",
                    "description": "What X location does the head move to when pausing.",
                    "unit": "mm   ",
                    "type": "float",
                    "maximum_value": "x_max_value",
                    "minimum_value": "x_min_value",
                    "default_value": 0,
                    "enabled": "enable_pause_at_height and head_park_enabled and pause_method != 'griffin'"
                },
                "x_min_value":
                {
                    "label": "Hidden setting",
                    "description": "Minimum X value for the build surface. Required for center origin machines",
                    "unit": "mm   ",
                    "type": "float",
                    "default_value": 0,
                    "enabled": false
                },
                "x_max_value":
                {
                    "label": "Hidden setting",
                    "description": "Maximum X value for the build surface. Required for center origin machines",
                    "unit": "mm   ",
                    "type": "float",
                    "default_value": 230,
                    "enabled": false
                },
                "head_park_y":
                {
                    "label": "     Park PrintHead Y",
                    "description": "What Y location does the head move to when pausing.",
                    "unit": "mm   ",
                    "type": "float",
                    "maximum_value": "y_max_value",
                    "minimum_value": "y_min_value",
                    "default_value": 0,
                    "enabled": "enable_pause_at_height and head_park_enabled and pause_method != 'griffin'"
                },
                "y_min_value":
                {
                    "label": "Hidden setting",
                    "description": "Minimum Y value for the build surface. Required for center origin machines",
                    "unit": "mm   ",
                    "type": "float",
                    "default_value": 0,
                    "enabled": false
                },
                "y_max_value":
                {
                    "label": "Hidden setting",
                    "description": "Maximum Y value for the build surface. Required for center origin machines",
                    "unit": "mm   ",
                    "type": "float",
                    "default_value": 230,
                    "enabled": false
                },
                "head_move_z":
                {
                    "label": "     Lift Head Z",
                    "description": "The relative move of the Z-axis above the print before parking.  If the Z ends up at less than 'Minimum Dist Nozzle to Plate' there will be a second move to provide room for purging below the nozzle (if you happen to be changing filament).",
                    "unit": "mm   ",
                    "type": "float",
                    "default_value": 1.0,
                    "minimum_value": 0.0,
                    "minimum_value_warning": 0.2,
                    "maximum_value_warning": 15,
                    "maximum_value": 20,
                    "enabled": "enable_pause_at_height and head_park_enabled and pause_method not in ['griffin', 'repetier']"
                },
                "retraction_amount":
                {
                    "label": "Retraction",
                    "description": "Obsolete - Disabled. Kept for compatibility with older versions of the script.  The retraction amount is now determined by the Cura settings for the active tool at the pause.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0,
                    "enabled": false
                },
                "retraction_speed":
                {
                    "label": "Retraction Speed",
                    "description": "Obsolete - Disabled. Kept for compatibility with older versions of the script. The retraction speed is now determined by the Cura settings for the active tool at the pause.",
                    "unit": "mm/s",
                    "type": "float",
                    "default_value": 0,
                    "enabled": false
                },
                "extrude_amount":
                {
                    "label": "Extrude Amount",
                    "description": "Obsolete - Disabled. Kept for compatibility with older versions of the script.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0,
                    "enabled": false
                },
                "extrude_speed":
                {
                    "label": "Extrude Speed",
                    "description": "Obsolete - Disabled. Kept for compatibility with older versions of the script.",
                    "unit": "mm/s",
                    "type": "float",
                    "default_value": 0,
                    "enabled": false
                },
                "min_purge_clearance":
                {
                    "label": "     Minimum dist nozzle to plate",
                    "description": "Pausing at a low layer might not leave enough room below the nozzle to purge.  The number you enter here will be used as the minimum Z height at the park position.  If your pause is at Z=8.4 and you enter 25 here then there will be a second Z move at the park position to move up to 25.",
                    "unit": "mm   ",
                    "type": "int",
                    "default_value": 15,
                    "minimum_value": 0,
                    "enabled": "enable_pause_at_height and head_park_enabled and pause_method not in ['griffin', 'repetier']"
                },
                "standby_wait_for_temperature_enabled":
                {
                    "label": "Use M109 for standby temperature? (M104 when false)",
                    "description": "Obsolete - Disabled. Kept for compatibility with older versions of the script.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": false
                },
                "standby_temperature":
                {
                    "label": "Standby Temperature",
                    "description": "The temperature to hold at during the pause.  If this temperature is different than your print temperature then use the 'M109' Resume Temperature Cmd option",
                    "unit": "°C   ",
                    "type": "int",
                    "default_value": 200,
                    "enabled": "enable_pause_at_height and pause_method not in [\\\"griffin\\\", \\\"repetier\\\"]"
                },
                "tool_temp_overide_enable":
                {
                    "label": "Hidden setting Temp Overide Enable",
                    "description": "Enable tool changes to overide the print temperature.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": false
                },
                "tool_temp_overide":
                {
                    "label": "Tool changes set resume temperature",
                    "description": "For multi-extruder printers - resume the print at the temperature of the current extruder.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "tool_temp_overide_enable and enable_pause_at_height"
                },
                "resume_temperature_cmd":
                {
                    "label": "Resume Temperature Cmd",
                    "description": "If you switch material, or if your standby temperature is different than the Resume Printing temperature, then use M109.  If standby and resume temperatures happen to be the same you can use M104 and there won't be a wait period.  'M109 R' (wait whether heating or cooling) is not enabled in all firmwares.  'M109 S' (wait for heating only) should work with any firmware.",
                    "type": "enum",
                    "options": {
                        "m104_cmd": "M104 S",
                        "m109_cmd_r": "M109 R",
                        "m109_cmd_s": "M109 S"},
                    "default_value": "m104_cmd",
                    "enabled": "enable_pause_at_height and pause_method not in [\\\"griffin\\\", \\\"repetier\\\"] and not tool_temp_overide"
                },
                "resume_print_temperature":
                {
                    "label": "Resume Print Temperature",
                    "description": "The temperature to resume the print after the pause.  If this temperature is different than your standby temperature then use the 'M109' Resume Temperature Cmd option",
                    "unit": "°C   ",
                    "type": "int",
                    "default_value": 200,
                    "enabled": "enable_pause_at_height and pause_method not in [\\\"griffin\\\", \\\"repetier\\\"] and not tool_temp_overide"
                },
                "display_text":
                {
                    "label": "Message to LCD",
                    "description": "Text that should appear on the display while paused. If left empty, there will not be any message.  Please note:  It is possible that the message will be immediately overridden by another message sent by the firmware.  If 'M0 w/message' is chosen as the pause command then the message is added to the pause command. You may have as many messages as pauses.  Delimit with a comma",
                    "type": "str",
                    "default_value": "",
                    "enabled": "enable_pause_at_height and pause_method != \\\"repetier\\\""
                },
                "custom_gcode_before_pause":
                {
                    "label": "G-code Before Pause",
                    "description": "Custom g-code to run before the pause. EX: M412 S0 ; Disable Runout. Use a comma to separate multiple commands. EX: M400,M412 S0,M117 Pause",
                    "type": "str",
                    "default_value": "",
                    "enabled": "enable_pause_at_height"
                },
                "beep_at_pause":
                {
                    "label": "Beep at pause",
                    "description": "Make an annoying sound when pausing",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_pause_at_height"
                },
                "beep_length":
                {
                    "label": "Beep duration",
                    "description": "How long should the annoying sound last.  The units are in milliseconds so 1000 equals 1 second. ('250' is a quick chirp).",
                    "type": "int",
                    "default_value": "1000",
                    "unit": "msec   ",
                    "enabled": "enable_pause_at_height and beep_at_pause"
                },
                "redo_layer":
                {
                    "label": "Redo Layer",
                    "description": "Redo the last layer before the pause, to get the filament flowing again after having oozed a bit during the pause.  (NOTE: Non-functional when Print Sequence is 'One At A Time').",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_pause_at_height and reason_for_pause == 'reason_filament'"
                },
                "redo_layer_flow":
                {
                    "label": "     Flow Rate for Redo Layer",
                    "description": "You can adjust the Flow Rate of the 'Redo Layer' to help keep a layer from sticking out due to over-extrusion.  The flow will be reset to 100% at the end of the redo layer.",
                    "type": "int",
                    "default_value": 100,
                    "maximum_value": 150,
                    "minimum_value": 50,
                    "enabled": "enable_pause_at_height and redo_layer and reason_for_pause == 'reason_filament'"
                },
                "custom_gcode_after_pause":
                {
                    "label": "G-code After Pause",
                    "description": "Custom g-code to run after the pause. Use a comma to separate multiple commands. EX: M204 X8 Y8,M106 S0,M412 S1 ; Enable runout.  Some firmware that uses M25 to pause may need a buffer to avoid executing commands that are beyond the pause line.  You can use 'M105,M105,M105,M105,M105,M105' as a buffer.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "enable_pause_at_height"
                },
                "machine_name":
                {
                    "label": "Machine Type",
                    "description": "The name of your 3D printer model. This setting is controlled by the script and will not be visible.",
                    "default_value": "Unknown",
                    "type": "str",
                    "enabled": false
                },
                "machine_gcode_flavor":
                {
                    "label": "G-code flavor",
                    "description": "The type of g-code to be generated. This setting is controlled by the script and will not be visible.",
                    "type": "enum",
                    "options":
                    {
                        "RepRap (Marlin/Sprinter)": "Marlin",
                        "RepRap (Volumetric)": "Marlin (Volumetric)",
                        "RepRap (RepRap)": "RepRap",
                        "UltiGCode": "Ultimaker 2",
                        "Griffin": "Griffin",
                        "Makerbot": "Makerbot",
                        "BFB": "Bits from Bytes",
                        "MACH3": "Mach3",
                        "Repetier": "Repetier"
                    },
                    "default_value": "RepRap (Marlin/Sprinter)",
                    "enabled": false
                }
            }
        }"""

    def execute(self, data: list[str]) -> list[str]:
        """
        Adds pauses 'By Layer' or 'By Height' based on the user input

        :param data: The gcode to be processed
        :return: The gcode with the pauses added
        """
        # Exit if the script is not enabled
        if not self.getSettingValueByKey("enable_pause_at_height"):
            data[0] += ";  [Pause at Layer or Height] Not enabled\n"
            Logger.log("i", "[Pause at Layer or Height] Not enabled")
            return data

        # Exit if the gcode has already been post-processed
        if ";POSTPROCESSED" in data[0]:
            return data

        # The preview_layer_list is a translation matrix for the layer locations in the Gcode.  It accounts for rafts and One-at-a-Time numbering.
        self.preview_layer_list = self.getPreviewLayerList(data)

        # Set some variables
        self.extruder_count = int(self.global_stack.getProperty("machine_extruder_count", "value"))
        self.extruder_list = self.global_stack.extruderList
        self.layer_height = float(self.global_stack.getProperty("layer_height", "value"))
        self.z_hop_enabled = bool(self.extruder_list[0].getProperty("retraction_hop_enabled", "value"))
        self.one_at_a_time = False if self.global_stack.getProperty("print_sequence", "value") == "all_at_once" else True
        self.redo_layer = self.getSettingValueByKey("redo_layer")

        pause_at = self.getSettingValueByKey("pause_at")
        pause_layer_string = str(self.getSettingValueByKey("pause_layer"))
        pause_height_string = str(self.getSettingValueByKey("pause_height"))

        # Added this as a 'minimum_value' check for the strings
        if (pause_layer_string == "" and pause_at == "layer_no") or (pause_height_string == "" and pause_at == "height"):
            Message(title = "[Pause at Layer or Height]", text = "Did not run because no layers or heights are entered.").show()
            Logger.log("i", "[Pause at Layer or Height] No layers or heights entered.")
            return data

        pause_display_string = str(self.getSettingValueByKey("display_text"))
        self.pause_lines_list = []

        # Get the pause layers or pause heights
        pause_layer_list, pause_index_list = self.getPauseIndexList(data, pause_at, pause_layer_string)

        # The display_text_list can match the pauses so color changes can be noted
        display_text_list = pause_display_string.split(",")

        # Go through the pause_index_list and add pauses to the gcode as necessary
        for index, pause_index in enumerate(pause_index_list):
            pause_layer = pause_layer_list[index]
            # Track the tool numbers so the settings will match the tool that is active at the pause
            self.tool_nr = 0
            if self.extruder_count > 1:
                self.tool_nr = self._track_tool_nr(data, pause_index)
            self._get_tool_settings(self.tool_nr)
            # This is to catch situations where the length of the display_list is shorter than the length of the pause_list.
            try:
                txt_msg = display_text_list[index]
            except IndexError:
                txt_msg = display_text_list[len(display_text_list) - 1]
            # Send the current pause_layer to _find_and_add_pause to create the string of commands to insert
            data = self._find_and_add_pause(data, int(pause_layer.strip()), txt_msg.strip(), pause_index)
        # Redo Layer is not compatible with One at a Time so if both are active - message the user that Redo Layer did not run
        if self.redo_layer and self.one_at_a_time:
            Message(title = "[Pause At Height]", text = "'Redo Layer' did not run because the Print Sequence is 'One-at-a-Time'.").show()
        self.pause_lines_list = []
        return data

    def _find_and_add_pause(self, data: list[str], pause_layer: int, txt_msg: str, pause_index: int) -> list[str]:
        """
        Goes through the list of pause layers/heights and adds pauses as required

        :param data: The gcode to be processed
        :param pause_layer: The layer number to pause at
        :param txt_msg: The message to display on the printer LCD
        :param pause_index: The index in the gcode where the pause should be inserted
        :return: the altered data
        """

        # Pause settings from this script
        hold_steppers_on = self.getSettingValueByKey("hold_steppers_on")
        disarm_timeout = self.getSettingValueByKey("disarm_timeout") * 60
        self.reason_for_pause = self.getSettingValueByKey("reason_for_pause")
        unload_amount = self.getSettingValueByKey("unload_amount")
        unload_quick_purge = self.getSettingValueByKey("enable_quick_purge")
        unload_reload_speed = int(self.getSettingValueByKey("unload_reload_speed")) * 60
        reload_amount = self.getSettingValueByKey("reload_amount")
        purge_amount = self.getSettingValueByKey("purge_amount")
        extra_prime_amount = self.getSettingValueByKey("extra_prime_amount")

        if self.reason_for_pause == "reason_filament":
            extra_prime_amount = "0"

        # Calculate the purge speed based on the nozzle size.  A 0.4 will be 200 and a 0.8 will be 400 mm/min.
        purge_speed = round(self.nozzle_size * self.DEFAULT_PURGE_SPEED_MULTIPLIER)

        # The slow_reload_speed is used at the end of the reloading to slow down the filament
        slow_reload_speed = purge_speed * 2

        # The park location and Z movement
        park_enabled = self.getSettingValueByKey("head_park_enabled")
        park_x = self.getSettingValueByKey("head_park_x")
        park_y = self.getSettingValueByKey("head_park_y")
        move_z = self.getSettingValueByKey("head_move_z")
        min_purge_clearance = self.getSettingValueByKey("min_purge_clearance")

        # Flow adjustment for Redo layer
        redo_layer_flow, redo_layer_flow_reset = self.getRedoLayerFlow()

        # Temperature settings from this script
        resume_temperature_cmd = self.getSettingValueByKey("resume_temperature_cmd")
        if resume_temperature_cmd in ["m104_cmd", "m109_cmd_s"]:
            resume_temperature_param = "S"
        else:
            resume_temperature_param = "R"

        standby_temperature = self.getSettingValueByKey("standby_temperature")
        use_tool_temperature = bool(self.getSettingValueByKey("tool_temp_overide"))
        resume_print_temperature = self.getSettingValueByKey("resume_print_temperature")

        # Temperature setting from Cura
        control_temperatures = self.global_stack.getProperty("machine_nozzle_temp_enabled", "value")

        # Firmware retraction
        firmware_retract = self.global_stack.getProperty("machine_firmware_retract", "value")

        # Consideration for Z-Hops which can interfere with 'By Height'
        if self.z_hop_enabled:
            self.z_hop_height = self.extruder_list[0].getProperty("retraction_hop", "value")
        else:
            self.z_hop_height = 0

        # The Gcode Before and Gcode After commands
        gcode_before, gcode_after = self.getGcodeBeforeAndAfter()

        # Beeps
        beep_at_pause = self.getSettingValueByKey("beep_at_pause")
        beep_length = self.getSettingValueByKey("beep_length")
        g4_dwell_time = round(self.getSettingValueByKey("g4_dwell_time") * 60)
        pause_method = self.getSettingValueByKey("pause_method")

        # The pause command to be used
        pause_command = self._get_pause_command(pause_method, txt_msg, g4_dwell_time)

        # Phase 1: Scan gcode up to the pause point to collect current Z and temperature
        layers_started, current_z, resume_print_temperature = self._scan_state_to_pause(
            data, pause_index, use_tool_temperature, resume_print_temperature
        )
        if not layers_started:
            self.pause_lines_list = []
            return data

        # Phase 2: Collect state from the layer just before the pause
        prev_layer = data[pause_index - 1]
        prev_lines = prev_layer.split("\n")
        is_retracted = None
        current_e = None
        chk_index = pause_index - 1

        # One at a time print sequence generates additional data[items] between models.  The first is often travel only and the second (if it is there) is a retraction.
        while current_e is None:
            current_e, is_retracted = self.getPreviousE(data, chk_index)
            if current_e is None:
                chk_index -= 1

        # Find last X,Y for the return-to location
        return_to_x, return_to_y = 0, 0
        for prev_line in reversed(prev_lines):
            if prev_line.startswith(("G0", "G1", "G2", "G3")):
                if self.getValue(prev_line, "X") is not None and self.getValue(prev_line, "Y") is not None:
                    return_to_x = self.getValue(prev_line, "X")
                    return_to_y = self.getValue(prev_line, "Y")
                    break

        # Maybe redo the previous layer.
        if self.redo_layer and self.reason_for_pause == "reason_filament" and not self.one_at_a_time:
            prev_layer = data[pause_index - 1]
            prev_layer = re.sub(";LAYER:", ";REDO_LAY:", prev_layer)
            temp_list = prev_layer.split("\n")
            temp_list[0] = temp_list[0] + str(" " * (29 - len(temp_list[0] + ".1"))) + "; Redo layer from 'Pause at Layer or Height'\n" + redo_layer_flow
            prev_layer = "\n".join(temp_list)
            data[pause_index] = prev_layer + redo_layer_flow_reset + data[pause_index]
            temp_list = []

            # Get the X Y position and the extruder's absolute position at the beginning of the redone layer.
            return_to_x, return_to_y = self.getNextXY(data[pause_index - 2])
            prev_lines = prev_layer.split("\n")
            for current_line in prev_lines:
                new_e = self.getValue(current_line, "E", current_e)
                if new_e != current_e:
                    if re.search("G1 F(\d+\.\d+|\d+) E(-?\d+\.\d+|-?\d+)", current_line) or "G10" in current_line:
                        if is_retracted == None:
                            is_retracted = True
                        if current_e is not None:
                            if is_retracted is None:
                                is_retracted = False
                    current_e = new_e
                    break

        # Start putting together the pause string 'pause_lines_list'
        partial_str = f";TYPE:CUSTOM---------------; Pause at end of Preview Layer {pause_layer}"
        if not self.one_at_a_time:
            partial_str += f" (end of Gcode LAYER:{int(pause_layer) - 1})"
        self.pause_lines_list.append(partial_str)

        # Don't change the extrusion mode if pause method is UM 'griffin'
        if pause_method != "griffin":
            self.pause_lines_list.append("M83 ; Relative extrusion")

        if pause_method == "repetier":
            if not is_retracted and self.retraction_enabled:
                self.pause_lines_list.append(f"G1 F{self.retraction_retract_speed} E-{self.retraction_amount} ; Retract")
            if park_enabled:
                # Move the head to the park location
                if current_z + move_z > self._machine_height:
                    move_z = 0
                self.pause_lines_list.append(f"G0 F{self.speed_z_hop} Z{round(current_z + move_z, 2)} ; Move up to clear the print")
                self.pause_lines_list.append(f"G0 F{self.speed_travel} X{park_x} Y{park_y} ; Move to park location")
                if current_z < move_z:
                    self.pause_lines_list.append(f"G0 F{self.speed_z_hop} Z{current_z + move_z} ; Move up to clear the print")
            # Disable the steppers
            self.pause_lines_list.append("M84 ; Disable Steppers")

        elif pause_method != "griffin":
            if not is_retracted and self.retraction_enabled:
                if firmware_retract:
                    self.pause_lines_list.append("G10 ; Retract")
                else:
                    self.pause_lines_list.append(f"G1 F{self.retraction_retract_speed} E-{self.retraction_amount} ; Retract")
            if park_enabled:
                # Move the head to the park position
                if current_z + move_z > self._machine_height:
                    move_z = 0
                self.pause_lines_list.append(f"G0 F{self.speed_z_hop} Z{round(current_z + move_z, 2)} ; Move up to clear the print")
                self.pause_lines_list.append(f"G0 F{self.speed_travel} X{park_x} Y{park_y} ; Move to park location")
                if current_z < min_purge_clearance - move_z:
                    self.pause_lines_list.append(f"G0 F{self.speed_z_hop} Z{min_purge_clearance} ; Minimum clearance" + str(" to purge" if purge_amount != 0 and self.reason_for_pause == 'reason_filament' else "") + " - move up some more")
            else:
                if current_z + move_z > self._machine_height:
                    move_z = 0
                self.pause_lines_list.append(f"G0 F{self.speed_z_hop} Z{round(current_z + move_z, 2)} ; Move up to clear the print")

            # 'Unload' and 'purge' are only available if there is a filament change.
            if self.reason_for_pause == "reason_filament" and int(unload_amount) > 0:
                # If it's a filament change then insert any 'unload' commands
                self.pause_lines_list.append("M400 ; Complete all moves")
                # Break up the unload distance into chunks of 'self.MAXIMUM_E_CHUNK'mm to avoid any firmware balks for 'too long of an extrusion'
                # The quick purge is meant to soften the filament end to insure it will retract.
                if unload_quick_purge:
                    quick_purge_amt = self.retraction_amount + self.DIRECT_DRIVE_ADJUSTMENT if self.retraction_amount < 2 else self.retraction_amount * self.BOWDEN_PURGE_OFFSET
                    self.pause_lines_list.append(f"G1 F{purge_speed} E{quick_purge_amt} ; Quick purge before unload")
                if unload_amount > self.MAXIMUM_E_CHUNK:
                    temp_unload = unload_amount
                    while temp_unload > self.MAXIMUM_E_CHUNK:
                        self.pause_lines_list.append(f"G1 F{int(unload_reload_speed)} E-{self.MAXIMUM_E_CHUNK} ; Unload some")
                        temp_unload -= self.MAXIMUM_E_CHUNK
                    if 0 < temp_unload <= self.MAXIMUM_E_CHUNK:
                        self.pause_lines_list.append(f"G1 F{int(unload_reload_speed)} E-{temp_unload} ; Unload the remainder")
                else:
                    self.pause_lines_list.append(f"G1 F{int(unload_reload_speed)} E-{unload_amount} ; Unload")

            # Set extruder standby temperature
            if control_temperatures:
                self.pause_lines_list.append(f"M104 S{round(standby_temperature)} ; Standby temperature")

        if txt_msg:
            self.pause_lines_list.append(f"M117 {txt_msg} ; Message to LCD")

        # Set the disarm timeout
        if pause_method != "griffin":
            if hold_steppers_on:
                temporary_str = f"M84 S{disarm_timeout}"
                if int(disarm_timeout) > 0:
                    temporary_str += f" ; Keep motors engaged for {str(disarm_timeout/60)} minutes"
                else:
                    temporary_str += " ; Keep motors engaged until printer power turned off (Marlin)."
                self.pause_lines_list.append(temporary_str)

        # Beep at pause
        if beep_at_pause:
            self.pause_lines_list.append(f"M300 S440 P{beep_length} ; Beep")

        # Insert any custom 'gcode before pause' lines
        if gcode_before:
            self.pause_lines_list.append(gcode_before)

        if txt_msg:
            self.pause_lines_list.append(f"M118 {txt_msg} ; Message to print server")

        # Insert the pause command
        self.pause_lines_list.append(f"{pause_command} ; Do the actual pause")

        # Insert any custom 'gcode after pause' lines
        if gcode_after:
            self.pause_lines_list.append(gcode_after)

        # If redoing a layer then move back down to the working height of that layer.
        if self.redo_layer:
            working_z = round(current_z - (self.layer_height if not self.z_hop_enabled else 0), 2)
            working_z_txt = "; Move down to redo layer height"
        else:
            working_z = current_z
            working_z_txt = "; Move down to resume height"

        relative_extrusion = self.global_stack.getProperty("relative_extrusion", "value")
        extrusion_mode_numeric = 83 if relative_extrusion else 82
        extrusion_mode_string = "relative" if relative_extrusion else "absolute"

        if pause_method == "repetier":
            # Optional purge
            if int(purge_amount) != 0:
                self.pause_lines_list.append(f"G1 F{purge_speed} E{purge_amount} ; Extra extrude after the unpause")
                self.pause_lines_list.append("     @info wait for cleaning nozzle from previous filament")
                self.pause_lines_list.append("     @pause remove the waste filament from parking area and press continue printing")

            # Retract after a purge before moving back to the print.
            if purge_amount != 0 and self.retraction_enabled:
                self.pause_lines_list.append(f"G1 F{self.retraction_retract_speed} E-{self.retraction_amount} ;Retract")

            # Move the head back to the resume position
            if park_enabled:
                self.pause_lines_list.append(f"G0 F{self.speed_travel} X{return_to_x} Y{return_to_y} ; Return to print location")
                self.pause_lines_list.append(f"G0 F{self.speed_z_hop} Z{working_z} {working_z_txt}")
            # Unretract when necessary
            if purge_amount != 0 and self.retraction_enabled:
                self.pause_lines_list.append(f"G1 F{self.retraction_prime_speed} E{self.retraction_amount} ; Unretract")

            # Change the extrusion mode as required
            self.pause_lines_list.append(f"M{extrusion_mode_numeric} ; switch back to {extrusion_mode_string} ; E values")

            # Reset extruder value to pre pause value
            self.pause_lines_list.append(f"G92 E{current_e} ;Reset extruder")

        elif pause_method != "griffin":
            if control_temperatures:
                # Set extruder resume temperature
                if resume_temperature_cmd in ["m109_cmd_r", "m109_cmd_s"] or use_tool_temperature:
                    temperature_cmd = 109
                    temperature_resume_str = "; Wait for resume temperature"
                else:
                    temperature_cmd = 104
                    temperature_resume_str = "; Resume temperature"

                self.pause_lines_list.append(f"M{temperature_cmd} {resume_temperature_param}{int(resume_print_temperature)} {temperature_resume_str}")

            # Load and Purge.  Break the load amount in 'self.MAXIMUM_E_CHUNK'mm chunks to avoid 'too long of extrusion' warnings from firmware.
            if self.reason_for_pause == "reason_filament":
                if int(reload_amount) > 0:
                    if reload_amount * self.RELOAD_FAST_PERCENTAGE > self.MAXIMUM_E_CHUNK:
                        partial_reload = reload_amount - reload_amount * .1
                        while partial_reload > self.MAXIMUM_E_CHUNK:
                            self.pause_lines_list.append(f"G1 F{unload_reload_speed} E{self.MAXIMUM_E_CHUNK} ; Fast Reload")
                            partial_reload -= self.MAXIMUM_E_CHUNK
                        if 0 < partial_reload <= self.MAXIMUM_E_CHUNK:
                            self.pause_lines_list.append(f"G1 F{round(int(unload_reload_speed))} E{round(partial_reload)} ; Fast Reload")
                            self.pause_lines_list.append(f"G1 F{round(float(self.nozzle_size) * self.PURGE_SPEED_CONSTANT)} E{round(reload_amount * (1 - self.RELOAD_FAST_PERCENTAGE))} ; Reload the remaining 10% slow to avoid jamming the nozzle")
                        else:
                            self.pause_lines_list.append(f"G1 F{round(float(self.nozzle_size) * self.PURGE_SPEED_CONSTANT)} E{round(reload_amount * (1 - self.RELOAD_FAST_PERCENTAGE))} ; Reload the remaining 10% slow to avoid jamming the nozzle")

                    else:
                        self.pause_lines_list.append(f"G1 F{round(int(unload_reload_speed))} E{round(reload_amount * self.RELOAD_FAST_PERCENTAGE)} ; Fast Reload")
                        self.pause_lines_list.append(f"G1 F{round(slow_reload_speed)} E{round(reload_amount * (1 - self.RELOAD_FAST_PERCENTAGE))} ; Reload the last 10% slower to avoid jamming the nozzle")

                if int(purge_amount) > 0:
                    self.pause_lines_list.append(f"G1 F{round(float(self.nozzle_size) * (self.PURGE_SPEED_CONSTANT / 2))} E{purge_amount} ; Purge")
                    if not firmware_retract and self.retraction_enabled:
                        self.pause_lines_list.append(f"G1 F{int(self.retraction_retract_speed)} E-{self.retraction_amount} ; Retract")
                    elif firmware_retract and self.retraction_enabled:
                        self.pause_lines_list.append("G10 ; Retract")
                    # If there is a purge then give the user time to grab the string before the head moves back to the print position.
                    self.pause_lines_list.append("M400 ; Complete all moves")
                    self.pause_lines_list.append("M300 P250 ; Beep")
                    self.pause_lines_list.append("G4 S2 ; Wait for 2 seconds")

            # Move the head back to the restart position
            if park_enabled:
                self.pause_lines_list.append(f"G0 F{self.speed_travel} X{return_to_x} Y{return_to_y} ; Move to resume location")
                self.pause_lines_list.append(f"G0 F{self.speed_z_hop} Z{working_z} {working_z_txt}")

            if purge_amount != 0:
                if firmware_retract and not is_retracted and self.retraction_enabled:
                    retraction_count = 1 if control_temperatures else 3 # Retract more if we don't control the temperature.
                    for i in range(retraction_count):
                        self.pause_lines_list.append("G11 ; Unretract")
                else:
                    if not is_retracted and self.retraction_enabled:
                        self.pause_lines_list.append(f"G1 F{self.retraction_prime_speed} E{self.retraction_amount} ; Unretract")

            # If the pause is for something like an magnet or nut insertion then there might be an extra prime amount
            if extra_prime_amount != "0" and self.reason_for_pause == "reason_other":
                self.pause_lines_list.append(f"G1 E{extra_prime_amount} F{int(self.retraction_prime_speed)} ; Extra Prime")

            if not self.redo_layer:
                self.pause_lines_list.append(f"M{extrusion_mode_numeric} ; Switch back to {extrusion_mode_string} E values")
                # Reset extruder value to pre-pause value
                self.pause_lines_list.append(f"G92 E{0 if relative_extrusion else current_e} ; Reset extruder location")

            if self.redo_layer and self.reason_for_pause == "reason_filament":
                # All other options reset the E value to what it was before the pause because E lines were added.
                # If it's not yet reset, it still needs to be reset if there were any redo layers.
                if is_retracted:
                    self.pause_lines_list.append(f"G92 E{0 if relative_extrusion else (round(current_e - self.retraction_amount,5))} ; Reset extruder location ~ retracted")
                    self.pause_lines_list.append(f"M{extrusion_mode_numeric} ; Switch back to {extrusion_mode_string} E values")
                else:
                    self.pause_lines_list.append(f"G92 E{0 if relative_extrusion else current_e} ; Reset extruder location ~ unretracted")
                    self.pause_lines_list.append(f"M{extrusion_mode_numeric} ; Switch back to {extrusion_mode_string} E values")

        # Add the end line
        self.pause_lines_list.append(f";{'-' * 26}; End of the Pause code")

        # Format the Prepend Gcode for readability
        for temp_index, temp_line in enumerate(self.pause_lines_list):
            if ";" in temp_line and not temp_line.startswith(";"):
                self.pause_lines_list[temp_index] = temp_line.replace(temp_line.split(";")[0], temp_line.split(";")[0] + str(" " * (27 - len(temp_line.split(";")[0]))), 1)
        pause_gcode_string = "\n".join(self.pause_lines_list)

        # Insert the Prepend Gcode at the end of the previous layer just before "TIME_ELAPSED".
        layer_lines = data[pause_index - 1].split("\n")
        layer_lines.insert(len(layer_lines) - 2, pause_gcode_string)
        data[pause_index - 1] = "\n".join(layer_lines)
        self.pause_lines_list = []
        return data

    def _scan_state_to_pause(self, data: list[str], pause_index: int, use_tool_temperature: bool, resume_print_temperature) -> Tuple[bool, float, float]:
        """
        Scans gcode up to the pause layer to collect whether printing has started,
        the current Z height, and (optionally) the latest resume temperature.

        :param data: The full gcode data list
        :param pause_index: The data index at which the pause will be inserted
        :param use_tool_temperature: Whether to track tool temperature changes
        :param resume_print_temperature: The initial resume temperature value
        :return: (layers_started, current_z, resume_print_temperature)
        """
        layers_started = False
        current_z = 0.0
        for index, layer in enumerate(data):
            for line in layer.split("\n"):
                if ";LAYER:0" in line:
                    layers_started = True
                if not layers_started:
                    continue
                if use_tool_temperature:
                    if line.startswith("M109 S") or line.startswith("M104 S"):
                        resume_print_temperature = self.getValue(line, "S")
                if self.getValue(line, "Z") is not None:
                    current_z = self.getValue(line, "Z")
            if index >= pause_index - 1:
                break
        return layers_started, current_z, resume_print_temperature

    def _get_pause_command(self, pause_method: str, txt_msg: str, g4_dwell_time: int) -> str:
        """
        Returns the gcode pause command string for the given pause method.

        :param pause_method: The selected pause method key
        :param txt_msg: The message to display (used by the marlin variant)
        :param g4_dwell_time: The dwell time in seconds (used by the g_4 variant)
        :return: The pause command string
        """
        custom_pause_command = self.getSettingValueByKey("custom_pause_command") if pause_method == "custom" else ""
        return {
            "marlin": "M0 " + txt_msg + " Click to resume",
            "marlin2": "M0",
            "griffin": "M0",
            "bq": "M25",
            "reprap": "M226",
            "repetier": "@pause now change filament and press continue printing",
            "alt_octo": "M125",
            "raise_3d": "M2000",
            "klipper": "PAUSE",
            "custom": str(custom_pause_command),
            "g_4": f"G4 S{g4_dwell_time}",
        }[pause_method]

    def getNextXY(self, layer: str) -> Tuple[float, float]:
        """
        Get the X and Y coordinates for a 'redo' layer.

        :param layer: The gcode layer to be searched
        :return: The X and Y coords for a 'redo' layer.
        """
        for line in reversed(layer.split("\n")):
            if line.startswith(("G0", "G1", "G2", "G3")):
                if self.getValue(line, "X") is not None and self.getValue(line, "Y") is not None:
                    return self.getValue(line, "X"), self.getValue(line, "Y")
        return 0, 0

    def _get_tool_settings(self, tool_nr: int) -> None:
        """
        Get the settings of the active extruder
        :param tool_nr: The tool number of the active extruder
        """
        self.retraction_enabled = self.extruder_list[tool_nr].getProperty("retraction_enable", "value")
        self.speed_z_hop = self.extruder_list[tool_nr].getProperty("speed_z_hop", "value") * 60
        self.retraction_amount = self.extruder_list[tool_nr].getProperty("retraction_amount", "value") if self.retraction_enabled else 0
        self.retraction_retract_speed = int(self.extruder_list[tool_nr].getProperty("retraction_retract_speed", "value")) * 60
        self.retraction_prime_speed = int(self.extruder_list[tool_nr].getProperty("retraction_prime_speed", "value")) * 60
        self.speed_travel = int(self.extruder_list[tool_nr].getProperty("speed_travel", "value")) * 60
        self.nozzle_size = self.extruder_list[tool_nr].getProperty("machine_nozzle_size", "value")

    def _track_tool_nr(self, data: list[str], pause_index: int) -> int:
        """
        For multi-extruder machines - track the tool so the proper settings get used in the pause.

        :param data: The gcode to be processed
        :param pause_index: The index in the gcode where the pause should be inserted
        :return: The tool number
        """
        for num in range(1, pause_index):
            lines = data[num].split("\n")
            for _, tool_line in enumerate(lines):
                if tool_line.startswith("T"):
                    self.tool_nr = self.getValue(tool_line, "T")
        return self.tool_nr

    def _pause_layer_from_height(self, data: list[str]) -> list[str]:
        """
        If 'height' - convert the heights to corresponding layer numbers and return the list.

        :param pause_height_list: A list derived from the pause_height_string
        :param temporary_layer_list: The list of layers derived from the layer heights
        :param cur_z: The working Z height
        :param p_hgt: The pause height currently being considered
        :param err_str: A string indicating the error for logging and user message
        :return: The list of corresponding layer numbers
        """
        pause_height_list = str(self.getSettingValueByKey("pause_height")).split(",")

        # For technical reasons - when in 'One at a time' print sequence, only a single height can be used.
        if self.one_at_a_time:
            pause_height_list = [pause_height_list[0]]

        temporary_layer_list = []
        for p_hgt in pause_height_list:
            # Get the 'height' equivalent layer number or skip it if it can't be cast to a float.  Inform the user of an error.
            try:
                p_hgt = float(p_hgt)
            except ValueError:
                Logger.log("w", "PauseAtLayerOrHeight error - An entered 'Height' could not be converted to a number.")
                err_str = f"An entered 'Height' ({p_hgt}) could not be converted to a number.  It was skipped."
                Message(title = "[PauseAtLayerOrHeight]", text = err_str).show()
                continue
            temporary_layer_list.append(str(self._is_legal_z(data, p_hgt)))
        return temporary_layer_list

    def _is_legal_z(self, data: list[str], the_height: float) -> int:
        """
        This returns the index of any 'height' that is passed to it.  If rafts are enabled this returns a data index adjusted by the raft height.

        :param data: The gcode to be processed
        :param the_height: The current height
        :return: The index corresponding to the legal Z height
        """
        starting_z = 0
        if str(self.global_stack.getProperty("adhesion_type", "value")) == "raft":
            # If z-hops are enabled then start looking for the Z after layer:0
            if self.z_hop_enabled:
                for layer in data:
                    if ";LAYER:0" in layer:
                        lines = layer.splitlines()
                        for index, line in enumerate(lines):
                            try:
                                if " Z" in line and (" E" in lines[index + 1] or "TYPE" in lines[index - 1]):
                                    starting_z = round(float(self.getValue(line, "Z")),2)
                                    the_height += starting_z
                                    break
                            except IndexError:
                                starting_z = round(float(self.getValue(line, "Z")),2)
                                the_height += starting_z
                                break
            # If Z-hops are disabled, then look for the starting Z from the start of the raft up to Layer:0
            else:
                for layer in data:
                    lines = layer.splitlines()
                    for index, line in enumerate(lines):
                        if " Z" in line and " E" in lines[index + 1]:
                            starting_z = self.getValue(line, "Z")
                        if ";LAYER:0" in line:
                            the_height += starting_z
                            break

        cur_z = 0.0
        for index, layer in enumerate(data):
            # Don't bother with the opening paragraph or the startup gcode
            the_index = 0
            if index < 2:
                continue
            lines = layer.splitlines()
            for z_index, line in enumerate(lines):
                if line[0:3] in ["G0 ", "G1 ", "G2 ", "G3 "]:
                    if " Z" in line:
                        cur_z = float(self.getValue(line, "Z"))
                    # The working Z of the layer is always after a ';TYPE:' line
                    if cur_z >= the_height and lines[z_index - 1].startswith(";TYPE:"):
                        # Subtract 2 to account for the first two items in the data list as they are not layers
                        the_index = index - 2
                        break
            if the_index > 0:
                break
        return the_index

    def getPreviewLayerList(self, data: list[str]) -> list[str]:
        """
        A list numbers that matches the Cura preview layers.  This is required for both All-At-Once and One-At-A-Time

        :param data: The gcode to be processed
        :return: The list of corresponding preview layer numbers
        """
        lay_num = 0
        preview_list = []
        for layer in data:
            if not ";LAYER:" in layer:
                preview_list.append("x")
            else:
                preview_list.append(str(lay_num))
                lay_num += 1

        return preview_list

    def getPreviousE(self, data: list[str], chk_index: int) -> Tuple[str, bool]:
        """
        Checks the end of the previous layer for the Last E value, and whether there was a retraction

        :param data: The gcode to be processed
        :param chk_index: The index of the previous layer to check
        :return: A tuple containing the current E value and a boolean indicating if the extruder is retracted
        """
        try:
            prev_layer = data[chk_index]
        except IndexError:
            Logger.log("w", "[PauseAtLayerOrHeight] Index error in getPreviousE")
            return "0", False
        prev_lines = prev_layer.split("\n")
        is_retracted = None
        current_e = None
        for prev_line in reversed(prev_lines):
            current_e = self.getValue(prev_line, "E")
            if re.search("G1 F(\d+\.\d+|\d+) E(-?\d+\.\d+|-?\d+)", prev_line) or "G10" in prev_line:
                if is_retracted == None:
                    is_retracted = True
            if current_e is not None:
                if is_retracted is None:
                    is_retracted = False
                break
        return current_e, is_retracted

    def getRedoLayerFlow(self) -> Tuple[str, str]:
        """
        Returns the Gcode to set the flow rate for a redo layer and the Gcode to reset it afterward.

        :return: A tuple containing the redo layer flow Gcode and the reset Gcode
        """
        redo_layer_flow = ""
        redo_layer_flow_reset = ""
        if self.redo_layer and self.reason_for_pause == "reason_filament":
            redo_layer_flow = f"M221 S{self.getSettingValueByKey('redo_layer_flow')}".ljust(27) + "; Set Redo Layer Flow Rate"
            redo_layer_flow_reset = "M221 S100                  ; End of Redo Layer - Reset Flow Rate\n"
        return redo_layer_flow, redo_layer_flow_reset

    def _format_custom_gcode(self, setting_key: str, label: str) -> str:
        """
        Reads a custom gcode setting and appends a comment label to each command.
        Comma-separated commands are each placed on their own line.

        :param setting_key: The settings key to read
        :param label: The comment label to append
        :return: The formatted gcode string
        """
        gcode = self.getSettingValueByKey(setting_key)
        if not gcode:
            return gcode
        comment = f"; {label}"
        if "," in gcode:
            return "\n".join(cmd.strip() + comment for cmd in gcode.split(","))
        return gcode + comment

    def getGcodeBeforeAndAfter(self) -> Tuple[str, str]:
        """
        Returns the Gcode to be inserted before and after the pause.

        :return: A tuple containing the Gcode before and after the pause
        """
        return (
            self._format_custom_gcode("custom_gcode_before_pause", "Gcode before pause"),
            self._format_custom_gcode("custom_gcode_after_pause", "Gcode after pause"),
        )

    def getPauseIndexList(self, data: list[str], pause_at: str, pause_layer_string: str) -> Tuple[list, list]:
        """
        Returns the list of pause indices based on the pause layer string.

        :param data: The gcode to be processed
        :param pause_at: The pause mode ('layer_no' or 'height')
        :param pause_layer_string: The string specifying the pause layers
        :return: A tuple containing the pause layer list and the pause index list
        """
        if pause_at == "layer_no":
            # When 'By Layer' the string from the setting can be used
            pause_layer_list = pause_layer_string.split(",")
        else:
            # When 'By Height' the string of heights must be converted to layers
            pause_layer_list = self._pause_layer_from_height(data)

        # Convert the pause layer numbers into their respective data[indexes] from the preview_layer_list.  This is a necessity for pausing in One at a Time mode.
        pause_index_list = []
        for p_layer in pause_layer_list:
            if str(p_layer) in self.preview_layer_list:
                pause_index_list.append(self.preview_layer_list.index(p_layer))
        return pause_layer_list, pause_index_list
