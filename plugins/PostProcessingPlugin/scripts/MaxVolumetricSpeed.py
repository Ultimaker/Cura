# Written by GregValiant (Greg Foresi) November, 2024.
#    Searches for retraction and prime lines and changes the printer max E speed to the user input of the Max Flow Rate
# The result is that retractions will look something like this
#    M203 E40.0
#    G1 F2400 E659.39904
#    M203 E6.24
# This script is compatible with both Absolute and Relative Extrusion and/or Firmware Retraction and both 1.75 and 2.85 diameter filament.
# Settings retreived from Cura are always for Extruder 1 (T0).
# Added E Jerk adjustment

import re
from ..Script import Script
from UM.Application import Application
import math
from UM.Message import Message

class MaxVolumetricSpeed(Script):

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
                "enable_volumetric":
                {
                    "label": "Enable Max Volumetric Control",
                    "description": "Check the box to enable M203's for retraction and primes.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "enable_script"
                },
                "max_E_flow_rate":
                {
                    "label": "    Max E Flow Rate",
                    "description": "The maximum flow rate that your printer works well at.  At every retraction or prime in the file the 'Max E Speed' will be adjusted upward for the retraction or prime and then back down for the printing extrusions.  The formula used is 'Max Flow Rate' divided by 'Filament Cross Section Area'.",
                    "type": "float",
                    "default_value": 12,
                    "unit": "mm3 / sec",
                    "enabled": "enable_script and enable_volumetric"
                },
                "use_units":
                {
                    "label": "    The units to use in M203",
                    "description": "Most firmwares (Ex: Marlin) use mm/second for the M203 Max Speeds.  RepRap might use mm/minute.",
                    "type": "enum",
                    "options": {
                        "per_second": "mm / second",
                        "per_minute": "mm / minute" },
                    "default_value": "per_second",
                    "enabled": "enable_script and enable_volumetric"
                },
                "enable_jerk_adjustment":
                {
                    "label": "Enable Jerk adjustment",
                    "description": "Check the box to also add M205's to adjust the Jerk for retractions.  This will decouple the Jerk setting for the E from the other axes.  ",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_script"
                },
                "max_e_jerk":
                {
                    "label": "    Max E Jerk",
                    "description": "This will adjust the Jerk before retract/prime and then reset it after.  The reset is 'Print Jerk' from Cura.",
                    "type": "int",
                    "unit": "mm/sec  ",
                    "default_value": 10,
                    "enabled": "enable_script and enable_jerk_adjustment"
                }
            }  
        }"""

    def execute(self, data):
        # Exit if the script is not enabled
        enable_script = self.getSettingValueByKey("enable_script")
        if not enable_script:
            Message(title = "[Set Max Volumetric E Speed]", text = "Is not enabled and will not run").show()
            return data
        # Get settings from Cura
        curaApp = Application.getInstance().getGlobalContainerStack()
        extruder = curaApp.extruderList
        retract_enabled = bool(extruder[0].getProperty("retraction_enable", "value"))
        cura_retract_speed = float(extruder[0].getProperty("retraction_retract_speed", "value"))
        cura_prime_speed = float(extruder[0].getProperty("retraction_prime_speed", "value"))
        # The reset_speed is used just for retractions and primes
        if cura_retract_speed > cura_prime_speed:
            speed_e_reset = cura_retract_speed
        else:
            speed_e_reset = cura_prime_speed
        firmware_retraction = bool(curaApp.getProperty("machine_firmware_retract", "value"))
        filament_dia = float(extruder[0].getProperty("material_diameter", "value"))
        max_e_flow_rate = self.getSettingValueByKey("max_E_flow_rate")
        enable_jerk_adjustment = self.getSettingValueByKey("enable_jerk_adjustment")
        enable_volumetric = self.getSettingValueByKey("enable_volumetric")
        max_e_jerk = self.getSettingValueByKey("max_e_jerk")
        default_jerk = extruder[0].getProperty("jerk_print", "value")
        # Adjust the search parameter depending on Firmware Retraction
        if not firmware_retraction:
            search_string = "G1 F(\d+\.\d+|\d+) E(-?\d+\.\d+|-?\d+)"
        else:
            search_string = "G1[0-1]"
        # Calculate the E Speed Maximum for the print
        cross_sect = ((filament_dia/2)**2)*math.pi
        speed_e_max = round(max_e_flow_rate / cross_sect, 2)
        # RepRap firmware may require that the M203 units are mm/minute
        if self.getSettingValueByKey("use_units") == "per_minute":
            speed_e_max = round(speed_e_max * 60)
            speed_e_reset = round(speed_e_reset * 60)
        replacement_before = ""
        replacement_after = ""
        if enable_volumetric:
            replacement_before += f"M203 E{speed_e_reset}\n"
            replacement_after += f"\nM203 E{speed_e_max}"
        if enable_jerk_adjustment:
            replacement_before += f"M205 E{max_e_jerk}\n"
            replacement_after += f"\nM205 E{default_jerk}"
        search_regex = re.compile(search_string)
        
        # Make the replacements
        for num in range(2, len(data) - 1):
            lines = data[num].split("\n")
            for index, line in enumerate(lines):
                if re.search(search_regex, line) is not None:
                    lines[index] = replacement_before + line + replacement_after
            data[num] = "\n".join(lines)
        # Reset the E speed at the end of the print
        if enable_volumetric:
            data[len(data)-1] = "M203 E" + str(speed_e_reset) + " ; Reset max E speed\n" + data[len(data)-1]
        return data
