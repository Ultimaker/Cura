"""
This script was found on Thingiverse and appears to have been posted by 'joochung' in 2018.
Update and bug fixes by GregValiant (Greg Foresi) in April of 2025.
"""

from UM.Application import Application
from ..Script import Script
from UM.Message import Message
import re

class PrintSkewCompensation(Script):
    def __init__(self):
        super().__init__()

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
                "xy_calc_type":
                {
                    "label": "XY (Top View) Calculation By",
                    "description": "XY Compensation based on: 'Y Base Line Length' and the 'X Error', or on a user-calculated tangent.",
                    "type": "enum",
                    "options": {"xytype_len":"Lengths","xytype_tan":"Tangent"},
                    "default_value": "xytype_len",
                    "enabled": "enable_print_skew_comp"
                },
                "xy_x_error":
                {
                    "label": "    XY Plane 'X' Error",
                    "description": "Error on the X axis in the XY plane (in mm).  This error is visible when looking straight down on the print (the Top View).  With the bottom edge of the print square to the front edge of the build plate - this is the adjustment required to make a parallelogram a rectangle.  A negative value will move the top of the shape to the right (CW) and a positive value will move the top of the shape to the left (CCW).",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0.0,
                    "maximum_value": 5.0,
                    "minimum_value": -5.0,
                    "enabled": "enable_print_skew_comp and xy_calc_type == 'xytype_len'"
                },
                "xy_y_length":
                {
                    "label": "    XY Plane 'Y' Base Line",
                    "description": "Length of the 'Y' side where the X error measurement was taken.  (The default assumes a 100mm calibration cube.)",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 100.0,
                    "minimum_value": 0.0,
                    "enabled": "enable_print_skew_comp and xy_calc_type == 'xytype_len'"
                },
                "xy_tangent":
                {
                    "label": "    XY Tangent",
                    "description": "The error in the XY as a tangent. The formula is 'X Error'/'Y Length'",
                    "unit": "radian",
                    "type": "float",
                    "default_value": 0.0,
                    "minimum_value": 0.0001,
                    "enabled": "enable_print_skew_comp and xy_calc_type == 'xytype_tan'"
                },
                "yz_calc_type":
                {
                    "label": "YZ (Side View) Calculation By",
                    "description": "YZ Compensation based on: 'Z Base Line Height' and 'Y Error', or on a user-calculated tangent.",
                    "type": "enum",
                    "options": {"yztype_len":"Lengths","yztype_tan":"Tangent"},
                    "default_value": "yztype_len",
                    "enabled": "enable_print_skew_comp"
                },
                "yz_y_error":
                {
                    "label": "    YZ Plane 'Y' Error",
                    "description": "Error on the Y axis for the YZ plane in mm.  This error is visible in the 'Side View' of the print.  This is the adjustment required to make a parallelogram into a rectangle.  A negative value will move the top of the shape to the right (CW) and a positive value will move the top of the shape to the left (CCW).",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0.0,
                    "maximum_value": 5.0,
                    "minimum_value": -5.0,
                    "enabled": "enable_print_skew_comp and yz_calc_type == 'yztype_len'"
                },
                "yz_z_hgt":
                {
                    "label": "    YZ Plane 'Z' Height",
                    "description": "Height of the Z side where the YZ error measurement was taken. (The default assumes a 100mm calibration cube.)",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 100,
                    "minimum_value": 0.0,
                    "enabled": "enable_print_skew_comp and yz_calc_type == 'yztype_len'"
                },
                "yz_tangent":
                {
                    "label": "    YZ Tangent",
                    "description": "The error in YZ as a tangent. The formula is 'Y Error'/'Z Height'",
                    "unit": "radian",
                    "type": "float",
                    "default_value": 0.0,
                    "minimum_value": 0.0001,
                    "enabled": "yz_calc_type == 'yztype_tan'"
                },

                "xz_calc_type":
                {
                    "label": "XZ (Front View) Calculation By",
                    "description": "XZ Compensation based on: 'Z Base Line Height' and the 'X Error', or on a user-calculated tangent.",
                    "type": "enum",
                    "options": {"xztype_len":"Lengths","xztype_tan":"Tangent"},
                    "default_value": "xztype_len",
                    "enabled": "enable_print_skew_comp"
                },
                "xz_x_error":
                {
                    "label": "    XZ Plane 'X' Error",
                    "description": "Error on the 'X' axis on the XZ plane in mm.  This error is visible in the 'Front View' of the print.  This is the adjustment required to make a parallelogram into a rectangle.  A negative value will move the top of the shape to the right (CW) and a positive value will move the top of the shape to the left (CCW).",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0.0,
                    "maximum_value": 5.0,
                    "minimum_value": -5.0,
                    "enabled": "enable_print_skew_comp and xz_calc_type == 'xztype_len'"
                },
                "xz_z_hgt":
                {
                    "label": "    XZ Plane 'Z' Height",
                    "description": "Height of the 'Z' side where the 'X' error measurement was taken. (The default assumes a 100mm calibration cube.)",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 100,
                    "minimum_value": 0.0,
                    "enabled": "enable_print_skew_comp and xz_calc_type == 'xztype_len'"
                },
                "xz_tangent":
                {
                    "label": "    XZ Tangent",
                    "description": "The error in the ZX pair as a tangent. The formula is 'XZ Error'/'XZ Height'",
                    "unit": "radian",
                    "type": "float",
                    "default_value": 0.0,
                    "minimum_value": 0.0001,
                    "enabled": "enable_print_skew_comp and xz_calc_type == 'xztype_tan'"
                }
            }
        }"""

    def execute(self, data: list):

        """
        This script compensates skew in the print by adjusting the X and Y parameters in each line of the gcode.
        params:
            xy_calc_type:   by error or by tangent
            xy_x_error:     the amount of skew in the X
            xy_y_length:    the Y base line length where the X skew was measured
            xy_tangent:     the user calculated tanget of 'X Error/Y Base Length'
            yz_calc_type:   by error or by tangent
            yz_y_error:     the amount of skew in the Y
            yz_z_hgt:       the Z base line height where the Y skew was measured
            yz_tangent:     the user calculated tanget of 'Y Error/Z Base Height'
            xz_calc_type:   by error or by tangent
            xz_x_error:     the amount of skew in the X
            xz_z_hgt:       the Z base line height where the X skew was measured
            xz_tangent:     the user calculated tanget of 'X Error/Z Base Height'
            cur_x, cur_y, cur_z:  the current axis values from the gcode
            x_input, y_input, z_input: values used when X, Y, Z are != None
            x_out, Y_out, z_out: the replacement values to fix the skew
        """

        # Exit if the post processor is not enabled
        if not bool(self.getSettingValueByKey("enable_print_skew_comp")):
            data[0] += ";    [Print Skew Compensation] not enabled\n"
            return data

        # Exit if the gcode has already been post-processed
        if ";POSTPROCESSED" in data[0]:
            return data

        # Notify the user that this script should run last
        scripts = Application.getInstance().getGlobalContainerStack().getMetaDataEntry("post_processing_scripts")
        scripts = scripts.replace("\\", "")
        script_list = scripts.split("\n")
        for ndex, script in enumerate(script_list):
            script_list[ndex] = script.split("]")[0]
            script_list[ndex] = script_list[ndex].replace("[", "")
        for ndex, script in enumerate(script_list):
            if "PrintSkewCompensation" in script and ndex < len(script_list) - 1:
                Message(title = "[Print Skew Compensation]", text = "Should usually be last in the Post-Processor list (in case some other script adds moves to the gcode).").show()
                break

        xy_calc_type = self.getSettingValueByKey("xy_calc_type")
        yz_calc_type = self.getSettingValueByKey("yz_calc_type")
        xz_calc_type = self.getSettingValueByKey("xz_calc_type")

        if xy_calc_type == "xytype_len":
            xy_x_error = self.getSettingValueByKey("xy_x_error")
            xy_y_length = self.getSettingValueByKey("xy_y_length")
            xy_tangent = xy_x_error/xy_y_length
        else:
            xy_tangent = self.getSettingValueByKey("xy_tangent")

        if yz_calc_type == "yztype_len":
            yz_y_error = self.getSettingValueByKey("yz_y_error")
            yz_z_hgt = self.getSettingValueByKey("yz_z_hgt")
            yz_tangent = yz_y_error/yz_z_hgt
        else:
            yz_tangent = self.getSettingValueByKey("yz_tangent")

        if xz_calc_type == "xztype_len":
            xz_x_error = self.getSettingValueByKey("xz_x_error")
            xz_z_hgt = self.getSettingValueByKey("xz_z_hgt")
            xz_tangent = xz_x_error/xz_z_hgt
        else:
            xz_tangent = self.getSettingValueByKey("xz_tangent")

        # z_input is cummulative
        z_input = 0
        for layer_index, layer in enumerate(data):
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

                    if cur_x != None:
                        x_input = cur_x
                    if cur_y != None:
                        y_input = cur_y
                    if cur_z != None:
                        z_input = cur_z

                    # Calculate the skew compensation
                    x_out = round(x_input-y_input*xy_tangent,3)
                    x_out = round(x_out-z_input*xz_tangent,3)
                    y_out = round(y_input-z_input*yz_tangent,3)
                    z_out = z_input

                    # If the first layer hasn't started then jump out
                    if layer_index < 2:
                        continue

                    # Alter the current line
                    if cur_x != None:
                        lines[index] = lines[index].replace(f"X{cur_x}", f"X{x_out}")
                    if cur_y != None:
                        lines[index] = lines[index].replace(f"Y{cur_y}", f"Y{y_out}")
                    if cur_z != None:
                        lines[index] = lines[index].replace(f"Z{cur_z}", f"Z{z_out}")

            data[layer_index] = "\n".join(lines)
        return data
