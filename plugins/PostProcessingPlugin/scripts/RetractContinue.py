"""
    Rewrite by GregValiant (Greg Foresi) June of 2025
    This script splits retractions into an "Initial Retraction" and "Retraction during travel" so that the remainder of the retraction occurs in any following travel moves.
    Retractions must be enabled in Cura and Cura's rules for when a retraction occurs remain in place.

    Compatibility:
        NOTE - The retraction settings for a multi-extruder printer are always taken from Extruder 1 (T0).
        There is support for:
            Absolute and Relative Extrusion
            Adaptive Layers

    Incompatibility:
        "One at a Time" mode is not supported
        "Firmware Retraction" is not supported

    Please Note:
        This is a slow running post processor as it must check the distances of all travel moves in the range of layers.
"""

from UM.Application import Application
from ..Script import Script
import re
from UM.Message import Message
import math
from UM.Logger import Logger
from UM.i18n import i18nCatalog

catalog = i18nCatalog("cura")

class RetractContinue(Script):
    def __init__(self):
        self.script_key = "RetractContinue"
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Retract Continue",
            "key": "RetractContinue",
            "metadata": {},
            "version": 2,
            "settings": {
                "retract_continue_enabled": {
                    "label": "Enable 'Retract Continue'",
                    "description": "Enables the script so it will run.  The script will split retractions so that part of the retraction occurs during the follow-up travel moves.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                },
                "start_layer": {
                    "label": "Start Layer",
                    "description": "Layer number to start the changes at.  Use the Cura preview layer numbers.  The changes will start at the start of the layer.",
                    "unit": "Lay# ",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": "1",
                    "enabled": "retract_continue_enabled"
                },
                "end_layer": {
                    "label": "End Layer",
                    "description": "Enter '-1' to indicate the top layer, or enter a specific Layer number from the Cura preview.  The changes will end at the end of this layer.",
                    "unit": "Lay# ",
                    "type": "int",
                    "default_value": -1,
                    "minimum_value": "-1",
                    "enabled": "retract_continue_enabled"
                },
                "initial_retract_percentage": {
                    "label": "Initial Retract Percentage",
                    "description": "Each retraction line in the layer range will be altered to this % of the Cura 'Retraction Distance' with the remaining percentage being spread across the travel moves.",
                    "unit": "%  ",
                    "type": "int",
                    "default_value": 70,
                    "minimum_value": 10,
                    "maximum_value": 100,
                    "enabled": "retract_continue_enabled"
                }
            }
        }"""

    def execute(self, data):
        """
        The script will parse the gcode and adjust retractions to provide an "initial retraction" and a "continuing retraction" which is spread across the following travel moves.
        """
        # Define the global_stack to access the Cura settings
        global_stack = Application.getInstance().getGlobalContainerStack()

        # Exit if the script is not enabled
        if not self.getSettingValueByKey("retract_continue_enabled"):
            data[0] += ";  [Retract Continue] Not enabled\n"
            Logger.log("i", "[Retract Continue] Not enabled")
            return data

        # Exit if the gcode has already been post-processed
        if ";POSTPROCESSED" in data[0]:
            return data

        # Exit if 'Firmware Retraction' is enabled because the amount of retraction is unknown.
        if bool(global_stack.getProperty("machine_firmware_retract", "value")):
            Message(
                title = "[Retract Continue]",
                text = "Is not compatible with 'Firmware Retraction'.").show()
            data[0] += ";  [Retract Continue] did not run because it is not compatible with Firmware Retraction.\n"
            return data

        # Exit if 'Print Sequence' is 'One-at-a-Time'.
        if global_stack.getProperty("print_sequence", "value") == "one_at_a_time":
            Message(
                title = "[Retract Continue]",
                text = "Is not compatible with Print Sequence = 'One at a Time'.").show()
            data[0] += ";  [Retract Continue] did not run because it is not compatible with Print Sequence = 'One at a Time'.\n"
            return data

        # Notify the user that this script should run last
        post_processing_plugin = Application.getInstance().getPluginRegistry().getPluginObject("PostProcessingPlugin")
        active_script_keys = post_processing_plugin.scriptList
        script_index = active_script_keys.index(self.script_key)
        if script_index < len(active_script_keys) - 1:
            Message(
                    text="'Retract Continue' Should be last in the Post-Processor list. It will run if it's not last, " \
                    "but any following post-processors might have a unexpected effect because of the changes made by 'Retract Continue'.",
                    title=catalog.i18n("[Retract Continue]"),
                    message_type=Message.MessageType.WARNING).show()

        # Define some variables
        extruder = global_stack.extruderList
        retraction_enabled = extruder[0].getProperty("retraction_enable", "value")
        self._retraction_amt = extruder[0].getProperty("retraction_amount", "value")
        initial_retract_adjustment = self.getSettingValueByKey("initial_retract_percentage") / 100
        retract_text = f"; Retract {self.getSettingValueByKey("initial_retract_percentage")}%"
        self.wipe_amt = self._retraction_amt * (1 - initial_retract_adjustment)
        self.init_retract_amt = self._retraction_amt - self.wipe_amt
        self._absolute_extrusion = not bool(global_stack.getProperty("relative_extrusion", "value"))
        filament_dia = extruder[0].getProperty("material_diameter", "value")
        extra_prime_vol = extruder[0].getProperty("retraction_extra_prime_amount", "value")
        extra_prime_dist = extra_prime_vol / (math.pi * (filament_dia / 2)**2)
        layer_list = []
        index_list = []
        end_index = None

        start_layer = self.getSettingValueByKey("start_layer")
        end_layer = self.getSettingValueByKey("end_layer")

        # Get the indexes for the start and end layers
        start_index = 2
        for num in range(1, len(data) - 1):
            if ";LAYER:" + str(start_layer - 1) + "\n" in data[num]:
                start_index = num
                break
        if end_layer == -1:
            if retraction_enabled:
                end_index = len(data) - 2
            else:
                end_index = len(data) - 1
        elif end_layer != -1:
            for num in range(1, len(data) - 1):
                if ";LAYER:" + str(end_layer) + "\n" in data[num]:
                    end_index = num
                    break
        if end_index == None:
            end_index = len(data) -1
        for num in range(start_index, end_index):
            index_list.append(num)

        # Initialize variables
        self._cur_x = 0.0
        self._cur_y = 0.0
        self._prev_x = 0.0
        self._prev_y = 0.0
        self._cur_e = 0.0
        self._prev_e = 0.0
        self._cur_z = float(global_stack.getProperty("layer_height_0", "value"))
        self._is_retracted = False
        cmd_list = ["G0 ", "G1 ", "G2 ", "G3 "]

        # Track the axes up to the beginning of the Start Layer
        for qnum in range(1, start_index):
            self._track_all_axes(data, cmd_list, qnum)

        # Start looking for insertion points
        for ldex in range(start_index, end_index):
            # If the layer is not a 'Layer of Interest' then just track the axes.
            if ldex not in index_list:
                self._track_all_axes(data, cmd_list, ldex)
                continue
            lines = data[ldex].split("\n")
            for index, line in enumerate(lines):
                # Break down the lines to retrieve information
                if not line.startswith(";") and ";" in line:
                    line = line.split(";")[0]
                if line[0:3] in cmd_list:
                    if self.getValue(line, "X") is not None:
                        self._prev_x = self._cur_x
                        self._cur_x = self.getValue(line, "X")
                    if self.getValue(line, "Y") is not None:
                        self._prev_y = self._cur_y
                        self._cur_y = self.getValue(line, "Y")
                    if self.getValue(line, "E") is not None:
                        self._cur_e = self.getValue(line, "E")
                        if self._absolute_extrusion:
                            if self._cur_e < self._prev_e:
                                self._is_retracted = True
                            elif self._cur_e >= self._prev_e:
                                self._is_retracted = False
                        elif not self._absolute_extrusion:
                            if self._cur_e < 0:
                                self._is_retracted = True
                            elif self._cur_e > 0:
                                self._is_retracted = False
                if line.startswith("G92 "):
                    self._prev_e = self._cur_e
                    self._cur_e = round(self.getValue(line, "E"), 5)
                    continue
                if line.startswith("M82"):
                    self._absolute_extrusion = True
                    continue
                if line.startswith("M83"):
                    self._absolute_extrusion = False
                    continue
                if not "X" in line and not "Y" in line and re.search(r"G1 F(\d+|\d.+) E(-?\d+|\d.+)", line) is not None:
                    distance_lists = self._total_travel_length(index, lines)
                    dist_list = distance_lists[0]
                    total_travel_dist = round(distance_lists[1],3)
                    if total_travel_dist == 0:
                        self._prev_e = self._cur_e
                        dist_list = []
                        continue
                    else:
                        if self._absolute_extrusion:
                            e_val_new = round(self._cur_e + self.wipe_amt, 5)
                            lines[index] = re.sub(f" E(-?\d+\d.+)", f" E{e_val_new}", lines[index])
                            lines[index] += f"{' ' * (39 - len(lines[index]))} {retract_text}" if not "Retract" in lines[index] else f" {self.getSettingValueByKey("initial_retract_percentage")}%"
                            lines[index] = lines[index] + "\n;WIPE_START" 
                            wdex = index + 1
                            for wdist in dist_list:
                                while lines[wdex].startswith(";") or (lines[wdex].startswith("G1 F") and " Z" in lines[wdex]):
                                    wdex += 1
                                if not " E" in lines[wdex]:
                                    lines[wdex] = re.sub("G0 ", "G1 ", lines[wdex])
                                    partial_e = e_val_new - ((wdist  / total_travel_dist) * self.wipe_amt)
                                    lines[wdex] += f" E{round(partial_e, 5)}"
                                    e_val_new -= round(((wdist  / total_travel_dist) * self.wipe_amt), 5)
                                    wdex += 1
                            lines[wdex] = ";WIPE_END\n" + lines[wdex]
                        else:
                            e_val_new = round(self.init_retract_amt,5)
                            lines[index] = re.sub(f"E{self._cur_e}", f"E-{e_val_new}", lines[index])
                            lines[index] += f"{' ' * (39 - len(lines[index]))} {retract_text}" if not "Retract" in lines[index] else f" {self.getSettingValueByKey("initial_retract_percentage")}%"
                            lines[index] = lines[index] + "\n;WIPE_START" 
                            wdex = index + 1
                            for wdist in dist_list:
                                while lines[wdex].startswith(";") or (lines[wdex].startswith("G1 F") and " Z" in lines[wdex]):
                                    wdex += 1
                                if not " E" in lines[wdex]:
                                    lines[wdex] = re.sub("G0 ", "G1 ", lines[wdex])
                                    partial_e = ((wdist  / total_travel_dist) * self.wipe_amt)
                                    lines[wdex] += f" E-{round(partial_e, 5)}"
                                    wdex += 1
                            lines[wdex] = ";WIPE_END\n" + lines[wdex]
            data[ldex] = "\n".join(lines)
        return data

    def _total_travel_length(self, l_index: int, lines: str) -> int:
        """
        Get the length of each travel move.
        Get total distance of the moves.
        For each travel move; get the percentage of the overall travel distance
        Each travel move add an E value equal to the % of the overall travel distance.
        """
        g_num = l_index + 1
        travel_total = 0.0
        dist_list = []
        while lines[g_num].startswith(";") or (lines[g_num].startswith("G1 F") and " Z" in lines[g_num]):
            g_num += 1
        # Total the lengths of each move and compare them to the Minimum Distance for a Z-hop to occur
        while lines[g_num].startswith("G0 "):
            if self.getValue(lines[g_num], "X"):
                self._cur_x = self.getValue(lines[g_num], "X")
            if self.getValue(lines[g_num], "Y"):
                self._cur_y = self.getValue(lines[g_num], "Y")
            move_length = self._get_distance()
            dist_list.append(round(move_length,3))
            travel_total += round(move_length,3)
            self._prev_x = self._cur_x
            self._prev_y = self._cur_y
            g_num += 1
            if g_num == len(lines):
                break
        return dist_list, travel_total

    def _get_distance(self) -> float:
        """
        This function gets the distance from the previous location to the current location.
        """
        try:
            dist = math.sqrt((self._prev_x - self._cur_x)**2 + (self._prev_y - self._cur_y)**2)
        except ValueError:
            return 0
        return dist

    def _track_all_axes(self, data: str, cmd_list: str, cont_index: int) -> str:
        """
        This function tracks the XYZE locations

        """
        lines = data[cont_index].split("\n")
        for line in lines:
            # Get the XYZ values from movement commands
            if not line.startswith(";") and ";" in line:
                line = line.split(";")[0]
            if line[0:3] in cmd_list:
                if " X" in line and self.getValue(line, "X"):
                    self._prev_x = self._cur_x
                    self._cur_x = self.getValue(line, "X")
                if " Y" in line and self.getValue(line, "Y"):
                    self._prev_y = self._cur_y
                    self._cur_y = self.getValue(line, "Y")
                if " Z" in line and self.getValue(line, "Z"):
                    self._cur_z = self.getValue(line, "Z")

            # Check whether retractions have occured and track the E location
            if not self._absolute_extrusion:
                if line.startswith("G1 ") and " X" in line and " Y" in line and " E" in line:
                    self._is_retracted = False
                    self._cur_e = self.getValue(line, "E")
                elif line.startswith("G1 ") and " F" in line and " E" in line and not " X" in line and not " Y" in line:
                    if self.getValue(line, "E"):
                        self._cur_e = self.getValue(line, "E")
            elif self._absolute_extrusion:
                if self._cur_e < 0:
                    self._is_retracted = True
                    self._cur_e = 0
        self._prev_e = self._cur_e
        return None
