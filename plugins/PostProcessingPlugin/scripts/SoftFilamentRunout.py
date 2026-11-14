"""
                                            "Software Filament Runout Warning"
                                            a post processor for UltiMaker Cura
                                        by GregValiant (Greg Foresi) November 2026
-----------------------------------------------------------------------------------------------------------------------------------
 This script starts out with the 'Filament used' from Cura, and then checks the useage for each layer.  An M118 line (or a simple comment) is added at each Layer Change line to send the amount of 'Filament Remaining to Print' and 'filament used this layer' to a print server (Ex: OctoPrint, Pronterface, etc.).  M118 is used because many LCD's can't handle a long message via M117.
 The user can ask to be notified when the filament remaining to print counts down to a certain length.  A beep is added at that point.  You can also choose to add a pause there. The pause script always uses "M0" as the pause command.  The user should open the file to double check the pause parking movement codes anyway, but changing the M0 to 'PAUSE" or 'M25' or whatever works with the machine would only take a second.  You could also utilize 'Search and Replace' (Ex: Search for 'M0 ;' and Replace with 'PAUSE ;').
 FYI: Be patient as this is a slow running post processer.  It has to add up every extrusion in the file.
"""

from ..Script import Script
from UM.Application import Application
from UM.Qt.Duration import DurationFormat
import math
from UM.Message import Message
from UM.Logger import Logger

