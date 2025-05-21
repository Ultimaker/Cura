"""
By GregValiant (Greg Foresi) in April of 2025.
Print Skew Compensation is designed to use either Cura post processing, Marlin M852, or Klipper SET_SKEW to compensate for hardware skewing of prints.

The measurements for skew are different for each printer.  A log file will be created within the configuration folder 'scripts' sub-folder and will be based on the printer name (Ex: Ender-3Pro.skew.log).  When you change printers a new log file will be created but it is up to the user to make sure the settings are correct for that specific printer.

Skew Calibration model files are available on my Git page at:
https://github.com/GregValiant/GV-PostProcessors/tree/StartPoint/Skew%20Calibration%20Models

"""

from UM.Application import Application
from ..Script import Script
from UM.Message import Message
from UM.Logger import Logger
import re
import math
import os.path
from UM.Resources import Resources
import os

class PrintSkewCompensation(Script):
    def initialize(self) -> None:
        super().initialize()
        """ Get the "Printer Name.skew.log" file and parse it for the settings.  If there isn't a log file, then create it for the active printer and use the default values.  The log file gets updated to the current settings every time the script runs.  When the user activates a different printer the script will re-initialize"""
        set_lines = None
        active_printer = Application.getInstance().getGlobalContainerStack().getName()
        config_path = Resources.getConfigStoragePath()
        scripts_dir_path = os.path.join(config_path, "scripts")

        try:
            # Ensure the 'scripts' directory exists.
            # exist_ok=True prevents an error if the directory already exists.
            os.makedirs(scripts_dir_path, exist_ok=True)
        except OSError as e:
            Logger.log("e", f"Failed to create scripts directory {scripts_dir_path}: {e}")
            # If directory creation fails, set_lines will remain None,
            # and default settings will be used by _getSettings.

        log_file_name = os.path.join(scripts_dir_path, f"{active_printer}.skew.log")

        try:
            # Use 'with' statement for safer file handling (ensures file is closed).
            with open(log_file_name, "r") as skew_settings_file:
                set_lines = skew_settings_file.readlines()
        except FileNotFoundError:
            # This is an expected case if the log file doesn't exist yet.
            Logger.log("i", f"Log file {log_file_name} not found. Default settings will be used and a new log file created upon saving.")
            # set_lines remains None.
        except IOError as e:
            # Handles other I/O errors during reading (e.g., permission issues).
            Logger.log("w", f"Error reading log file {log_file_name}: {e}. Default settings will be used.")
            # set_lines remains None.

        # If there is a log file then load it and set the script settings to the values in the file.
        self._getSettings(set_lines)
        if set_lines != None:
            self._instance.setProperty("xy_ac_measurement", "value", self.xy_ac_temp)
            self._instance.setProperty("xy_bd_measurement", "value", self.xy_bd_temp)
            self._instance.setProperty("xy_ad_measurement", "value", self.xy_ad_temp)
            self._instance.setProperty("xz_ac_measurement", "value", self.xz_ac_temp)
            self._instance.setProperty("xz_bd_measurement", "value", self.xz_bd_temp)
            self._instance.setProperty("xz_ad_measurement", "value", self.xz_ad_temp)
            self._instance.setProperty("yz_ac_measurement", "value", self.yz_ac_temp)
            self._instance.setProperty("yz_bd_measurement", "value", self.yz_bd_temp)
            self._instance.setProperty("yz_ad_measurement", "value", self.yz_ad_temp)

    def getSettingDataString(self):
        return """{
            "name":"Print Skew Compensation",
            "key": "PrintSkewCompensation",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "enable_print_skew_comp":
                {
                    "label": "Enable Print Skew Comp",
                    "description": "Enable the script",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                },
                "compensation_method":
                {
                    "label": "Compensation Method",
                    "description": "Select 'Cura' to post-process the gcode.  Select 'Marlin' to insert an M852 line into the StartUp section of the Gcode.  Select 'Klipper' to insert a 'SET_SKEW' line into the StartUp section of the Gcode.  Both 'Marlin' and 'Klipper' require that the commands are enabled in the firmware.",
                    "type": "enum",
                    "options": {
                        "method_cura": "Cura",
                        "method_marlin": "Marlin",
                        "method_klipper": "Klipper"
                        },
                    "default_value": "method_cura",
                    "enabled": "enable_print_skew_comp"
                },
                "xy_ac_measurement":
                {
                    "label": " XY - A to C diagonal",
                    "description": "The distance measured across the A to C diagonal of the XY calibration print.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 141.42,
                    "maximum_value": 150.0,
                    "minimum_value": 130,
                    "enabled": "enable_print_skew_comp"
                },
                "xy_bd_measurement":
                {
                    "label": " XY - B to D diagonal",
                    "description": "The distance measured across the B to D diagonal of the XY calibration print.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 141.42,
                    "minimum_value": 130,
                    "maximum_value": 150,
                    "enabled": "enable_print_skew_comp"
                },
                "xy_ad_measurement":
                {
                    "label": " XY - A to D width",
                    "description": "The distance measured across the A to D width of the XY calibration print.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 100.00,
                    "minimum_value": 1.00,
                    "enabled": "enable_print_skew_comp"
                },
                "xz_ac_measurement":
                {
                    "label": "    XZ - A to C diagonal",
                    "description": "The distance measured across the A to C diagonal of the XZ calibration print.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 141.42,
                    "maximum_value": 150.0,
                    "minimum_value": 130,
                    "enabled": "enable_print_skew_comp"
                },
                "xz_bd_measurement":
                {
                    "label": "    XZ - B to D diagonal",
                    "description": "The distance measured across the B to D diagonal of the XZ calibration print.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 141.42,
                    "maximum_value": 150.0,
                    "minimum_value": 130,
                    "enabled": "enable_print_skew_comp"
                },
                "xz_ad_measurement":
                {
                    "label": "    XZ - A to D width",
                    "description": "The distance measured across the A to D width of the XZ calibration print.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 100.00,
                    "minimum_value": 1,
                    "enabled": "enable_print_skew_comp"
                },
                "yz_ac_measurement":
                {
                    "label": " YZ - A to C diagonal",
                    "description": "The distance measured across the A to C diagonal of the YZ calibration print.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 141.42,
                    "maximum_value": 150.0,
                    "minimum_value": 130.0,
                    "enabled": "enable_print_skew_comp"
                },
                "yz_bd_measurement":
                {
                    "label": " YZ - B to D diagonal",
                    "description": "The distance measured across the B to D diagonal of the YZ calibration print.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 141.42,
                    "maximum_value": 150.0,
                    "minimum_value": 130,
                    "enabled": "enable_print_skew_comp"
                },
                "yz_ad_measurement":
                {
                    "label": " YZ - A to D width",
                    "description": "The distance measured across the A to D width of the YZ calibration print.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 100.00,
                    "minimum_value": 1,
                    "enabled": "enable_print_skew_comp"
                },
                "add_settings_to_gcode":
                {
                    "label": "Add settings to the gcode",
                    "description": "Whether to make a record of these settings in the gcode file.  They go in at the end of the file.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_print_skew_comp"
                }
            }
        }"""

    def execute(self, data: list):

        # Set up to open the log file
        self.active_printer = Application.getInstance().getGlobalContainerStack().getName()
        config_path = Resources.getConfigStoragePath()
        pp_path = os.path.join(config_path, "scripts")
        log_file_name = os.path.join(pp_path, self.active_printer + ".skew.log")

        # Exit if the post processor is not enabled
        if not bool(self.getSettingValueByKey("enable_print_skew_comp")):
            data[0] += ";  [Print Skew Compensation] not enabled\n"
            return data

        # Exit if the gcode has already been post-processed
        if ";POSTPROCESSED" in data[0]:
            return

        # Notify the user that this script should run first
        scripts = Application.getInstance().getGlobalContainerStack().getMetaDataEntry("post_processing_scripts")
        script_list = scripts.split("\\n")
        if not "PrintSkewCompensation" in script_list[0]:
            Logger.log("i", str(script_list[0]))
            Message(
                title = "[Print Skew Compensation]",
                text = "Should be first in the Post-Processor list.  It will run if it isn't first, but any following post-processors should act on the changes made by 'Print Skew Compensation'.").show()

        # The current settings for this script
        self.compensation_method = self.getSettingValueByKey("compensation_method")
        self.xy_ac_dist = self.getSettingValueByKey("xy_ac_measurement")
        self.xy_bd_dist = self.getSettingValueByKey("xy_bd_measurement")
        self.xy_ad_dist = self.getSettingValueByKey("xy_ad_measurement")
        self.xz_ac_dist = self.getSettingValueByKey("xz_ac_measurement")
        self.xz_bd_dist = self.getSettingValueByKey("xz_bd_measurement")
        self.xz_ad_dist = self.getSettingValueByKey("xz_ad_measurement")
        self.yz_ac_dist = self.getSettingValueByKey("yz_ac_measurement")
        self.yz_bd_dist = self.getSettingValueByKey("yz_bd_measurement")
        self.yz_ad_dist = self.getSettingValueByKey("yz_ad_measurement")

        # Skew Factors
        self.xy_skew_factor = self.calculate_skew_factor(self.xy_ac_dist, self.xy_bd_dist, self.xy_ad_dist)
        self.xz_skew_factor = self.calculate_skew_factor(self.xz_ac_dist, self.xz_bd_dist, self.xz_ad_dist)
        self.yz_skew_factor = self.calculate_skew_factor(self.yz_ac_dist, self.yz_bd_dist, self.yz_ad_dist)

        # Select the proper function based on the compensation_method
        if self.compensation_method == "method_cura":
            data = self.cura_compensation(data)
        elif self.compensation_method == "method_marlin":
            data = self.marlin_compensation(data)
        elif self.compensation_method == "method_klipper":
            data = self.klipper_compensation(data)

        # Add the script settings to the gcode if requested
        if self.getSettingValueByKey("add_settings_to_gcode"):
            setting_string = (
                f";  Print Skew Compensation Settings:\n"
                f";    xy_ac_measurement: {self.xy_ac_dist}\n"
                f";    xy_bd_measurement: {self.xy_bd_dist}\n"
                f";    xy_ad_measurement: {self.xy_ad_dist}\n"
                f";        XY skew factor:    {round(self.xy_skew_factor, 8)}\n"
                f";    xz_ac_measurement: {self.xz_ac_dist}\n"
                f";    xz_bd_measurement: {self.xz_bd_dist}\n"
                f";    xz_ad_measurement: {self.xz_ad_dist}\n"
                f";        XZ skew factor:    {round(self.xz_skew_factor, 8)}\n"
                f";    yz_ac_measurement: {self.yz_ac_dist}\n"
                f";    yz_bd_measurement: {self.yz_bd_dist}\n"
                f";    yz_ad_measurement: {self.yz_ad_dist}\n"
                f";        YZ skew factor:    {round(self.yz_skew_factor, 8)}\n"
            )
            data[len(data) - 1] += setting_string

        # Write the settings to the log file
        self._write_log_file(log_file_name)
        return data

    def cura_compensation(self, cura_data: str) -> str:

        # z_input is cummulative
        z_input = 0
        cur_x = 0
        cur_y = 0
        cur_z = 0
        for layer_index, layer in enumerate(cura_data):
            lines = layer.split("\n")

            # Get the X, Y, Z locations
            for index, line in enumerate(lines):
                if line.startswith(("G0", "G1")):
                    cur_x = self.getValue(line, "X", None)
                    cur_y = self.getValue(line, "Y", None)
                    cur_z = self.getValue(line, "Z", None)

                    # Reset x_input and y_input every time through
                    x_input = 0
                    y_input = 0

                    # Equivalencies to avoid confusion
                    if cur_x != None:
                        x_input = cur_x
                    if cur_y != None:
                        y_input = cur_y
                    if cur_z != None:
                        z_input = cur_z

                    # Calculate the skew compensation
                    x_out = round(x_input - y_input * self.xy_skew_factor, 3)
                    x_out = round(x_out - z_input * self.xz_skew_factor, 3)
                    y_out = round(y_input - z_input * self.yz_skew_factor, 3)

                    # If the first layer hasn't started then jump out (after tracking the XYZ).
                    if layer_index < 2:
                        continue

                    # Alter the current line
                    if cur_x != None:
                        lines[index] = lines[index].replace(f"X{cur_x}", f"X{x_out}")
                    if cur_y != None:
                        lines[index] = lines[index].replace(f"Y{cur_y}", f"Y{y_out}")
            cura_data[layer_index] = "\n".join(lines)
        return cura_data

    def marlin_compensation(self, cura_data: str) -> str:

        # If the skew_factors are zero then leave a message in the Gcode
        if self.xy_skew_factor == 0 and self.xz_skew_factor == 0 and self.yz_skew_factor == 0:
            cmd_line = ";No Skew Compensation Required"
        else:
            cmd_line = "M852"

        # If only the XY skew factor is > 0 the use the "S" parameter
        if self.xy_skew_factor and (self.xz_skew_factor == 0 and self.yz_skew_factor == 0):
            cmd_line += f" S{round(self.xy_skew_factor, 8)}"
        elif self.xy_skew_factor and (self.xz_skew_factor != 0 or self.yz_skew_factor != 0):
            cmd_line += f" I{round(self.xy_skew_factor,8)}"
        if self.xz_skew_factor != 0:
            cmd_line += f" J{round(self.xz_skew_factor,8)}"
        if self.yz_skew_factor != 0:
            cmd_line += f" K{round(self.yz_skew_factor,8)}"
        startup = cura_data[1].split("\n")
        startup.insert(1, cmd_line)
        cura_data[1] = "\n".join(startup)
        return cura_data

    def klipper_compensation(self, cura_data: str) -> str:

        # If the skew_factors are zero then leave a message in the Gcode
        if self.xy_skew_factor == 0 and self.xz_skew_factor == 0 and self.yz_skew_factor == 0:
            cmd_line = ";No Skew Compensation Required"
        else:
            cmd_line = "SET_SKEW"
        if self.xy_skew_factor != 0:
            cmd_line += f" XY={self.xy_ac_dist},{self.xy_bd_dist},{self.xy_ad_dist}"
        if self.xz_skew_factor != 0:
            cmd_line += f" XZ={self.xz_ac_dist},{self.xz_bd_dist},{self.xz_ad_dist}"
        if self.yz_skew_factor != 0:
            cmd_line += f" YZ={self.yz_ac_dist},{self.yz_bd_dist},{self.yz_ad_dist}"
        if cmd_line == "SET_SKEW":
            cmd_line = ";No Skew Compensation Required"
        startup = cura_data[1].split("\n")
        startup.insert(1, cmd_line)
        cura_data[1] = "\n".join(startup)
        return cura_data

    def calculate_skew_factor(self, ac: float, bd: float, ad:float) -> str:
        ab = math.sqrt(2*ac*ac+2*bd*bd-4*ad*ad)/2
        skew_comp = math.tan(math.pi/2-math.acos((ac*ac-ab*ab-ad*ad)/(2*ab*ad)))
        return skew_comp

    def _getSettings(self, lines: str) -> str:

        # Parse the log file for the settings
        if lines != None:
            self.active_printer = lines[0].split(":")[1]
            self.compensation_method = lines[1].split(":")[1]
            self.xy_ac_temp = float(lines[2].split(":")[1])
            self.xy_bd_temp = float(lines[3].split(":")[1])
            self.xy_ad_temp = float(lines[4].split(":")[1])
            self.xz_ac_temp = float(lines[5].split(":")[1])
            self.xz_bd_temp = float(lines[6].split(":")[1])
            self.xz_ad_temp = float(lines[7].split(":")[1])
            self.yz_ac_temp = float(lines[8].split(":")[1])
            self.yz_bd_temp = float(lines[9].split(":")[1])
            self.yz_ad_temp = float(lines[10].split(":")[1])
            self.xy_skew_factor = float(lines[11].split(":")[1])
            self.xz_skew_factor = float(lines[12].split(":")[1])
            self.yz_skew_factor = float(lines[13].split(":")[1])
            self.add_settings_to_gcode = bool(lines[14].split(":")[1])
        else:
            # Set the defaults
            self.active_printer = Application.getInstance().getGlobalContainerStack().getName()
            self.compensation_method = "method_cura"
            # XY plane measurements
            self.xy_ac_temp = 141.42
            self.xy_bd_temp = 141.42
            self.xy_ad_temp = 100.00
            # XZ plane measurements
            self.xz_ac_temp = 141.42
            self.xz_bd_temp = 141.42
            self.xz_ad_temp = 100.00
            # YZ plane measurements
            self.yz_ac_temp = 141.42
            self.yz_bd_temp = 141.42
            self.yz_ad_temp = 100.00
            # Skew Factors
            self.xy_skew_factor = 0.00
            self.xz_skew_factor = 0.00
            self.yz_skew_factor = 0.00
            self.add_settings_to_gcode = False
        return None

    def _write_log_file(self, log_file_name: str) -> None:
        # Write the log file
        the_line = (
            f"active_printer:{self.active_printer}\n"
            f"compensation_method:{self.compensation_method}\n"
            f"xy_ac_dist:{self.xy_ac_dist}\n"
            f"xy_bd_dist:{self.xy_bd_dist}\n"
            f"xy_ad_dist:{self.xy_ad_dist}\n"
            f"xz_ac_dist:{self.xz_ac_dist}\n"
            f"xz_bd_dist:{self.xz_bd_dist}\n"
            f"xz_ad_dist:{self.xz_ad_dist}\n"
            f"yz_ac_dist:{self.yz_ac_dist}\n"
            f"yz_bd_dist:{self.yz_bd_dist}\n"
            f"yz_ad_dist:{self.yz_ad_dist}\n"
            f"xy_skew_factor:{round(self.xy_skew_factor, 8)}\n"
            f"xz_skew_factor:{round(self.xz_skew_factor, 8)}\n"
            f"yz_skew_factor:{round(self.yz_skew_factor, 8)}\n"
            f"add_settings_to_gcode:{str(self.add_settings_to_gcode)}"
        )
        try:
            with open(log_file_name, "w") as skew_log_file:
                skew_log_file.write(the_line)
        except IOError as e:
            Logger.log("e", f"Failed to write to log file {log_file_name}: {e}")
        return None