"""
    Authored By: GregValiant (Greg Foresi) September of 2026 (concept by: 'EdoFro')
    ~ This script will print the ";LAYER:0's" (and any raft layers) of each model first (ala 'All-at-Once' mode).  Then it will revert to One-at-a-Time print sequence to finish each print.
    ~ Layers will be moved around and re-ordered.  That might confuse other post processors that are using the Layer Count.

    Rules:
    * This script must run before 'DisplayInfoOnLCD'.  There might be other conflicts as well.  Open and check your G-Code.
    * This script requires "Print Sequence" == "One at a Time"
    * If both "Raft" and "Pause at Height" are enabled - the script exits as the layer numbers don't work out.
"""

from UM.Application import Application
from ..Script import Script
from UM.Message import Message
from UM.Logger import Logger
import time
from UM.Qt.Duration import DurationFormat
import re

class BaseLayersFirst(Script):
    def getSettingDataString(self):
        return """{
            "name": "Base Layers First (OneAtATime)",
            "key": "BaseLayersFirst",
            "metadata": {},
            "version": 2,
            "settings": {
                "base_layers_first_enabled":
                {
                    "label": "Enable script",
                    "description": "Enables the script so it will run.  This script will move all the individual 'Initial Layers' (and any raft layers) into a single layer that will print first.  That allows you to see if all the prints start properly. Please note: #1. 'One-at-a-Time' is required.  #2. You cannot use 'Raft' AND 'PauseAtHeight'.  Either one or the other will work.  Double-check the G-Code when using PauseAtHeight or FilamentChange.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                }
            }
        }"""

    def execute(self, data):
        # Exit if the script is not enabled
        script_is_enabled = bool(self.getSettingValueByKey("base_layers_first_enabled"))
        if not script_is_enabled:
            data[0] += ";  [Base Layers First] Not enabled\n"
            Logger.info(f"\n[Base Layers First] Not enabled\n")
            return data
        # Exit if the gcode has already been post-processed
        if ";POSTPROCESSED" in data[0]:
            return data

        self.global_stack = Application.getInstance().getGlobalContainerStack()
        extruder = self.global_stack.extruderList

        # Get the Print Sequence from Cura
        if self.global_stack.getProperty("print_sequence", "value") == "one_at_a_time":
            one_at_a_time = True
        else:
            one_at_a_time = False

        # Exit logic: If "one at a time" is not enabled then exit the script.
        if not one_at_a_time:
            Message(title = "⚠️ [Base Layers First] Did NOT run ⚠️", text = "Print Sequence must be set to 'One at a Time'.").show()
            Logger.info("[Base Layers First] Did NOT run. Print Sequence must be set to 'One at a Time'.")
            data[0] += ";  [Base Layers First] Did not run.  Print Sequence must be 'One At A Time'.\n"
            return data

        # Initialize some variables
        if self.global_stack.getProperty("adhesion_type", "value") == "raft":
            raft_enabled = True
        else:
            raft_enabled = False

        speed_z_hop = int(self.global_stack.getProperty("speed_z_hop", "value")) * 60
        self.z_hops_enabled = bool(extruder[0].getProperty("retraction_hop_enabled", "value"))
        self.speed_travel = int(extruder[0].getProperty("speed_travel", "value")) * 60
        self.matl_print_temp_0 = extruder[0].getProperty("material_print_temperature_layer_0", "value")
        self.matl_print_temp = extruder[0].getProperty("material_print_temperature", "value")
        self.matl_bed_temp_0 = self.global_stack.getProperty("material_bed_temperature_layer_0", "value")
        self.matl_bed_temp = self.global_stack.getProperty("material_bed_temperature", "value")
        self.layer_0_total_time = 0.0
        self.new_travel_list = []
        absolute_extrusion = not bool(self.global_stack.getProperty("relative_extrusion", "value"))

        # A check to insure the user knows that 'Raft' combined with 'PauseAtHeight' doesn't work.  The script will exit.
        criteria = "pause_at_height"
        if raft_enabled:
            if self._PostProcessorOrderWarning(criteria):
                Message(title = "⚠️[Base Layers First]", text = "Cannot be used when both 'Raft' and 'PauseAtHeight' are enabled. The script did not run.").show()
                return data

        # A check to insure that the user knows 'Base Layers First' should run before 'DisplayInfoOnLCD'
        criteria = "display_info"
        if self._PostProcessorOrderWarning(criteria):
            Message(title = "[Base Layers First]", text = "Should run BEFORE 'DisplayInfoOnLCD' to insure the layer numbers turn out correctly. Check the preview of the Gcode File to insure it is correct.").show()

        # If in Absolute Extrusion mode - enter 'G92 E' lines at the beginning of each layer to insure the E will be synced prior to shuffling the layers
        if absolute_extrusion:
            data = self._AdjustELocations(data)

        # If adaptive layers are enabled then the Layer:1 Height must be checked to get it right
        layer_1_height = self._RealLayer1Height(data)
        self.init_layer_height_line = self._format_string(f"G1 F{speed_z_hop} Z{layer_1_height}; FpF Move Z")

        # Get the "from" location for the initial extrusion of each layer:0.
        data = self._ExtrudeFromLocation(data)

        # If rafts are enabled the travel between prints must be ortho so any intervening rafts doesn't get hit.
        if raft_enabled:
            data = self._OrthogonalTravel(data)

        # Strip the temperature lines as they get disordered by the layer shuffling
        data = self._StripTemperatureLines(data)

        # Determine the time it takes for each layer to print and add 'TIME_DELTA' to each layer.  Calculate the 'layer_0_total_time' for the new combined layer.
        data = self._CalculateTimeDeltas(data)

        # Add the rest of the layer time deltas.
        data = self._RewriteTimeElapsedLines(data)

        # Put together the new LAYER:0 comprised of all raft layers and all layer 0's
        layer_0_result = self._AssembleLayer0String(data)
        layer_0_str = layer_0_result[0]
        data = layer_0_result[1]

        # Go through the new combined LAYER:0 and remove any extraneous Layer:0 lines.
        data = self._FixTimes(data, layer_0_str)

        # Set the temperatures for Layer:0 to 'Initial Layer Print' and 'Initial Layer Bed' Temps and then reset to 'Print/Bed Temps' for Layer:1
        layer_0_str = self._SetTemperatures(layer_0_str)

        # Remove the delta time from the layer:0 elapsed time line
        data[2] = self._FixTimeLine(data[2])

        # Add the extra travel lines between prints
        data = self._AddTravelLines(data)

        # Re-number the layers to so the Cura preview will be in 'One-at-a-Time' mode.
        data = self._RenumberLayers(data)

        # A message regarding the print_time of the new combined layer_0.
        c_minutes, c_seconds = divmod(self.layer_0_total_time, 60)
        Message(title = "[Base Layers First]", text = f"The new 'Combined Initial Layer' will take {round(c_minutes)}min {round(c_seconds)}sec to print.").show()
        return data

    def _PostProcessorOrderWarning(self, criteria):
        """
        1. This puts up a reminder message for the user that 'Base Layers First' needs to run before 'Display Info On LCD'.
        2. Having both 'Raft' and 'PauseAtHeight' enabled is not allowed.
        """
        pp_data = ""
        scripts_list = Application.getInstance().getGlobalContainerStack().getMetaDataEntry("post_processing_scripts")
        for script_str in scripts_list.split("\n"):
            script_str = script_str.replace(r"\\\n", "\n;  ").replace("\n;  \n;  ", "\n")
            pp_data += str(script_str)
        pp_list = pp_data.split("\n")
        display_info_index = len(pp_list)
        base_layers_first_index = -1
        if criteria == "display_info":
            try:
                for index, post_proc in enumerate(pp_list):
                    if "[DisplayInfoOnLCD]" in post_proc:
                        display_info_index = index
                    if "[BaseLayersFirst]" in post_proc:
                        base_layers_first_index = index
                    if display_info_index < base_layers_first_index in post_proc:
                        Message(title = "[Base Layers First]", text = "The script ran - BUT - Any removed/re-ordered layers will confuse 'Display Info on LCD'.  'Base Layers First' really needs to run before 'DisplayInfoOnLCD'.").show()
            except:
                IndexError, ValueError
            if display_info_index < base_layers_first_index:
                return True
            else:
                return False
        elif criteria == "pause_at_height":
            try:
                for index, post_proc in enumerate(pp_list):
                    if "enable_pause_at_height = True" in post_proc:
                        return True
            except:
                IndexError, ValueError
            return False

    def _AdjustELocations(self, alt_data):
        # This accounts for the shuffling of the Initial Layer E values when in Absolute Extrusion mode.
        # Pad the list so the e_list indices match the layers in data
        e_list = ["G92 E0", "G92 E0", "G92 E0"]
        cur_e_string = "G92 E0"
        for index, layer in enumerate(alt_data):
            if index < 2:
                continue
            lines = layer.split("\n")
            for line in lines:
                if line.startswith("G1 ") and " E" in line:
                    if self.getValue(line, "E") is not None:
                        cur_e_value = self.getValue(line, "E")
                        cur_e_string = self._format_string(f"G92 E{cur_e_value}; FpF Set E")
            e_list.append(cur_e_string)
        # Make the insertions
        for index, layer in enumerate(alt_data):
            if index < 2:
                continue
            if index > len(e_list):
                break
            if ";LAYER:" in alt_data[index]:
                lines = layer.split("\n")
                lines.insert(2, e_list[index])
                alt_data[index] = "\n".join(lines)
        return alt_data

    def _RealLayer1Height(self, alt_data):
        # This gets the actual Layer:1 height whether or not Adaptive Layers is enabled
        layer_1_height = self.global_stack.getProperty("layer_height", "value") + self.global_stack.getProperty("layer_height_0", "value")
        for index, layer in enumerate(alt_data):
            if not self.z_hops_enabled:
                if ";LAYER:0" in layer:
                    lines = layer.split("\n")
                    for line in lines:
                        if " Z" in line:
                            layer_1_height = self.getValue(line, "Z")
            else:
                if ";LAYER:1\n" in layer:
                        lines = layer.split("\n")
                        for line in lines:
                            if " Z" in line:
                                layer_1_height = self.getValue(line, "Z")
                                break
        return layer_1_height

    def _ExtrudeFromLocation(self, alt_data):
        # The 'extrude from' line of the first-extrusion-of-a-layer is before the layer change and must be copied to the beginning of the next layer so it still relates to the 'extrude to' line after the layers are shuffled.
        prev_x = 0.0
        prev_y = 0.0
        new_travel_line = ""
        for index, layer in enumerate(alt_data):
            if ";LAYER:0" in layer:
                lines = layer.split("\n")
                lines.reverse()
                for line in lines:
                    if line.startswith("G0 ") and " X" in line and " Y" in line:
                        prev_x = self.getValue(line, "X")
                        prev_y = self.getValue(line, "Y")
                        break
                new_travel_line = self._format_string(f"G0 F{self.speed_travel} X{prev_x} Y{prev_y}; FpF Travel")
                self.new_travel_list.append(new_travel_line)
        return alt_data

    def _OrthogonalTravel(self, alt_data):
        # If rafts are enabled then it is possible that a 3 axis direct line travel that drops in the Z could smack the nozzle into a finished raft print. This splits the travel into a separate XY move followed by the Z move.
        for index, layer in enumerate(alt_data):
            if index <= 2:
                continue
            lines = layer.split("\n")
            for ddex, line in enumerate(lines):
                if line.startswith("G0 ") and " X" in line and " Y" in line and " Z" in line:
                    xy_move = line.split(" Z")[0]
                    z_move = line.split(" Z")[1].split()[0]
                    lines[ddex] = self._format_string(f"{xy_move}; FpF XY Ortho\nG0 Z{z_move}; FpF Z Ortho")
                    break
            alt_data[index] = "\n".join(lines)
        return alt_data

    def _StripTemperatureLines(self, alt_data):
        # The 'initial layer' has been modified and the 'Init Bed' temps and 'Init Print' temps need to be reinserted.
        indices_to_delete = []
        for index, layer in enumerate(alt_data):
            if index < 2 or index >= len(alt_data)-1:
                continue
            lines = layer.split("\n")
            for ldex, line in enumerate(lines):
                try:
                    if lines[ldex].startswith("M104 S") or lines[ldex].startswith("M140"):
                        indices_to_delete.append(ldex)
                    if ";LAYER_COUNT:" in line:
                        lines[ldex] = self._format_string(f"M104 S{round(self.matl_print_temp)}; FpF Print Temp\n") + line
                except:
                    IndexError
            # Step backwards through the list and delete the temperature lines to avoid skips
            if indices_to_delete != []:
                for ddex in sorted(indices_to_delete, reverse=True):
                    del lines[ddex]
            indices_to_delete = []
            alt_data[index] = "\n".join(lines)
        return alt_data

    def _CalculateTimeDeltas(self, alt_data):
        # Add TIME_DELTA text to the TIME_ELAPSED lines to indicate the 'Print Time' of each individual layer
        temp_string = ""
        current_time = 0.0
        prev_time = 0.0
        for index, layer in enumerate(alt_data):
            if ";TIME_ELAPSED:" in layer:
                current_time = float(layer.split(";TIME_ELAPSED:")[1].split()[0])
                delta_time = current_time - prev_time
                replacement_string = f";TIME_ELAPSED:{current_time} TIME_DELTA:{delta_time}\n"
                alt_data[index] = re.sub(r";TIME_ELAPSED:(\d.*)\n", replacement_string, layer)
                prev_time = current_time
        for index, layer in enumerate(alt_data):
            if ";LAYER:0" in layer or ";LAYER:-" in layer:
                temp_string += alt_data[index]
        # The 'temp string' will later be the layer_0_str but for now, we just need it's new delta time.
        lines = temp_string.split("\n")
        for line in lines:
            if "TIME_DELTA" in line:
                temp_time = float(line.split("TIME_DELTA:")[1].split()[0])
                self.layer_0_total_time += round(temp_time,2)
        return alt_data

    def _RewriteTimeElapsedLines(self, alt_data):
        # After the layers are shuffled, recalculate the TIME_ELAPSED lines to fit the new reality
        layer_0_list = alt_data[2].split("\n")
        for index, layer in enumerate(layer_0_list):
            if ";TIME_ELAPSED:" in layer:
                layer_0_list[index] = f";TIME_ELAPSED:{self.layer_0_total_time:.2f} TIME_DELTA:{self.layer_0_total_time:.2f}"
                alt_data[2] = "\n".join(layer_0_list)
                break
        prev_layer_time = self.layer_0_total_time
        for index, layer in enumerate(alt_data):
            if 2 < index >= len(alt_data)-1:
                continue
            if ";TIME_ELAPSED:" in layer:
                lines = layer.split("\n")
                for tdel, line in enumerate(lines):
                    if ";TIME_ELAPSED:" in line:
                        current_layer_time = float(layer.split(";TIME_ELAPSED:")[1].split()[0])
                        delta_time = current_layer_time - prev_layer_time
                        prev_layer_time = current_layer_time
                alt_data[index] = "\n".join(lines)
        return alt_data

    def _AssembleLayer0String(self, alt_data):
        # Pull any raft layers and the layer:0's and morph them into a single layer that will print first.
        layer_0_str = ""
        self.layer_0_index_list = []
        for index, layer in enumerate(alt_data):
            if ";LAYER:-" in layer or ";LAYER:0" in layer:
                layer_0_str += alt_data[index]
                self.layer_0_index_list.append(index)
        # Sort in descending order to delete from back to front
        for i in sorted(self.layer_0_index_list, reverse=True):
            del alt_data[i]
        # Remove all the existing TIME_ELAPSED lines from the new layer:0 and replace with a single line with the new print time.
        layer_0_list = layer_0_str.split("\n")
        for index, line in enumerate(layer_0_list):
            if ";TIME_ELAPSED:" in line:
                layer_0_list.pop(index)
        new_time_str = f";TIME_ELAPSED:{self.layer_0_total_time:.2f} TIME_DELTA:{self.layer_0_total_time:.2f}\n"
        layer_0_str = "\n".join(layer_0_list)
        layer_0_str += new_time_str
        alt_data.insert(2, layer_0_str)
        return layer_0_str, alt_data

    def _FixTimes(self, alt_data, layer_0_str):
        # Go through the new Initial Layer and fix all the other Time Elapsed lines
        start_now = False
        layer_0_list = layer_0_str.split("\n")
        for ldex, line in enumerate(layer_0_list):
            if (";LAYER:0" in line or ";LAYER:-" in line) and start_now:
                layer_0_list.pop(ldex)
            if ";LAYER:0" in line or ";LAYER:-" in line:
                start_now = True
        running_time = self.layer_0_total_time
        for index, layer in enumerate(alt_data):
            if index < 3:
                continue
            lines = layer.split("\n")
            for tdex, line in enumerate(lines):
                if ";TIME_ELAPSED:" in line:
                    delta_time = float(line.split("TIME_DELTA:")[1].split()[0].strip())
                    running_time += delta_time
                    new_time_line = f";TIME_ELAPSED:{running_time:.2f}"
                    lines[tdex] = new_time_line
                    alt_data[index] = "\n".join(lines)
        return alt_data

    def _AddTravelLines(self, alt_data):
        # Insert the lateral move line and the vertical move line before the start of each 'lAYER:1'
        count = 0
        for num, layer in enumerate(alt_data):
            if ";LAYER:1\n" in layer:
                lines = alt_data[num-1].split("\n")
                lines.insert(len(lines)-2, f"{self.new_travel_list[count]}\n{self.init_layer_height_line}")
                count += 1
                alt_data[num-1] = "\n".join(lines)
        return alt_data

    def _RenumberLayers(self, alt_data):
        # Renumber so the Cura preview is correct when the Gcode is opened to preview
        consecutive_lay_num = 0
        for num, layer in enumerate(alt_data):
            lines = layer.split("\n")
            for index, line in enumerate(lines):
                if ";LAYER:" in line:
                    lines[index] = f";LAYER:{consecutive_lay_num}"
                    consecutive_lay_num += 1
            alt_data[num] = "\n".join(lines)
        return alt_data

    def _SetTemperatures(self, layer_0_str):
        # The temperatures are re-inserted here
        layer_0_list = layer_0_str.split("\n")
        insertion_string = self._format_string(f"M104 S{round(self.matl_print_temp_0)}; FpF Print Temp\nM140 S{round(self.matl_bed_temp_0)}; FpF Bed Temp")
        layer_0_list.insert(1, insertion_string)
        layer_0_list.insert(len(layer_0_list)-2, self._format_string(f"M104 S{round(self.matl_print_temp)};FpF Print Temp\nM140 S{round(self.matl_bed_temp)} ; FpF Bed Temp"))
        layer_0_str = "\n".join(layer_0_list)
        return layer_0_str

    def _FixTimeLine(self, lay_0):
        # Final fix is the Time Elapsed line at the end of new lAYER:0  It will include the delta times of the included layers.
        lines = lay_0.split("\n")
        for index, line in enumerate(lines):
            if index < 3:
                continue
            if ";LAYER:" in line:
                lines.pop(index)
            if "TIME_DELTA:" in line:
                lines[index] = line.split("TIME_DELTA:")[0].strip()
        lay_0 = "\n".join(lines)
        return lay_0

    def _format_string(self, any_gcode_str: str):
        # I like when things are neat and lined up.  Makes things easier to read.
        temp_lines = any_gcode_str.split("\n")
        gap_len = 0
        for temp_line in temp_lines:
            if ";" in temp_line and not temp_line.startswith(";"):
                if gap_len - len(temp_line.split(";")[0]) + 1 < 0:
                    gap_len = len(temp_line.split(";")[0]) + 1
        if gap_len < 32: gap_len = 32
        for temp_index, temp_line in enumerate(temp_lines):
            if ";" in temp_line and not temp_line.startswith(";"):
                temp_lines[temp_index] = temp_line.replace(temp_line.split(";")[0], temp_line.split(";")[0] + str(
                    " " * (gap_len - len(temp_line.split(";")[0]))), 1)
            # This formats lines that are commented out but contain additional comments Ex:  ;M420 ; leveling mesh
            elif temp_line.startswith(";") and ";" in temp_line[1:]:
                temp_lines[temp_index] = temp_line[1:].replace(temp_line[1:].split(";")[0], ";" + temp_line[1:].split(";")[0] + str(" " * (gap_len - 1 - len(temp_line[1:].split(";")[0]))), 1)
        any_gcode_str = "\n".join(temp_lines)
        return any_gcode_str