class SoftFilamentRunout(Script):

    def getSettingDataString(self):
        return """{
            "name": "Software Filament Runout Warning",
            "key": "SoftFilamentRunout",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "enable_runout":
                {
                    "label": "Enable the Script",
                    "description": "Enable the Post Processor so it will run.  This script adds M118 lines to the gcode at each layer telling you how much filament is required to finish the print.  There are options for a <beep> and a 'generic' pause.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                },
                "add_filament_use":
                {
                    "label": "Add a Message to the Gcode",
                    "description": "You may elect to insert an M118 line at the beginning of each layer (in the G-Code) indicating the amount of filament (Extruder 1 (T0) only) that is required to finish the print from that point, and the amount of filament that the current layer will use.  M118 sends a message over a network or USB port to a print server (like Octoprint or Pronterface).  The other option is to add a comment line to the gcode (no M118 command).",
                    "type": "enum",
                    "options": {
                        "m118_line": "M118 line",
                        "just_comment": "Comment only"
                        },
                    "default_value": "m118_line",
                    "enabled": "enable_runout"
                },
                "add_m118_a1":
                {
                    "label": "    Add A1 parameter",
                    "description": "Some printer firmwares require the 'A' parameter to be added to the M118 line. The 'E' and 'P' parameters are always entered by default.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_runout and add_filament_use=='m118_line'"
                },
                "beep_at_runout":
                {
                    "label": "Beep at Runout",
                    "description": "Adds an M300 when the filament gets down to 'Warn At'.  If you aren't around the machine, you'll miss it.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_runout and runout_min_filament>0"
                },
                "runout_min_filament":
                {
                    "label": "    Minimum Filament notification",
                    "description": "When the 'filament remaining to print' gets down to this amount (in meters), the 'M300 ; Beep' line will be inserted.  (FYI: 3.0 meters is about 9.8 feet.).  Set to zero to disable this.",
                    "type": "float",
                    "default_value": 3.0,
                    "minimum_value": 1,
                    "unit": "meters ",
                    "enabled": "enable_runout and beep_at_runout"
                },
                "beep_tone_duration":
                {
                    "label": "    Beep Duration",
                    "description": "How long should the beep be (in seconds). A 5 second beep is really annoying if you are there to hear it, and useless if you are not.",
                    "type": "float",
                    "default_value": 1,
                    "minimum_value": 0.1,
                    "unit": "Sec's  ",
                    "enabled": "enable_runout and runout_min_filament>0 and beep_at_runout"
                },
                "pause_at_runout":
                {
                    "label": "    Add Pause",
                    "description": "Adds a generic pause snippet to the Gcode at the indicated RunOut point. The head will at X0 Y(machine_depth - 5). Enter the pause command for your printer into the box below.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_runout and runout_min_filament>0 and beep_at_runout"
                },
                "pause_command":
                {
                    "label": "    Pause Command",
                    "description": "Different firmware flavors require different commands to pause.  Enter your pause command here.",
                    "type": "str",
                    "default_value": "M0",
                    "enabled": "enable_runout and pause_at_runout"
                }
            }
        }"""

    def execute(self, data):
        # Exit if the script is not enabled or if it was previously postprocessed.
        if not self.getSettingValueByKey("enable_runout"):
            data[0] += ";  [Software Filament Runout] Not enabled\n"
            Logger.info(f"\n[Software Filament Runout] Not enabled\n")
            return data
        # Exit if the file has been post processed, or if it is a Gcode file.
        for layer in data:
            if ";POSTPROCESSED" in layer:
                return data
            if ";LAYER:" in layer:
                break

        # Define some variables.
        self.global_stack = Application.getInstance().getGlobalContainerStack()
        self.extruder = self.global_stack.extruderList
        self.retraction_enabled = self.extruder[0].getProperty("retraction_enable", "value")
        if self.retraction_enabled:
            self.retraction_amount = self.extruder[0].getProperty("retraction_amount", "value")
        else:
            self.retraction_amount = 0
        self.one_at_a_time = self.global_stack.getProperty("print_sequence", "value")
        self.add_m118_a1 = self.getSettingValueByKey("add_m118_a1")
        self.beep_at_runout = self.getSettingValueByKey("beep_at_runout")
        # 'beep_layer_count' Limits the insertion of M300 lines to 1 layer.
        self.beep_layer_count = 1
        self.beep_tone_duration = self.getSettingValueByKey("beep_tone_duration") * 1000
        # For a message to the user
        self.runout_layer = 0
        # For a message to the user
        self.runout_str = ""
        # The amount of filament left in the print that will trigger the Beep insertion
        self.runout_min_filament = int(self.getSettingValueByKey("runout_min_filament") * 1000)
        pause_at_runout = bool(self.getSettingValueByKey("pause_at_runout"))
        # A list of ('total_filament' minus 'filament per layer') to insert to indicate the 'filament required' to finish the print.
        self.filament_countdown_list = []
        # The amount of filament to be used in the upcoming layer
        self.filament_delta_list = []
        self.add_filament_use = self.getSettingValueByKey("add_filament_use")
        # Get the cross-sectional area since it affects the 'weight-of-extruded-material'.
        self.filament_x_section = (float(self.extruder[0].getProperty("material_diameter", "value") / 2)**2) * math.pi
        # Convert the density from gm/cm³ to gr/mm³
        self.material_density = float(self.extruder[0].material.getMetaDataEntry("properties", {}).get("density", 0)) / 1000
        # The total filament used in the print.  Only T0 (Extruder 1) is considered.
        self.total_filament_reqd = round(Application.getInstance().getPrintInformation().materialLengths[0] * 1000, 2)
        # Get the extrusion mode.
        self.absolute_extrusion = not bool(self.global_stack.getProperty("relative_extrusion", "value"))
        # If the user doesn't want an M118 line inserted then insert a simple comment.
        self.m118_text = ";"
        if self.add_filament_use == "m118_line":
            # The E1 and P0 parameters are rquired by many firmwares to display longer messages
            self.m118_text = "M118 E1 P0 "
            # Some firmware also requires the A parameter
            if self.add_m118_a1:
                self.m118_text += "A1 "

        # The Extrusion Mode determines how the E is tracked and the data handled.
        if self.absolute_extrusion:
            data = self._AbsoluteFilamentUse(data)
        else:
            data = self._RelativeFilamentUse(data)

        # Pad the per and delta lists to account for the 'ending gcode' section to avoid IndexErrors.
        self.filament_countdown_list.append(0.0)
        self.filament_delta_list.append("0.0")

        # Everything has been:  collected, calculated, collated, and configured, and is now ready for combining.
        data = self._AlterGcode(data)

        # If the user opted for an M300 line AND the user opted for a pause - it gets inserted here.
        if pause_at_runout and self.beep_at_runout:
            data = self._PauseAtRunout(data)

        # If the user opted for an M300 line message regarding the runout layer and the runout time elapsed.
        if self.beep_at_runout:
            Message(title = "[Software Filament Runout]", text = f"'Filament Minimum' of {round(self.runout_min_filament/1000)} meters will be reached at the start of preview layer #{self.runout_layer + 1} about {self.runout_str} into the print.").show()
        total_num = 0
        for item in self.filament_delta_list:
            num = float(item.split()[0])
            total_num += num
        return data

    def _AlterGcode(self, alt_data):
        # Go through and make the insertions from the countdown list and the delta list.
        for index, layer in enumerate(alt_data):
            if index < 2 or index >= len(alt_data)-1:
                continue
            lines = layer.split("\n")
            for lineindex, line in enumerate(lines):
                if line.startswith(";LAYER:"):
                    try:
                        weight = float(self.filament_countdown_list[index]) * float(self.material_density) * float(self.filament_x_section)
                    except TypeError as e:
                        Logger.error(f"\nError while calculating the filament weight: {e}\n")
                        weight = "error"
                    lines[lineindex] += f"\n{self.m118_text}Filament Reqd= {float(self.filament_countdown_list[index])/1000:.2f}m | Wt= {weight:.2f}gr | This layer will use: {self.filament_delta_list[index]}"
                    if self.beep_at_runout and self.beep_layer_count > 0:
                        if float(self.filament_countdown_list[index])/1000 <= float(self.runout_min_filament)/1000:
                            lines[lineindex] += f"\nM300 P{self.beep_tone_duration} ; Beep at Runout"
                            self.beep_layer_count -= 1
                            runout_time_elapsed_str = self._RunoutTimeElapsed(alt_data[index - 1], index, alt_data)
            alt_data[index] = "\n".join(lines)
        return alt_data

    def _RelativeFilamentUse(self, alt_data):
        # Track the E values when in Relative Mode.
        self.filament_countdown_list = []

        # layer_total_e is the filament use per layer.
        layer_total_e = 0.0
        # The layer_total_e will be appended to the delta list
        self.filament_delta_list = []

        # running_total_e is the 'countdown from' amount
        running_total_e = float(self.total_filament_reqd)
        self.filament_countdown_list.append(round(self.total_filament_reqd,2))

        for layindex, layer in enumerate(alt_data):
            # This can happen in one-at-a-time mode
            if not ";LAYER:" in layer:
                self.filament_delta_list.append("0.0")
                self.filament_countdown_list.append(round(running_total_e,2))
                continue
            if 1 < layindex >= len(alt_data)-1:
                continue
            lines = layer.split("\n")
            layer_total_e = 0.0
            e_before_reset = 0.0
            current_e = 0.0
            for line in lines:
                if line[0:3] in ["G1 ", "G2 ", "G3 "] and " X" in line and " Y" in line and " E" in line:
                    layer_total_e +=  self.getValue(line, "E")
            running_total_e -= layer_total_e
            if running_total_e < 0:
                running_total_e = 0.0
            weight = layer_total_e * self.filament_x_section * self.material_density
            # Add the message to print server line for layer to the list
            self.filament_delta_list.append(f"{layer_total_e:.1f} millimeters")
            self.filament_countdown_list.append(round(running_total_e,2))
            layer_total_e = 0.0
        return alt_data

    def _AbsoluteFilamentUse(self, alt_data):
        # Track the E values when in Absolute Mode.  (This function really sucked to write.)
        self.filament_countdown_list = [0.0, 0.0]
        # The amount of filament to be used in the upcoming layer
        self.filament_delta_list = ["0.0", "0.0"]
        running_total_e = float(self.total_filament_reqd)
        starting_e = 0.0
        ending_e = 0.0
        layer_total_e = 0.0
        # Pad the countdown list so the indexes match
        self.filament_countdown_list.append(round(self.total_filament_reqd,2))
        for index, layer in enumerate(alt_data):
            if index < 2:
                continue
            if index > len(alt_data)-1:
                break
            if not ";LAYER:" in layer:
                self.filament_delta_list.append("0.0")
                self.filament_countdown_list.append(running_total_e)
                layer_total_e = 0.0
                continue
            layer_total_e = 0.0
            starting_e = 0.0
            ending_e = 0.0
            lines = layer.split("\n")
            # Get the starting_e
            for line in lines:
                if (line[0:3] in ["G1 ", "G2 ", "G3 ", "G92"] and " E" in line):
                    the_e_value = "E" + line.split("E")[1].split()[0]
                    starting_e = self.getValue(the_e_value, "E")
                    break
            lines.reverse()
            # Get the ending_e
            for line in lines:
                if (line[0:3] in ["G1 ", "G2 ", "G3 ", "G92"] and " E" in line):
                    the_e_value = "E" + line.split("E")[1].split()[0]
                    ending_e = self.getValue(the_e_value, "E")
                    if ending_e > 0:
                        break
            lines.reverse()

            # Get the starting_e and ending_e in layers with a reset and adjust
            if "G92 E" in layer or starting_e > ending_e:
                layer_total_e = self._CalculateG92values(layer, starting_e, ending_e)
                running_total_e -= layer_total_e
                self.filament_delta_list.append(f"{layer_total_e:.2f} millimeters")
                self.filament_countdown_list.append(round(running_total_e, 2))
                layer_total_e = 0.0
            elif not "G92 E" in layer:
                layer_total_e = ending_e - starting_e
                # This one was really hard to figure out
                if self.one_at_a_time:
                    layer_total_e += self.retraction_amount
                running_total_e -= layer_total_e
                self.filament_delta_list.append(f"{layer_total_e:.2f} millimeters")
                self.filament_countdown_list.append(round(running_total_e, 2))
                layer_total_e = 0.0
        return alt_data

    def _PauseAtRunout(self, alt_data):
        # Adds a generic pause code
        if self.beep_at_runout:
            self.extruder = self.global_stack.extruderList
            speed_z_hop = round(self.extruder[0].getProperty("speed_z_hop", "value") * 60)
            speed_travel = round(self.extruder[0].getProperty("speed_travel", "value") * 60)
            speed_retract = round(self.extruder[0].getProperty("retraction_retract_speed", "value") * 60)
            machine_depth = self.global_stack.getProperty("machine_depth", "value")
            pause_code = None
            pause_cmd = self.getSettingValueByKey("pause_command")
            x_return = 0.0
            y_return = 0.0

            for index, layer in enumerate(alt_data):
                if "Beep at Runout" in layer:
                    prev_lines = alt_data[index-1].split("\n")
                    prev_lines.reverse()
                    for line_index, line in enumerate(prev_lines):
                        if " X" in line and " Y" in line:
                            x_return = self.getValue(line, "X")
                            y_return = self.getValue(line, "Y")
                            break
                    lines = layer.split("\n")
                    for line_index, line in enumerate(lines):
                        if "Beep at Runout" in line:
                            if "M600" not in pause_cmd:
                                pause_code = (
                                        ";..........................Runout Pause Code\n"
                                        "G91 ; Relative movement\n"
                                        f"G0 F{speed_z_hop} Z5 ; Move up\n"
                                        "G90 ; Absolute movement\n"
                                        f"G0 F{speed_travel} X0 Y{machine_depth-5} ; Park the head\n"
                                        f"{line}\n"
                                        f"{pause_cmd} ; The pause command\n"
                                        f"G0 F{speed_travel} X{x_return} Y{y_return} ; Return to print\n"
                                        "G91 ; Relative movement\n"
                                        f"G0 F{speed_z_hop} Z-5 ; Move down\n"
                                        "G90 ; Absolute movement")

                                if self.retraction_enabled:
                                    pause_code += f"\nM83 ; Relative extrusion\nG1 F{speed_retract} E-{self.retraction_amount} ; Retract after filament change"
                                    if self.absolute_extrusion:
                                        pause_code += "\nM82 ; Absolute extrusion\n;..........................End of Pause Code"
                                    else:
                                        pause_code += "\n;..........................End of Pause Code"
                                else:
                                    pause_code += f"\n;..........................End of Pause Code"
                            elif "M600" in pause_cmd:
                                pause_code = (
                                        ";..........................Runout Pause Code\n"
                                        f"{pause_cmd} ; The pause command\n"
                                        ";..........................End of Pause Code")

                            lines[line_index] = self._FormatString(pause_code)
                            alt_data[index] = "\n".join(lines)
                            break
                if pause_code is not None:
                    break
        return alt_data

    def _CalculateG92values(self, layer, starting_e, ending_e):
        #Logger.info(f" 0000 Starting_E {starting_e}  Ending E {ending_e}")
        starting_e = 0
        ending_e = 0
        layer_total_e = 0
        lines = layer.split("\n")
        for line in lines:
            if line[0:3] in ["G1 ", "G2 ", "G3 "] and " E" in line:
                if starting_e == 0:
                    starting_e = float(line.split("E")[1].split()[0])
                ending_e = float(line.split("E")[1].split()[0])
            if "G92 E" in line:
                layer_total_e += ending_e - starting_e
                starting_e = float(line.split("E")[1].split()[0])
                ending_e = starting_e
        layer_total_e += ending_e - starting_e
        return layer_total_e

    def _FormatString(self, any_gcode_str: str):
        # Mrs. Trudell (3rd grade English teacher) would be please with this.
        temp_lines = any_gcode_str.split("\n")
        gap_len = 0
        for temp_line in temp_lines:
            if ";" in temp_line and not temp_line.startswith(";"):
                if gap_len - len(temp_line.split(";")[0]) + 1 < 0:
                    gap_len = len(temp_line.split(";")[0]) + 1
        if gap_len < 27: gap_len = 27
        for temp_index, temp_line in enumerate(temp_lines):
            if ";" in temp_line and not temp_line.startswith(";"):
                temp_lines[temp_index] = temp_line.replace(temp_line.split(";")[0], temp_line.split(";")[0] + str(
                    " " * (gap_len - len(temp_line.split(";")[0]))), 1)
            # This formats lines that are commented out but contain additional comments Ex:  ;M420 ; leveling mesh
            elif temp_line.startswith(";") and ";" in temp_line[1:]:
                temp_lines[temp_index] = temp_line[1:].replace(temp_line[1:].split(";")[0], ";" + temp_line[1:].split(";")[0] + str(" " * (gap_len - 1 - len(temp_line[1:].split(";")[0]))), 1)
        any_gcode_str = "\n".join(temp_lines)
        return any_gcode_str

    def _RunoutTimeElapsed(self, prev_layer, index, alt_data):
        # This will set the value of the self.runout_layer and the self.runout_str that will go into a Message to the user.
        runout_time = float(prev_layer.split(";TIME_ELAPSED:")[1].split("\n")[0])
        self.runout_layer = 0
        runout_hr = int(runout_time / 3600)
        runout_min = runout_time / 3600 - runout_hr
        runout_min *= 60
        for num in range(2, index):
            if ";LAYER:" in alt_data[num]:
                self.runout_layer += 1
        self.runout_str = f"{runout_hr}hr {round(runout_min)}min"
        return
