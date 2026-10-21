"""
    By GregValiant (Greg Foresi) September of 2026 (concept by: 'EdoFro')
    ~ This script will print the ";LAYER:0's" of each model first, and then revert to One-at-a-Time print sequence.
    ~ When using this with other scripts, this script must run before 'DisplayInfoOnLCD' or the M117 and M118 lines inserted by DisplayInfo will be incorrect.
    ~ This script requires "Print Sequence" == "One at a Time"
    ~ If both "Raft" and "Pause at Height" are enabled - the script exits as the layer numbers don't work out.
"""

from UM.Application import Application
from ..Script import Script
from UM.Message import Message
from UM.Logger import Logger
import time
from UM.Qt.Duration import DurationFormat
import re

class FootPrintsFirst(Script):
    def getSettingDataString(self):
        return """{
            "name": "Foot Prints First (OneAtATime)",
            "key": "FootPrintsFirst",
            "metadata": {},
            "version": 2,
            "settings": {
                "footprints_first_enabled": {
                    "label": "Enable script",
                    "description": "Enables the script so it will run.  This script will move all the individual 'Initial Layers' into a single layer that will print first.  That allows you to see if all the prints start OK. Please note: 'One-at-a-Time' is required.  You cannot use 'Raft' with 'PauseAtHeight'.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                }
            }
        }"""

    def execute(self, data):
        # Exit if the script is not enabled
        if not self.getSettingValueByKey("footprints_first_enabled"):
            data[0] += ";  [Foot Prints First] Not enabled\n"
            Logger.info("[Foot Prints First] Not enabled")
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
            Message(title = "⚠️⚠️ [Foot Prints First] Did NOT run ⚠️⚠️", text = "Print Sequence must be set to 'One at a Time'.").show()
            Logger.info("[Foot Prints First] Did NOT run. Print Sequence must be set to 'One at a Time'.")
            data[0] += ";  [Foot Prints First] Did not run.  Print Sequence must be 'One At A Time'.\n"
            return data

        # Initialize variables
        relative_extrusion = bool(self.global_stack.getProperty("relative_extrusion", "value"))
        if bool(extruder[0].getProperty("retraction_hop_enabled", "value")):
            self.z_hops_enabled = True
        else:
            self.z_hops_enabled = False

        if self.global_stack.getProperty("adhesion_type", "value") == "raft":
            raft_enabled = True
        else:
            raft_enabled = False

        speed_z_hop = int(self.global_stack.getProperty("speed_z_hop", "value")) * 60
        self.speed_travel = int(extruder[0].getProperty("speed_travel", "value")) * 60
        matl_print_temp_0 = extruder[0].getProperty("material_print_temperature_layer_0", "value")
        self.matl_print_temp = extruder[0].getProperty("material_print_temperature", "value")
        matl_bed_temp_0 = self.global_stack.getProperty("material_bed_temperature_layer_0", "value")
        matl_bed_temp = self.global_stack.getProperty("material_bed_temperature", "value")
        self.new_travel_list = []
        self.layer_0_index_list = []
        self.layer_0_total_time = 0.0

        # A check to insure the user knows that 'Raft' combined with 'PauseAtHeight' doesn't work.
        criteria = "pause_at_height"
        if raft_enabled:
            if self._PostProcessorOrderWarning(criteria):
                Message(title = "⚠️[FootprintsFirst]", text = "'FootprintsFirst' cannot be used when both 'Raft' and 'PauseAtHeight' are enabled. The script did not run.").show()
                return data
        #Logger.info(f">>>GREG 1:  raft = {raft_enabled}  criteria = {criteria}")
        # A check to insure that the user knows 'FootPrintsFirst' should run before 'DisplayInfoOnLCD'
        criteria = "display_info"
        if self._PostProcessorOrderWarning(criteria):
            Message(title = "⚠️[FootprintsFirst]", text = "'FootprintsFirst' should run BEFORE 'DisplayInfoOnLCD' to insure the layer numbers turn out correctly. Check the preview of the Gcode File to insure it is correct.").show()

        # If in Absolute Extrusion mode - enter 'G92 E' lines to insure the E is synced at the start of each layer.
        if not relative_extrusion:
            data = self._AdjustELocations(data)

        # If adaptive layers are enabled then the Layer:1 Height must be checked to get it right
        layer_1_height = self._RealLayer1Height(data)
        self.init_layer_height_line = f"G1 F{speed_z_hop} Z{layer_1_height}                ; FpF Move Z"

        # Get the "from" location for the initial extrusion of each layer:0 and add them to a list.
        data = self._ExtrudeFromLocation(data)

        # If rafts are enabled the travel between prints must be ortho so any intervening print doesn't get hit.
        if raft_enabled:
            data = self._OrthogonalTravel(data)

        # Strip the temperature lines as they get disordered by the layer shuffling
        data = self._StripTemperatureLines(data)

        # Determine the time it takes for each layer to print and add 'DELTA_TIME' to each layer
        data = self._AddLayerTimes(data)

        # Pull all the layer:0's from the gcode and concatenate them into a single layer.  This includes any Raft layers.
        layer_0_result = self._Layer0String(data)
        layer_0_str = layer_0_result[0]
        data = layer_0_result[1]

        # Skip the first LAYER:0 line but remove any other Layer:0 lines from the new initial layer.
        start_now = False
        layer_0_list = layer_0_str.split("\n")
        for ldex, line in enumerate(layer_0_list):
            if (";LAYER:0" in line or ";LAYER:-" in line) and start_now:
                layer_0_list.pop(ldex)
            if ";LAYER:0" in line or ";LAYER:-" in line:
                start_now = True

        # Set the temps for Layer:0 to 'Initial Layer Print/Initial Layer Bed' Temps and then reset to 'Print/Bed Temps' for Layer:1
        layer_0_list.insert(1, f"M104 S{round(matl_print_temp_0)}                   ; FpF Print Temp\nM140 S{round(matl_bed_temp_0)}                    ; FpF Bed Temp")
        layer_0_list.insert(len(layer_0_list)-2, f"M104 S{round(self.matl_print_temp)}                   ; FpF Print Temp\nM140 S{round(matl_bed_temp)}                    ; FpF Bed Temp")
        layer_0_str = "\n".join(layer_0_list)

        # Remove the TIME_ELAPSED lines from the new Layer 0.
        layer_0_str = self._RemoveTimeElapsedLines(layer_0_str)

        # Insert the layer_0_string at the beginning of the file as the new Layer:0.
        data.insert(2, layer_0_str)

        # Recalculate the TIME_ELAPSED lines base on the new layer order and remove the DELTA_TIME lines
        data = self._RewriteTimeElapsedLines(data)

        # Insert an XY lateral move line and a Z height line before the start of each individual print.
        data = self._AddTravelLines(data)

        # Re-number the layers to so the Cura preview will be in 'One-at-a-Time' mode.
        data = self._RenumberLayers(data)

        return data

    def _ExtrudeFromLocation(self, alt_data):
        # The first-extrusion-of-a-layer 'From' line is before layer change and must move to still relate to their 'go to' lines after the layers are shuffled.
        prev_x = 0.0
        prev_y = 0.0
        new_travel_line = ""
        for index, layer in enumerate(alt_data):
            if ";LAYER:0" in layer:
                lines = alt_data[index].split("\n")
                lines.reverse()
                for line in lines:
                    if line.startswith("G0 ") and " X" in line and " Y" in line:
                        prev_x = self.getValue(line, "X")
                        prev_y = self.getValue(line, "Y")
                        break
                new_travel_line = f"G0 F{self.speed_travel} X{prev_x} Y{prev_y}   ; FpF Travel"
                self.new_travel_list.append(new_travel_line)
        return alt_data

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
                        cur_e_string = f"G92 E{cur_e_value}               ; FpF Set E"
            e_list.append(cur_e_string)
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

    def _StripTemperatureLines(self, alt_data):
        # The 'initial layer' has been modified so the 'Init Bed' temps and 'Init Print' temps need to be reinserted.
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
                        lines[ldex] = f"M104 S{round(self.matl_print_temp)}                   ; FpF Print Temp\n" + line
                except:
                    IndexError
            # Step backwards through the list and delete the temperature lines to avoid skips
            if indices_to_delete != []:
                for ddex in sorted(indices_to_delete, reverse=True):
                    del lines[ddex]
            indices_to_delete = []
            alt_data[index] = "\n".join(lines)
        return alt_data

    def _RenumberLayers(self, alt_data):
        # Renumber so the Cura preview is correct when the Gcode is opened
        consecutive_lay_num = 0
        for num, layer in enumerate(alt_data):
            lines = layer.split("\n")
            for index, line in enumerate(lines):
                if ";LAYER:" in line:
                    lines[index] = f";LAYER:{consecutive_lay_num}"
                    consecutive_lay_num += 1
            alt_data[num] = "\n".join(lines)
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

    def _Layer0String(self, alt_data):
        '''
        Pull any raft layers and the layer:0's and morph them into a single layer ala 'All at Once'.
        Each print will complete rafts (if used) and then initial layer of each print before moving on to the next print.
        '''
        layer_0_str = ""
        self.layer_0_index_list = []
        for index, layer in enumerate(alt_data):
            if ";LAYER:-" in layer:
                layer_0_str += alt_data[index]
                self.layer_0_index_list.append(index)
            if ";LAYER:0" in alt_data[index]:
                layer_0_str += alt_data[index]
                self.layer_0_index_list.append(index)
        # Sort in descending order to delete from back to front
        for i in sorted(self.layer_0_index_list, reverse=True):
            del alt_data[i]
        return layer_0_str, alt_data

    def _RealLayer1Height(self, alt_data):
        # This accounts for the Layer:1 height whether or not Adaptive Layers is enabled
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

    def _PostProcessorOrderWarning(self, criteria):
        # It won't hurt anything but FootPrintsFirst really needs to run before DisplayInfoOnLCD.  This puts up a reminder message for the user.
        pp_data = ""
        scripts_list = Application.getInstance().getGlobalContainerStack().getMetaDataEntry("post_processing_scripts")
        for script_str in scripts_list.split("\n"):
            script_str = script_str.replace(r"\\\n", "\n;  ").replace("\n;  \n;  ", "\n")
            pp_data += str(script_str)
        pp_list = pp_data.split("\n")
        display_info_index = len(pp_list)
        footprintsfirst_index = -1
        if criteria == "display_info":
            try:
                for index, post_proc in enumerate(pp_list):
                    if "[DisplayInfoOnLCD]" in post_proc:
                        display_info_index = index
                    if "[FootPrintsFirst]" in post_proc:
                        footprintsfirst_index = index
                    if "add_filament_use = True" in post_proc:
                        Message(title = "[Foot Prints First]", text = "Will confuse 'Display Info on LCD / Filament Usage'.  There could be negative filament amounts reported.").show()
            except:
                IndexError, ValueError
            if display_info_index < footprintsfirst_index:
                return True
            else:
                return False
        elif criteria == "pause_at_height":
            try:
                for index, post_proc in enumerate(pp_list):
                    #Logger.info(f">>>GREG 3:  {post_proc}")
                    if "enable_pause_at_height = True" in post_proc:
                        return True
            except:
                IndexError, ValueError
            return False

    def _OrthogonalTravel(self, alt_data):
        # If rafts are enabled it is possible that there could be one in the way of the nozzle so any Z move must be last.
        for index, layer in enumerate(alt_data):
            lines = layer.split("\n")
            for ddex, line in enumerate(lines):
                if line.startswith("G0 ") and " X" in line and " Y" in line and " Z" in line:
                    xy_move = line.split(" Z")[0]
                    z_move = line.split(" Z")[1].split()[0]
                    lines[ddex] = f"{xy_move}          ; FpF XY Ortho\nG0 Z{z_move}                     ; FpF Z Ortho"
                    break
            alt_data[index] = "\n".join(lines)
        return alt_data

    def _RemoveTimeElapsedLines(self, layer_0_str):
        # They aren't needed within LAYER:0 and having more than one in the layer might affect other scripts.
        lines = layer_0_str.split("\n")
        number_of_models = layer_0_str.count(";TIME_ELAPSED:")
        time_value = 0.0
        mesh_count = 0
        for index, timeline in enumerate(lines):
            if ";TIME_ELAPSED:" in timeline:
                mesh_count += 1
                time_value += float(timeline.split(":")[1].split()[0])
                if self.layer_0_total_time == 0.0:
                    self.layer_0_total_time = float(time_value)
        # This 'Total Time' is an average and is close when the models are the same.
        self.layer_0_total_time *= mesh_count
        line_to_leave = f";TIME_ELAPSED:{round(float(self.layer_0_total_time),2)}      ; FpF New First Layer Time"
        layer_0_str = "\n".join(lines)
        layer_0_str = re.sub(";TIME_ELAPSED:(\d.*)\n", "", layer_0_str)
        layer_0_str += line_to_leave + "\n"
        return layer_0_str

    def _AddLayerTimes(self, alt_data):
        # Because the layers get scrambled a bit, the TIME_ELAPSED are incorrect. This function adds DELTA_TIME to each layer indicating the time required for the particular layer to print.  This is done before reordering the new LAYER:0.
        prev_layer_time = self.layer_0_total_time
        for index, layer in enumerate(alt_data):
            if index < 2 or index > len(alt_data)-1:
                continue
            if ";TIME_ELAPSED:" in layer:
                lines = layer.split("\n")
                for tdel, line in enumerate(lines):
                    if ";TIME_ELAPSED:" in line:
                        current_layer_time = float(layer.split(";TIME_ELAPSED:")[1].split()[0])
                        delta_time = current_layer_time - prev_layer_time
                        lines[tdel] = f";DELTA_TIME:{round(delta_time,2)}\n{line}"
                        prev_layer_time = current_layer_time
                alt_data[index] = "\n".join(lines)
        return alt_data

    def _RewriteTimeElapsedLines(self, alt_data):
        # After shuffling the layers around - this function uses the delta times and rewrites the TIME_ELAPSED lines.  It's not exact, but it's pretty close.  This is why FootPrintsFirst needs to run before DisplayInfoOnLCD.
        prev_time = round(self.layer_0_total_time,2)
        new_time = prev_time
        for index, layer in enumerate(alt_data):
            if ";TIME_ELAPSED:" in layer:
                lines = layer.split("\n")
                for tdel, line in enumerate(lines):
                    if ";DELTA_TIME:" in line:
                        delta_time = float(layer.split(";DELTA_TIME:")[1].split()[0])
                        new_time = delta_time + prev_time
                    if ";TIME_ELAPSED:" in line:
                        lines[tdel] = f";TIME_ELAPSED:{round(new_time,2)}"
                        prev_time = new_time
                alt_data[index] = "\n".join(lines)
            if ";LAYER:0" in layer or ";LAYER:-" in layer:
                alt_data[index] = re.sub(";DELTA_TIME:(\d.*)\n", "", layer)
                continue
        # Remove the temporary DELTA_TIME lines.
        for index, layer in enumerate(alt_data):
            if ";DELTA_TIME" in layer:
                alt_data[index] = re.sub(";DELTA_TIME:(-?\d+\.\d+|-?\d+)\n", "", layer)
        return alt_data