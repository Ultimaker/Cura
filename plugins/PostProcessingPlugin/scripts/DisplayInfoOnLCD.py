# Display Filename and Layer on the LCD by Amanda de Castilho on August 28, 2018
# Modified: Joshua Pope-Lewis on November 16, 2018
# Display Progress on LCD by Mathias Lyngklip Kjeldgaard, Alexander Gee, Kimmo Toivanen, Inigo Martinez on July 31, 2019
# Show Progress was adapted from Display Progress by Louis Wooters on January 6, 2020.  His changes are included here.
#---------------------------------------------------------------
# DisplayNameOrProgressOnLCD.py
# Cura Post-Process plugin
# Combines 'Display Filename and Layer on the LCD' with 'Display Progress'
# Combined and with additions by: GregValiant (Greg Foresi)
# Date:  September 8, 2023
# Date:  March 31, 2024 - Bug fix for problem with adding M118 lines if 'Remaining Time' was not checked.
# NOTE:  This combined post processor will make 'Display Filename and Layer on the LCD' and 'Display Progress' obsolete
# Description:  Display Filename and Layer options:
#       Status messages sent to the printer...
#           - Scrolling (SCROLL_LONG_FILENAMES) if enabled in Marlin and you aren't printing a small item select this option.
#           - Name: By default it will use the name generated by Cura (EG: TT_Test_Cube) - You may enter a custom name here
#           - Start Num: Choose which number you prefer for the initial layer, 0 or 1
#           - Max Layer: Enabling this will show how many layers are in the entire print (EG: Layer 1 of 265!)
#           - Add prefix 'Printing': Enabling this will add the prefix 'Printing'
#           - Example Line on LCD:  Printing Layer 0 of 395 3DBenchy
#       Display Progress options:
#           - Display Total Layer Count
#           - Disply Time Remaining for the print
#           - Time Fudge Factor % - Divide the Actual Print Time by the Cura Estimate.  Enter as a percentage and the displayed time will be adjusted.  This allows you to bring the displayed time closer to reality (Ex: Entering 87.5 would indicate an adjustment to 87.5% of the Cura estimate).
#           - Example line on LCD:  1/479 | ET 2h13m
#           - Time to Pauses changes the M117/M118 lines to countdown to the next pause as  1/479 | TP 2h36m
#           - 'Add M118 Line' is available with either option.  M118 will bounce the message back to a remote print server through the USB connection.
#           - 'Add M73 Line' is used by 'Display Progress' only.  There are options to incluse M73 P(percent) and M73 R(time remaining)
#           - Enable 'Finish-Time' Message - when enabled, takes the Print Time and calculates when the print will end.  It takes into account the Time Fudge Factor.  The user may enter a print start time.  This is also available for Display Filename.

from ..Script import Script
from UM.Application import Application
from UM.Qt.Duration import DurationFormat
import time
import datetime
import math
from UM.Message import Message
import re

