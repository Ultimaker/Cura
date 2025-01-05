# Written by GregValiant (Greg Foresi) November, 2024.
#    Searches for retraction and prime lines and changes the printer max E speed to the user input of the Max Flow Rate.  Optionally, can adjust the E Jerk.
# This script is compatible with both Absolute and Relative Extrusion and/or Firmware Retraction and both 1.75 and 2.85 diameter filament.
# Settings retreived from Cura are always for Extruder 1 (T0).
# Added E Jerk adjustment
# Added support for dual extruders
# Added support for RepRap M566
# The result is that retractions may look something like this
#    M203 E40.0 ; Adjust the E speed to the retraction is at it's set speed
#    M205 E4    ; Adjust the E Jerk for the retraction
#    G1 F2400 E659.39904 ;The retraction or prime
#    M203 E6.24 ; Reset the E speed to the correct speed for the user input Max Volumetric Flow
#    M205 E10   ; Reset the E Jerk to the Cura 'Default Filament Jerk' for printing.

import re
from ..Script import Script
from UM.Application import Application
import math
from UM.Message import Message

class MaxVolumetricSpeed(Script):

    def initialize(self) -> None:
        super().initialize()
        curaApp = Application.getInstance().getGlobalContainerStack()
        extruder_count = int(curaApp.getProperty("machine_extruder_count", "value"))
        if extruder_count > 1:
            self._instance.setProperty("multi_extruder", "value", True)
        gcode_flavor = curaApp.getProperty("machine_gcode_flavor", "value")
        if gcode_flavor in ["Repetier", "RepRap (RepRap)"]:
            self._instance.setProperty("jerk_cmd", "value", "M566")
            
    def getSettingDataString(self):
        return """{
            "name": "Max E Speed and Jerk Decoupler",
            "key": "MaxVolumetricSpeed",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "enable_script":
                {
                    "label": "Enable post processor",
                    "description": "Check the box to enable the script so it will run.",
                    "type": "bool",
                    "default_value": true
                },
                "jerk_cmd":
                {
                    "label": "The Jerk command to use",
                    "description": "Most firmwares (Ex: Marlin) use M205 for Jerk.  RepRap and Repetier might use M566.  You need to know which.",
                    "type": "enum",
                    "options": {
                        "M205": "M205",
                        "M566": "M566" },
                    "default_value": "M205",
                    "enabled": "enable_script"
                },
                "use_units":
                {
                    "label": "The Speed units in M203",
                    "description": "Most firmwares (Ex: Marlin) use mm/second for the M203 Max Speeds.  RepRap might use mm/minute.  You need to know which.",
                    "type": "enum",
                    "options": {
                        "per_second": "mm / second",
                        "per_minute": "mm / minute" },
                    "default_value": "per_second",
                    "enabled": "enable_script"
                },
                "enable_volumetric_t0":
                {
                    "label": "Enable Max Volumetric Control (T0)",
                    "description": "Check the box to limit the speed of the primary extruder to provide NO MORE than the entered amount of flow.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "enable_script"
                },
                "max_E_flow_rate_t0":
                {
                    "label": "    Max E Flow Rate (T0)",
                    "description": "The maximum flow rate that your printer works well at.  At every retraction or prime in the file the 'Max E Speed' will be adjusted upward for the retraction or prime and then back down for the printing extrusions.  The formula used is 'Max Flow Rate' divided by 'Filament Cross Section Area'.",
                    "type": "float",
                    "default_value": 12,
                    "unit": "mm3 / sec",
                    "enabled": "enable_script and enable_volumetric_t0"
                },
                "enable_jerk_adjustment_t0":
                {
                    "label": "Enable Jerk adjustment (T0)",
                    "description": "Check the box to also add M205's (or M566) to adjust the Jerk for retractions.  This will decouple the Jerk setting for the E from the other axes.  The default (reset) value is the 'Default Filament Jerk' in the Printer Settings.  You must have the 'Printer Settings' plugin loaded from the MarketPlace.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_script and enable_volumetric_t0"
                },
                "max_e_jerk_t0":
                {
                    "label": "    Retract/Prime Jerk (T0)",
                    "description": "This will adjust the Jerk before retract/prime and then reset it after.  The reset is 'Default Filament Jerk' from Cura.",
                    "type": "float",
                    "unit": "mm/sec  ",
                    "default_value": 10,
                    "enabled": "enable_script and enable_jerk_adjustment_t0 and enable_volumetric_t0"
                },
                "enable_volumetric_t1":
                {
                    "label": "Enable Max Volumetric Control (T1)",
                    "description": "Check the box to limit the speed of the SECOND extruder to provide NO MORE than the entered amount of flow.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "enable_script and multi_extruder"
                },
                "max_E_flow_rate_t1":
                {
                    "label": "    Max E Flow Rate (T1)",
                    "description": "The maximum flow rate that your printer works well at.  At every retraction or prime in the file the 'Max E Speed' will be adjusted upward for the retraction or prime and then back down for the printing extrusions.  The formula used is 'Max Flow Rate' divided by 'Filament Cross Section Area'.",
                    "type": "float",
                    "default_value": 12,
                    "unit": "mm3 / sec",
                    "enabled": "enable_script and enable_volumetric_t1 and multi_extruder"
                },
                "enable_jerk_adjustment_t1":
                {
                    "label": "Enable Jerk adjustment (T1)",
                    "description": "For the second extruder.  Check the box to also add M205's (or M566) to adjust the Jerk for retractions.  This will decouple the Jerk setting for the E from the other axes.  The default (reset) value is the 'Default Filament Jerk' in the Printer Settings.  You must have the 'Printer Settings' plugin loaded from the MarketPlace.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_script and enable_volumetric_t1 and multi_extruder"
                },
                "max_e_jerk_t1":
                {
                    "label": "    Retract/Prime Jerk (T1)",
                    "description": "This will adjust the Jerk before retract/prime and then reset it after.  The re-set is 'Default Filament Jerk' from Cura.",
                    "type": "float",
                    "unit": "mm/sec  ",
                    "default_value": 10,
                    "enabled": "enable_script and enable_volumetric_t1 and enable_jerk_adjustment_t1 and multi_extruder"
                },
                "multi_extruder":
                {
                    "label": "Hidden Setting",
                    "description": "Enables the settings for the second extruder.",
                    "type": "bool",
                    "value": false,
                    "default_value": false,
                    "enabled": false
                }
            }
        }"""

    def execute(self, data):
        # Exit if the script has been previously post-processed
        if ";POSTPROCESSED" in data[0]:
            return data
            
        # Exit if the script is not enabled
        enable_script = self.getSettingValueByKey("enable_script")
        if not enable_script:
            Message(title = "[Set Max Volumetric E Speed]", text = "Is not enabled and will not run").show()
            return data
        
        # Get settings from Cura
        curaApp = Application.getInstance().getGlobalContainerStack()
        extruder_count = curaApp.getProperty("machine_extruder_count", "value")
        extruder = curaApp.extruderList
        firmware_retraction = bool(curaApp.getProperty("machine_firmware_retract", "value"))
        enable_volumetric_t0 = self.getSettingValueByKey("enable_volumetric_t0")
        enable_volumetric_t1 = self.getSettingValueByKey("enable_volumetric_t1") if extruder_count > 1 else False
        filament_dia_t0 = float(extruder[0].getProperty("material_diameter", "value"))
        filament_dia_t1 = filament_dia_t0
        if enable_volumetric_t0:
            retract_enabled_t0 = bool(extruder[0].getProperty("retraction_enable", "value"))
            cura_retract_speed_t0 = float(extruder[0].getProperty("retraction_retract_speed", "value"))
            cura_prime_speed_t0 = float(extruder[0].getProperty("retraction_prime_speed", "value"))
            speed_e_reset_t0 = cura_retract_speed_t0 if cura_retract_speed_t0 >= cura_prime_speed_t0 else cura_prime_speed_t0
            max_E_flow_rate_t0 = self.getSettingValueByKey("max_E_flow_rate_t0")
            enable_jerk_adjustment_t0 = self.getSettingValueByKey("enable_jerk_adjustment_t0")
            max_e_jerk_t0 = round(self.getSettingValueByKey("max_e_jerk_t0"),1) if enable_jerk_adjustment_t0 else curaApp.getProperty("machine_max_jerk_e", "value")
            default_jerk_t0 = curaApp.getProperty("machine_max_jerk_e", "value")
        else:
            cura_retract_speed_t0 = float(extruder[0].getProperty("retraction_retract_speed", "value"))
            cura_prime_speed_t0 = float(extruder[0].getProperty("retraction_prime_speed", "value"))
            speed_e_reset_t0 = cura_retract_speed_t0 if cura_retract_speed_t0 >= cura_prime_speed_t0 else cura_prime_speed_t0

        if enable_volumetric_t1 and extruder_count > 1:
            retract_enabled_t1 = bool(extruder[1].getProperty("retraction_enable", "value"))
            cura_retract_speed_t1 = float(extruder[1].getProperty("retraction_retract_speed", "value"))
            cura_prime_speed_t1 = float(extruder[1].getProperty("retraction_prime_speed", "value"))
            speed_e_reset_t1 = cura_retract_speed_t1 if cura_retract_speed_t1 >= cura_prime_speed_t1 else cura_prime_speed_t1
            filament_dia_t1 = float(extruder[1].getProperty("material_diameter", "value"))
            max_E_flow_rate_t1 = self.getSettingValueByKey("max_E_flow_rate_t1")
            enable_jerk_adjustment_t1 = self.getSettingValueByKey("enable_jerk_adjustment_t1")
            max_e_jerk_t1 = round(self.getSettingValueByKey("max_e_jerk_t1"),1) if enable_jerk_adjustment_t1 else curaApp.getProperty("machine_max_jerk_e", "value")
            default_jerk_t1 = curaApp.getProperty("machine_max_jerk_e", "value")
        elif not enable_volumetric_t1 and extruder_count > 1:
            cura_retract_speed_t1 = float(extruder[1].getProperty("retraction_retract_speed", "value"))
            cura_prime_speed_t1 = float(extruder[1].getProperty("retraction_prime_speed", "value"))
            speed_e_reset_t1 = cura_retract_speed_t1 if cura_retract_speed_t1 >= cura_prime_speed_t1 else cura_prime_speed_t1
        if extruder_count > 1:
            final_speed_reset = speed_e_reset_t0 if speed_e_reset_t0 >= speed_e_reset_t1 else speed_e_reset_t1
        else:
            final_speed_reset = speed_e_reset_t0

        # Adjust the search parameter depending on Firmware Retraction
        if not firmware_retraction:
            search_string = "G1 F(\d+\.\d+|\d+) E(-?\d+\.\d+|-?\d+)"
        else:
            search_string = "G1[0-1]"
        search_regex = re.compile(search_string)

        # Calculate the E Speed Maximum for the extruder so it can't push beyond max volume
        if enable_volumetric_t0:
            cross_sect_t0 = ((filament_dia_t0/2)**2)*math.pi
            speed_e_max_t0 = round(max_E_flow_rate_t0 / cross_sect_t0, 2)
        else:
            speed_e_max_t0 = 100
        if enable_volumetric_t1 and extruder_count > 1:
            cross_sect_t1 = ((filament_dia_t1/2)**2)*math.pi
            speed_e_max_t1 = round(max_E_flow_rate_t1 / cross_sect_t1, 2)
        else:
            speed_e_max_t1 = 100

        # RepRap firmware may require that the M203 units are mm/minute
        if self.getSettingValueByKey("use_units") == "per_minute":
            speed_e_max_t0 = round(speed_e_max_t0 * 60)
            speed_e_reset_t0 = round(speed_e_reset_t0 * 60)
        # Initialize some variables
        replacement_before_t0 = ""; replacement_after_t0 = ""; replacement_before_t1 = ""; replacement_after_t1 = ""; repl_bef = ""; repl_aft = ""
        jerk_cmd = self.getSettingValueByKey("jerk_cmd")
        
        # Put the replacement strings together
        if enable_volumetric_t0:
            replacement_before_t0 += self._format_line(f"M203 E{speed_e_reset_t0} ; E Speed for Retract and Prime" + (" T0\n" if extruder_count > 1 else "\n"))
            replacement_after_t0 += "\n" + self._format_line(f"M203 E{speed_e_max_t0} ; E Speed Volume Limit" + (" T0" if extruder_count > 1 else ""))
            if enable_jerk_adjustment_t0:
                replacement_before_t0 += self._format_line(f"{jerk_cmd} E{max_e_jerk_t0} ; E Jerk for Retract and Prime" + (" T0\n" if extruder_count > 1 else "\n"))
                replacement_after_t0 += "\n" + self._format_line(f"{jerk_cmd} E{default_jerk_t0} ; E Jerk for Print" + (" T0" if extruder_count > 1 else ""))
        if enable_volumetric_t1 and extruder_count > 1:
            replacement_before_t1 += self._format_line(f"M203 E{speed_e_reset_t1} ; E Speed for Retract and Prime T1\n")
            replacement_after_t1 += "\n" + self._format_line(f"M203 E{speed_e_max_t1} ; E Speed Volume Limit T1")
            if enable_jerk_adjustment_t1:
                replacement_before_t1 += self._format_line(f"{jerk_cmd} E{max_e_jerk_t1} ; E Jerk for Retract and Prime T1\n")
                replacement_after_t1 += "\n" + self._format_line(f"{jerk_cmd} E{default_jerk_t1} ; E Jerk for Print T1")

        active_tool = 0
        # Required for multi-extruders - Start at the beginning and track the active tool
        if extruder_count > 1:
            startup = data[1].split("\n")
            for line in startup:
                if line.startswith("T"):
                    active_tool = int(self.getValue(line, "T"))

        # Make the replacements
        for num in range(2, len(data) - 1):
            lines = data[num].split("\n")
            for index, line in enumerate(lines):
                if line.startswith("T"):
                    active_tool = int(self.getValue(line, "T"))
                if active_tool == 0:
                    repl_bef = replacement_before_t0
                    repl_aft = replacement_after_t0
                else:
                    repl_bef = replacement_before_t1
                    repl_aft = replacement_after_t1
                if re.search(search_regex, line):
                    lines[index] = repl_bef + line + repl_aft
            data[num] = "\n".join(lines)

        # Reset the E speed at the end of the print
        if enable_volumetric_t0 or enable_volumetric_t1:
            data[len(data)-1] = f"M203 E{final_speed_reset} ; Reset max E speed\n" + data[len(data)-1]
        return data

    def _format_line(self, line: str) -> str:
        line = line.split(";")[0] + (" " * (15 - len(line.split(";")[0]))) + ";" + line.split(";")[1]
        return line