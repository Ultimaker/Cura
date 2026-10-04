"""
    By GregValiant (Greg Foresi) September of 2026 (concept by: 'EdoFro')
    ~ This script will print the ";LAYER:0's" of each model first, and then revert to One-at-a-Time print sequence.
    ~ When using this with other scripts, this script must run before 'DisplayInfoOnLCD' or the M117 and M118 lines inserted by DisplayInfo will be incorrect.
    ~ This script requires "Print Sequence" == "One at a Time"
"""

from UM.Application import Application
from ..Script import Script
from UM.Message import Message
from UM.Logger import Logger

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
                    "description": "Enables the script so it will run.  This script will move all the individual 'Initial Layers' into a single layer that will print first.  That allows you to see if all the prints start OK.  Please note: 'One-at-a-Time'.",
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

        # A check to insure that the user knows 'FootPrintsFirst' should run before 'DisplayInfoOnLCD'
        data = self._PostProcessorOrderWarning(data)

        # If in Absolute Extrusion mode - enter 'G92 E' lines to insure the E is synced to the start of the layer.
        if not relative_extrusion:
            data = self._AdjustELocations(data)

        # If adaptive layers are enabled then the Layer:1 Height must be checked so just do it
        layer_1_height = self._RealLayer1Height(data)
        self.init_layer_height_line = f"G1 F{speed_z_hop} Z{layer_1_height}                ; FpF Move Z"

        # Get the "from" location for the initial extrusion of each layer:0 and add them to a list.
        data = self._ExtrudeFromLocation(data)

        # If rafts are enabled the travel between prints must be ortho so and intervening print doesn't get hit.
        if raft_enabled:
            data = self._OrthogonalTravel(data)

        # Strip the temperature lines.
        data = self._StripTemperatureLines(data)

        # Pull all the layer:0's from the gcode and concatenate them into a single layer.  This includes any Raft layers.
        layer_0_result = self._Layer0String(data)
        layer_0_str = layer_0_result[0]
        data = layer_0_result[1]

        # Skip the first LAYER:0 line and then remove any other Layer:0 lines from the new layer 0.
        start_now = False
        layer_0_list = layer_0_str.split("\n")
        indices_to_delete = []
        for ldex, line in enumerate(layer_0_list):
            if (";LAYER:0" in line or ";LAYER:-" in line) and start_now:
                indices_to_delete.append(ldex)
            if ";LAYER:0" in line or ";LAYER:-" in line:
                start_now = True
        # Step backwards through the list and delete so earlier indices aren't shifted out from under us.
        for ldex in sorted(indices_to_delete, reverse=True):
            layer_0_list.pop(ldex)

        # Set the temps for Layer:0 to 'Initial Layer Print/Initial Layer Bed' Temps and then reset to 'Print/Bed Temps' for Layer:1
        layer_0_list.insert(1, f"M104 S{round(matl_print_temp_0)}                   ; FpF Print Temp\nM140 S{round(matl_bed_temp_0)}                    ; FpF Bed Temp")
        layer_0_list.insert(len(layer_0_list)-2, f"M104 S{round(self.matl_print_temp)}                   ; FpF Print Temp\nM140 S{round(matl_bed_temp)}                    ; FpF Bed Temp")
        layer_0_str = "\n".join(layer_0_list)

        # Insert the layer_0_string at the beginning of the file as the new Layer:0.
        data.insert(2, layer_0_str)

        # Insert an XY lateral move line and a Z height line before the start of each layer.
        data = self._AddTravelLines(data)

        # Re-number the layers to fix the Cura preview
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
                new_travel_line = f"G0 F{self.speed_travel} X{prev_x} Y{prev_y} ; FpF Travel"
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
                except IndexError:
                    Logger.warning(f"[Foot Prints First] IndexError while stripping temperature line at index {ldex}")
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
        # Insert the lateral move line and the vertical move line before the start of each layer:1
        count = 0
        for num, layer in enumerate(alt_data):
            if ";LAYER:1\n" in layer:
                lines = alt_data[num-1].split("\n")
                lines.insert(len(lines)-2, f"{self.new_travel_list[count]}\n{self.init_layer_height_line}")
                count += 1
                alt_data[num-1] = "\n".join(lines)
        return alt_data

    def _Layer0String(self, alt_data):
        # Pull any raft layers and the layer:0's and morph them into a single layer ala 'All at Once'.
        layer_0_str = ""
        layer_0_index_list = []
        for index, layer in enumerate(alt_data):
            if ";LAYER:-" in layer:
                layer_0_str += alt_data[index]
                layer_0_index_list.append(index)
            if ";LAYER:0" in alt_data[index]:
                layer_0_str += alt_data[index]
                layer_0_index_list.append(index)
        # Sort in descending order to delete from back to front
        for i in sorted(layer_0_index_list, reverse=True):
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

    def _PostProcessorOrderWarning(self, alt_data):
        # It won't hurt anything but FootPrintsFirst really needs to run before DisplayInfoOnLCD.  This puts up a reminder message for the user.
        pp_data = ""
        scripts_list = Application.getInstance().getGlobalContainerStack().getMetaDataEntry("post_processing_scripts")
        for script_str in scripts_list.split("\n"):
            script_str = script_str.replace(r"\\\n", "\n;  ").replace("\n;  \n;  ", "\n")
            pp_data += str(script_str)
        pp_list = pp_data.split("\n")
        display_info_index = len(pp_list)
        try:
            for index, post_proc in enumerate(pp_list):
                if "[DisplayInfoOnLCD]" in post_proc:
                    display_info_index = index
                if "[FootPrintsFirst]" in post_proc:
                    footprintsfirst_index = index
                if "add_filament_use = True" in post_proc:
                    Message(title = "⚠️[Foot Prints First]⚠️", text = "Is not compatible with Display Info on LCD 'Filament Usage' and could be negative filament use values reported to a print server.").show()
        except (IndexError, ValueError):
            Logger.warning("[Foot Prints First] Error parsing post_processing_scripts metadata for order check")
        if display_info_index < footprintsfirst_index:
            Message(title = "⚠️[FootprintsFirst]", text = "'FootprintsFirst' should run BEFORE 'DisplayInfoOnLCD' to insure the layer numbers turn out correct.").show()
        return alt_data

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