class DisplayInfoOnLCD(Script):

    def initialize(self) -> None:
        super().initialize()
        try:
            if Application.getInstance().getGlobalContainerStack().getProperty("print_sequence", "value") == "all_at_once":
                enable_countdown = True
                self._instance.setProperty("enable_countdown", "value", enable_countdown)
        except:
            pass
            
    def getSettingDataString(self):
        return """{
            "name": "Display Info on LCD",
            "key": "DisplayInfoOnLCD",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "display_option":
                {
                    "label": "LCD display option...",
                    "description": "Display Filename and Layer was formerly 'Display Filename and Layer on LCD' post-processor.  The message format on the LCD is 'Printing Layer 0 of 15 3D Benchy'.  Display Progress is similar to the former 'Display Progress on LCD' post-processor.  The display format is '1/16 | ET 2hr28m'.  Display Progress includes a fudge factor for the print time estimate.",
                    "type": "enum",
                    "options": {
                        "display_progress": "Display Progress",
                        "filename_layer": "Filename and Layer"
                        },
                    "default_value": "display_progress"
                },
                "format_option":
                {
                    "label": "Scroll enabled/Small layers?",
                    "description": "If SCROLL_LONG_FILENAMES is enabled in your firmware select this setting.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "display_option == 'filename_layer'"
                },
                "file_name":
                {
                    "label": "Text to display:",
                    "description": "By default the current filename will be displayed on the LCD. Enter text here to override the filename and display something else.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "display_option == 'filename_layer'"
                },
                "startNum":
                {
                    "label": "Initial layer number:",
                    "description": "Choose which number you prefer for the initial layer, 0 or 1",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": 0,
                    "maximum_value": 1,
                    "enabled": "display_option == 'filename_layer'"
                },
                "maxlayer":
                {
                    "label": "Display max layer?:",
                    "description": "Display how many layers are in the entire print on status bar?",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "display_option == 'filename_layer'"
                },
                "addPrefixPrinting":
                {
                    "label": "Add prefix 'Printing'?",
                    "description": "This will add the prefix 'Printing'",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "display_option == 'filename_layer'"
                },
                "display_total_layers":
                {
                    "label": "Display total layers",
                    "description": "This setting adds the 'Total Layers' to the LCD message as '17/234'.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "display_option == 'display_progress'"
                },
                "display_remaining_time":
                {
                    "label": "Display remaining time",
                    "description": "This will add the remaining printing time to the LCD message.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "display_option == 'display_progress'"
                },
                "add_m117_line":
                {
                    "label": "Add M117 Line",
                    "description": "M117 sends a message to the LCD screen.  Some screen firmware will not accept or display messages.",
                    "type": "bool",
                    "default_value": true
                },
                "add_m118_line":
                {
                    "label": "Add M118 Line",
                    "description": "Adds M118 in addition to the M117.  It will bounce the message back through the USB port to a computer print server (if a printer server like Octoprint or Pronterface is in use).",
                    "type": "bool",
                    "default_value": true
                },
                "add_m118_a1":
                {
                    "label": "    Add A1 to M118 Line",
                    "description": "Adds A1 parameter.  A1 adds a double foreslash '//' to the response.  Octoprint may require this.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "add_m118_line"
                },
                "add_m118_p0":
                {
                    "label": "    Add P0 to M118 Line",
                    "description": "Adds P0 parameter.  P0 has the printer send the response out through all it's ports.  Octoprint may require this.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "add_m118_line"
                },
                "add_m73_line":
                {
                    "label": "Add M73 Line(s)",
                    "description": "Adds M73 in addition to the M117.  For some firmware this will set the printers time and or percentage.  M75 is added to the beginning of the file and M77 is added to the end of the file.  M73 will be added if one or both of the following options is chosen.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "display_option == 'display_progress'"
                },
                "add_m73_percent":
                {
                    "label": "     Add M73 Percentage",
                    "description": "Adds M73 with the P parameter to the start of each layer.  For some firmware this will set the printers 'percentage' of layers completed and it will count upward.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "add_m73_line and display_option == 'display_progress'"
                },
                "add_m73_time":
                {
                    "label": "     Add M73 Time",
                    "description": "Adds M73 with the R parameter to the start of each layer.  For some firmware this will set the printers 'print time' and it will count downward.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "add_m73_line and display_option == 'display_progress' and display_remaining_time"
                },
                "speed_factor":
                {
                    "label": "Time Fudge Factor %",
                    "description": "When using 'Display Progress' tweak this value to get better estimates. ([Actual Print Time]/[Cura Estimate]) x 100 = Time Fudge Factor.  If Cura estimated 9hr and the print actually took 10hr30min then enter 117 here to adjust any estimate closer to reality.  This Fudge Factor is also used to calculate the print finish time.",
                    "type": "float",
                    "unit": "%",
                    "default_value": 100,
                    "enabled": "enable_end_message or display_option == 'display_progress'"
                },
                "enable_countdown":
                {
                    "label": "Enable Countdown to Pauses",
                    "description": "If print sequence is 'one_at_a_time' this is false.  This setting is always hidden.",
                    "type": "bool",
                    "value": false,
                    "enabled": false
                },
                "countdown_to_pause":
                {
                    "label": "Countdown to Pauses",
                    "description": "This must run AFTER any script that adds a pause.  Instead of the remaining print time the LCD will show the estimated time to the next layer that has a pause (TP).",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "display_option == 'display_progress' and enable_countdown and display_remaining_time"
                },
                "pause_cmd":
                {
                    "label": "     What pause command(s) are used?",
                    "description": "This might be M0, or M25 or M600 if Filament Change is used.  If you have mixed commands then delimit them with a comma ',' (Ex: M0,M600).  Spaces are not allowed.",
                    "type": "str",
                    "default_value": "M0",
                    "enabled": "countdown_to_pause and enable_countdown and display_remaining_time"
                },
                "enable_end_message":
                {
                    "label": "Enable 'Finish-Time' Message",
                    "description": "Get a message when you save a fresh slice.  It will show the estimated date and time that the print would finish.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                },
                "print_start_time":
                {
                    "label": "Print Start Time (Ex 16:45)",
                    "description": "Use 'Military' time.  16:45 would be 4:45PM.  09:30 would be 9:30AM.  If you leave this blank it will be assumed that the print will start Now.  If you enter a guesstimate of your printer start time and that time is before 'Now' then the guesstimate will consider that the print will start tomorrow at the entered time.  ",
                    "type": "str",
                    "default_value": "",
                    "unit": "hrs  ",
                    "enabled": "enable_end_message"
                }
            }
        }"""

    def execute(self, data):
        display_option = self.getSettingValueByKey("display_option")
        add_m117_line = self.getSettingValueByKey("add_m117_line")
        add_m118_line = self.getSettingValueByKey("add_m118_line")
        add_m118_a1 = self.getSettingValueByKey("add_m118_a1")
        add_m118_p0 = self.getSettingValueByKey("add_m118_p0")
        add_m73_line = self.getSettingValueByKey("add_m73_line")
        add_m73_time = self.getSettingValueByKey("add_m73_time")
        add_m73_percent = self.getSettingValueByKey("add_m73_percent")
        m73_str = ""

    # This is Display Filename and Layer on LCD---------------------------------------------------------
        if display_option == "filename_layer":
            max_layer = 0
            lcd_text = "M117 "
            octo_text = "M118 "
            if self.getSettingValueByKey("file_name") != "":
                file_name = self.getSettingValueByKey("file_name")
            else:
                file_name = Application.getInstance().getPrintInformation().jobName
            if self.getSettingValueByKey("addPrefixPrinting"):
                lcd_text += "Printing "
                octo_text += "Printing "
            if not self.getSettingValueByKey("scroll"):
                lcd_text += "Layer "
                octo_text += "Layer "
            else:
                lcd_text += file_name + " - Layer "
                octo_text += file_name + " - Layer "
            i = self.getSettingValueByKey("startNum")
            for layer in data:
                display_text = lcd_text + str(i)
                m118_text = octo_text + str(i)
                layer_index = data.index(layer)
                lines = layer.split("\n")
                for line in lines:
                    if line.startswith(";LAYER_COUNT:"):
                        max_layer = line
                        max_layer = max_layer.split(":")[1]
                        if self.getSettingValueByKey("startNum") == 0:
                            max_layer = str(int(max_layer) - 1)
                    if line.startswith(";LAYER:"):
                        if self.getSettingValueByKey("maxlayer"):
                            display_text += " of " + max_layer
                            m118_text += " of " + max_layer
                            if not self.getSettingValueByKey("scroll"):
                                display_text += " " + file_name
                                m118_text += " " + file_name
                        else:
                            if not self.getSettingValueByKey("scroll"):
                                display_text += " " + file_name + "!"
                                m118_text += " " + file_name + "!"
                            else:
                                display_text += "!"
                                m118_text += "!"
                        line_index = lines.index(line)
                        if add_m117_line:
                            lines.insert(line_index + 1, display_text)
                        if add_m118_line:
                            if add_m118_a1 and not add_m118_p0:
                                m118_str = m118_text.replace("M118 ","M118 A1 ")
                            if add_m118_p0 and not add_m118_a1:
                                m118_str = m118_text.replace("M118 ","M118 P0 ")
                            if add_m118_p0 and add_m118_a1:
                                m118_str = m118_text.replace("M118 ","M118 A1 P0 ")
                            lines.insert(line_index + 2, m118_str)
                        i += 1
                final_lines = "\n".join(lines)
                data[layer_index] = final_lines
            if bool(self.getSettingValueByKey("enable_end_message")):
                message_str = self.message_to_user(self.getSettingValueByKey("speed_factor") / 100)
                Message(title = "Display Info on LCD - Estimated Finish Time", text = message_str[0] + "\n\n" + message_str[1] + "\n" + message_str[2] + "\n" + message_str[3]).show()
            return data

    # Display Progress (from 'Show Progress' and 'Display Progress on LCD')---------------------------------------
        elif display_option == "display_progress":
            print_sequence = Application.getInstance().getGlobalContainerStack().getProperty("print_sequence", "value")
            # Add the Initial Layer Height just below Layer Height in data[0]
            extruder_count = Application.getInstance().getGlobalContainerStack().getProperty("machine_extruder_count", "value")
            init_layer_hgt_line = ";Initial Layer Height: " + str(Application.getInstance().getGlobalContainerStack().getProperty("layer_height_0", "value"))
            nozzle_size_line = ";Nozzle Size T0: " + str(Application.getInstance().getGlobalContainerStack().extruderList[0].getProperty("machine_nozzle_size", "value"))            
            filament_type = "\n;Filament type for T0: " + str(Application.getInstance().getGlobalContainerStack().extruderList[0].getProperty("material_type", "value"))
            if extruder_count > 1:
                nozzle_size_line += "\n;Nozzle Size T1: " + str(Application.getInstance().getGlobalContainerStack().extruderList[1].getProperty("machine_nozzle_size", "value"))
                filament_type += "\n;Filament type for T1: " + str(Application.getInstance().getGlobalContainerStack().extruderList[1].getProperty("material_type", "value"))
            lines = data[0].split("\n")
            for index, line in enumerate(lines):
                if line.startswith(";Layer height:"):
                    lines[index] += "\n" + init_layer_hgt_line + "\n" + nozzle_size_line
                if line.startswith(";Filament used"):
                    lines[index] += filament_type
            data[0] = "\n".join(lines)
            # Get settings
            display_total_layers = self.getSettingValueByKey("display_total_layers")
            display_remaining_time = self.getSettingValueByKey("display_remaining_time")
            speed_factor = self.getSettingValueByKey("speed_factor") / 100
            m73_time = False
            m73_percent = False
            if add_m73_line and add_m73_time:
                m73_time = True
            if add_m73_line and add_m73_percent:
                m73_percent = True
            if add_m73_line:
                data[1] = "M75\n" + data[1]
                data[len(data)-1] += "M77\n"
            # Initialize some variables
            first_layer_index = 0
            time_total = int(data[0].split(";TIME:")[1].split("\n")[0])
            number_of_layers = 0
            time_elapsed = 0

            # If at least one of the settings is disabled, there is enough room on the display to display "layer"
            first_section = data[0]
            lines = first_section.split("\n")
            for line in lines:
                if line.startswith(";TIME:"):
                    tindex = lines.index(line)
                    cura_time = int(line.split(":")[1])
                    print_time = cura_time * speed_factor
                    hhh = print_time/3600
                    hr = round(hhh // 1)
                    mmm = round((hhh % 1) * 60)
                    orig_hhh = cura_time/3600
                    orig_hr = round(orig_hhh // 1)
                    orig_mmm = math.floor((orig_hhh % 1) * 60)
                    if add_m118_line: lines.insert(tindex + 6,"M118 Adjusted Print Time " + str(hr) + "hr " + str(mmm) + "min")
                    if add_m117_line: lines.insert(tindex + 6,"M117 ET " + str(hr) + "hr " + str(mmm) + "min")
                    # Add M73 line at beginning
                    mins = int(60 * hr + mmm)   
                    if add_m73_line and (add_m73_time or add_m73_percent):
                        if m73_time:
                            m73_str += " R{}".format(mins)
                        if m73_percent:
                            m73_str += " P0"
                        lines.insert(tindex + 4, "M73" + m73_str)
                    # If Countdown to pause is enabled then count the pauses
                    pause_str = ""
                    if bool(self.getSettingValueByKey("countdown_to_pause")):
                        pause_count = 0
                        pause_setting = self.getSettingValueByKey("pause_cmd").upper()
                        pause_cmd = []
                        if "," in pause_setting:
                            pause_cmd = pause_setting.split(",")
                        else:
                            pause_cmd.append(pause_setting)
                        for q in range(0, len(pause_cmd)):
                            pause_cmd[q] = "\n" + pause_cmd[q]
                        for num in range(2,len(data) - 2, 1):
                            for q in range(0,len(pause_cmd)):
                                if pause_cmd[q] in data[num]:
                                    pause_count += data[num].count(pause_cmd[q], 0, len(data[num]))
                        pause_str = f" with {pause_count} pause(s)"
                    # This line goes in to convert seconds to hours and minutes
                    lines.insert(tindex + 1, f";Cura Time Estimate: {orig_hr}hr {orig_mmm}min {pause_str}")
                    data[0] = "\n".join(lines)
                    if add_m117_line:
                        data[len(data)-1] += "M117 Orig Cura Est " + str(orig_hr) + "hr " + str(orig_mmm) + "min\n"
                    if add_m118_line:
                        data[len(data)-1] += "M118 Est w/FudgeFactor  " + str(speed_factor * 100) + "% was " + str(hr) + "hr " + str(mmm) + "min\n"
            if not display_total_layers or not display_remaining_time:
                base_display_text = "layer "
            else:
                base_display_text = ""
            layer = data[len(data)-1]
            data[len(data)-1] = layer.replace(";End of Gcode" + "\n", "")
            data[len(data)-1] += ";End of Gcode" + "\n"
        # Search for the number of layers and the total time from the start code
            for index in range(len(data)):
                data_section = data[index]
        # We have everything we need, save the index of the first layer and exit the loop
                if ";LAYER:" in data_section:
                    first_layer_index = index
                    break
                else:
                    for line in data_section.split("\n"):
                        if line.startswith(";LAYER_COUNT:"):
                            number_of_layers = int(line.split(":")[1])
                        if print_sequence == "one_at_a_time":
                            number_of_layers = 1
                            for lay in range(2,len(data)-1,1):
                                if ";LAYER:" in data[lay]:
                                    number_of_layers += 1
                        elif line.startswith(";TIME:"):
                            time_total = int(line.split(":")[1])
        # for all layers...
            current_layer = 0
            for layer_counter in range(len(data)-2):
                current_layer += 1
                layer_index = first_layer_index + layer_counter
                display_text = base_display_text
                display_text += str(current_layer)
        # create a list where each element is a single line of code within the layer
                lines = data[layer_index].split("\n")
                if not ";LAYER:" in data[layer_index]:
                    current_layer -= 1
                    continue
        # add the total number of layers if this option is checked
                if display_total_layers:
                    display_text += "/" + str(number_of_layers)
        # if display_remaining_time is checked, it is calculated in this loop
                if display_remaining_time:
                    time_remaining_display = " | ET "  # initialize the time display
                    m = (time_total - time_elapsed) // 60  # estimated time in minutes
                    m *= speed_factor  # correct for printing time
                    m = int(m)
                    h, m = divmod(m, 60)  # convert to hours and minutes
        # add the time remaining to the display_text
                    if h > 0:  # if it's more than 1 hour left, display format = xhxxm
                        time_remaining_display += str(h) + "h"
                        if m < 10:  # add trailing zero if necessary
                            time_remaining_display += "0"
                        time_remaining_display += str(m) + "m"
                    else:
                        time_remaining_display += str(m) + "m"
                    display_text += time_remaining_display
        # find time_elapsed at the end of the layer (used to calculate the remaining time of the next layer)
                    if not current_layer == number_of_layers:
                        for line_index in range(len(lines) - 1, -1, -1):
                            line = lines[line_index]
                            if line.startswith(";TIME_ELAPSED:"):
        # update time_elapsed for the NEXT layer and exit the loop
                                time_elapsed = int(float(line.split(":")[1]))
                                break
        # insert the text AFTER the first line of the layer (in case other scripts use ";LAYER:")
                for l_index, line in enumerate(lines):
                    if line.startswith(";LAYER:"):
                        if add_m117_line:
                            lines[l_index] += "\nM117 " + display_text
                        if add_m118_line:
                            a1_str = ""
                            p0_str = ""
                            if add_m118_a1:
                                a1_str = "A1 "                            
                            if add_m118_p0:
                                p0_str = "P0 "
                            lines[l_index] += "\nM118 " + a1_str + p0_str + display_text
                        # add M73 line
                        if display_remaining_time:
                            mins = int(60 * h + m)
                        if add_m73_line and (add_m73_time or add_m73_percent):
                            m73_str = ""
                            if m73_time and display_remaining_time:
                                m73_str += " R{}".format(mins)
                            if m73_percent:
                                m73_str += " P" + str(round(int(current_layer) / int(number_of_layers) * 100))
                            lines[l_index] += "\nM73" + m73_str
                        break
        # overwrite the layer with the modified layer
                data[layer_index] = "\n".join(lines)

        # If enabled then change the ET to TP for 'Time To Pause'
            if bool(self.getSettingValueByKey("countdown_to_pause")):
                time_list = []
                time_list.append("0")
                time_list.append("0")
                this_time = 0
                pause_index = 1

        # Get the layer times
                for num in range(2,len(data) - 1):
                    layer = data[num]
                    lines = layer.split("\n")
                    for line in lines:
                        if line.startswith(";TIME_ELAPSED:"):
                            this_time = (float(line.split(":")[1]))*speed_factor
                            time_list.append(str(this_time))
                            for p_cmd in pause_cmd:
                                if p_cmd in layer:
                                    for qnum in range(num - 1, pause_index, -1):
                                        time_list[qnum] = str(float(this_time) - float(time_list[qnum])) + "P"
                                    pause_index = num-1
                                    break

        # Make the adjustments to the M117 (and M118) lines that are prior to a pause
                for num in range (2, len(data) - 1,1):
                    layer = data[num]
                    lines = layer.split("\n")
                    for line in lines:
                        try:
                            if line.startswith("M117") and "|" in line and "P" in time_list[num]:
                                time_to_go = self.get_time_to_go(time_list[num])
                                M117_line = line.split("|")[0] + "| TP " + time_to_go
                                layer = layer.replace(line, M117_line)
                            if line.startswith("M118") and "|" in line and "P" in time_list[num]:
                                time_to_go = self.get_time_to_go(time_list[num])
                                M118_line = line.split("|")[0] + "| TP " + time_to_go
                                layer = layer.replace(line, M118_line)
                        except:
                            continue
                    data[num] = layer
            setting_data = ""
            if bool(self.getSettingValueByKey("enable_end_message")):
                message_str = self.message_to_user(speed_factor)
                Message(title = "[Display Info on LCD] - Estimated Finish Time", text = message_str[0] + "\n\n" + message_str[1] + "\n" + message_str[2] + "\n" + message_str[3]).show()
        return data

    def message_to_user(self, speed_factor: float):
        # Message the user of the projected finish time of the print
        print_time = Application.getInstance().getPrintInformation().currentPrintTime.getDisplayString(DurationFormat.Format.ISO8601)
        print_start_time = self.getSettingValueByKey("print_start_time")
        # If the user entered a print start time make sure it is in the correct format or ignore it.
        if print_start_time == "" or print_start_time == "0" or len(print_start_time) != 5 or not ":" in print_start_time:
            print_start_time = ""
        # Change the print start time to proper time format, or, use the current time
        if print_start_time != "":
            hr = int(print_start_time.split(":")[0])
            min = int(print_start_time.split(":")[1])
            sec = 0
        else:
            hr = int(time.strftime("%H"))
            min = int(time.strftime("%M"))
            sec = int(time.strftime("%S"))

        #Get the current data/time info
        yr = int(time.strftime("%Y"))
        day = int(time.strftime("%d"))
        mo = int(time.strftime("%m"))

        date_and_time = datetime.datetime(yr, mo, day, hr, min, sec)
        #Split the Cura print time
        pr_hr = int(print_time.split(":")[0])
        pr_min = int(print_time.split(":")[1])
        pr_sec = int(print_time.split(":")[2])
        #Adjust the print time if none was entered
        print_seconds = pr_hr*3600 + pr_min*60 + pr_sec
        #Adjust the total seconds by the Fudge Factor
        adjusted_print_time = print_seconds * speed_factor
        #Break down the adjusted seconds back into hh:mm:ss
        adj_hr = int(adjusted_print_time/3600)
        print_seconds = adjusted_print_time - (adj_hr * 3600)
        adj_min = int(print_seconds) / 60
        adj_sec = int(print_seconds - (adj_min * 60))
        #Get the print time to add to the start time
        time_change = datetime.timedelta(hours=adj_hr, minutes=adj_min, seconds=adj_sec)
        new_time = date_and_time + time_change
        #Get the day of the week that the print will end on
        week_day = str(["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][int(new_time.strftime("%w"))])
        #Get the month that the print will end in
        mo_str = str(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][int(new_time.strftime("%m"))-1])
        #Make adjustments from 24hr time to 12hr time
        if int(new_time.strftime("%H")) > 12:
            show_hr = str(int(new_time.strftime("%H")) - 12) + ":"
            show_ampm = " PM"
        elif int(new_time.strftime("%H")) == 0:
            show_hr = "12:"
            show_ampm = " AM"
        else:
            show_hr = str(new_time.strftime("%H")) + ":"
            show_ampm = " AM"
        if print_start_time == "":
            start_str = "Now"
        else:
            start_str = "and your entered 'print start time' of " + print_start_time + "hrs."
        if print_start_time != "":
            print_start_str = "Print Start Time................." + str(print_start_time) + "hrs"
        else:
            print_start_str = "Print Start Time.................Now"
        estimate_str = "Cura Time Estimate.........." + str(print_time)
        adjusted_str = "Adjusted Time Estimate..." + str(time_change)
        finish_str = week_day + " " + str(mo_str) + " " + str(new_time.strftime("%d")) + ", " + str(new_time.strftime("%Y")) + " at " + str(show_hr) + str(new_time.strftime("%M")) + str(show_ampm)
        return finish_str, estimate_str, adjusted_str, print_start_str
        
    def get_time_to_go(self, time_str: str):    
        alt_time = time_str[:-1]
        hhh = int(float(alt_time) / 3600)
        if hhh > 0:
            hhr = str(hhh) + "h"
        else:
            hhr = ""
        mmm = ((float(alt_time) / 3600) - (int(float(alt_time) / 3600))) * 60
        sss = int((mmm - int(mmm)) * 60)
        mmm = str(round(mmm)) + "m"
        time_to_go = str(hhr) + str(mmm)
        if hhr == "": time_to_go = time_to_go + str(sss) + "s"
        return time_to_go