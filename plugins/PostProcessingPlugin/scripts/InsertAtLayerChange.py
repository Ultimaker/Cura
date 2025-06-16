# Copyright (c) 2020 Ultimaker B.V.
# Created by Wayne Porter
# Re-write in April of 2024 by GregValiant (Greg Foresi)
# Made convert inserted text to upper-case optional March 2025 by HellAholic
# Changes:
#     Added an 'Enable' setting
#     Added support for multi-line insertions (comma delimited)
#     Added insertions in a range of layers or a single insertion at a layer.  Numbers are consistent with the Cura Preview (base1)
#     Added frequency of Insertion (once only, every layer, every 2nd, 3rd, 5th, 10th, 25th, 50th, 100th)
#     Added support for 'One at a Time' print sequence
#     Rafts are allowed and accounted for but no insertions are made in raft layers

from ..Script import Script
import re
from UM.Application import Application

class InsertAtLayerChange(Script):

    def getSettingDataString(self):
        return """{
            "name": "Insert at Layer Change",
            "key": "InsertAtLayerChange",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "enabled":
                {
                    "label": "Enable this script",
                    "description": "You must enable the script for it to run.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                },
                "insert_frequency":
                {
                    "label": "How often to insert",
                    "description": "Every so many layers starting with the Start Layer OR as single insertion at a specific layer.  If the print sequence is 'one_at_a_time' then the insertions will be made for every model.  Insertions are made at the beginning of a layer.",
                    "type": "enum",
                    "options": {
                        "once_only": "One insertion only",
                        "every_layer": "Every Layer",
                        "every_2nd": "Every 2nd",
                        "every_3rd": "Every 3rd",
                        "every_5th": "Every 5th",
                        "every_10th": "Every 10th",
                        "every_25th": "Every 25th",
                        "every_50th": "Every 50th",
                        "every_100th": "Every 100th"},
                    "default_value": "every_layer",
                    "enabled": "enabled"
                },
                "start_layer":
                {
                    "label": "Starting Layer",
                    "description": "The layer before which the first insertion will take place.  If the Print_Sequence is 'All at Once' then use the layer numbers from the Cura Preview.  Enter '1' to start at gcode LAYER:0. In 'One at a Time' mode use the layer numbers from the first model that prints AND all models will receive the same insertions.  NOTE: There is never an insertion for raft layers.",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": 1,
                    "enabled": "insert_frequency != 'once_only' and enabled"
                },
                "end_layer":
                {
                    "label": "Ending Layer",
                    "description": "The layer before which the last insertion will take place.  Enter '-1' to indicate the entire file.  Use layer numbers from the Cura Preview.",
                    "type": "int",
                    "default_value": -1,
                    "minimum_value": -1,
                    "enabled": "insert_frequency != 'once_only' and enabled"
                },
                "single_end_layer":
                {
                    "label": "Layer # for Single Insertion.",
                    "description": "The layer before which the Gcode insertion will take place.  Use the layer numbers from the Cura Preview.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "insert_frequency == 'once_only' and enabled"
                },
                "gcode_to_add":
                {
                    "label": "G-code to insert.",
                    "description": "G-code to add at start of the layer. Use a comma to delimit multi-line commands. EX: G28 X Y,M220 S100,M117 HELL0.  NOTE:  All inserted text will be converted to upper-case as some firmwares don't understand lower-case.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "enabled"
                },
                "convert_to_upper":
                {
                    "label": "Convert to upper-case",
                    "description": "Convert all inserted text to upper-case as some firmwares don't understand lower-case.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "enabled"
                }
            }
        }"""

    def execute(self, data):
        # Exit if the script is not enabled
        if not bool(self.getSettingValueByKey("enabled")):
            return data
        #Initialize variables
        mycode = self.getSettingValueByKey("gcode_to_add").upper() if self.getSettingValueByKey("convert_to_upper") else self.getSettingValueByKey("gcode_to_add")
        start_layer = int(self.getSettingValueByKey("start_layer"))
        end_layer = int(self.getSettingValueByKey("end_layer"))
        when_to_insert = self.getSettingValueByKey("insert_frequency")
        end_list = [0]
        print_sequence = Application.getInstance().getGlobalContainerStack().getProperty("print_sequence", "value")
        # Get the topmost layer number and adjust the end_list
        if end_layer == -1:
            if print_sequence == "all_at_once":
                for lnum in range(0, len(data) - 1):
                    if ";LAYER:" in data[lnum]:
                        the_top = int(data[lnum].split(";LAYER:")[1].split("\n")[0])
                end_list[0] = the_top
            # Get the topmost layer number for each model and append it to the end_list
            if print_sequence == "one_at_a_time":
                for lnum in range(0, 10):
                    if ";LAYER:0" in data[lnum]:
                        start_at = lnum + 1
                        break
                for lnum in range(start_at, len(data)-1, 1):
                    if ";LAYER:" in data[lnum] and not ";LAYER:0" in data[lnum] and not ";LAYER:-" in data[lnum]:
                        end_list[len(end_list) - 1] = int(data[lnum].split(";LAYER:")[1].split("\n")[0])
                        continue
                    if ";LAYER:0" in data[lnum]:
                        end_list.append(0)
        elif end_layer != -1:
            if print_sequence == "all_at_once":
                # Catch an error if the entered End_Layer > the top layer in the gcode
                for e_num, layer in enumerate(data):
                    if ";LAYER:" in layer:
                        top_layer = int(data[e_num].split(";LAYER:")[1].split("\n")[0])
                end_list[0] = end_layer - 1
                if top_layer < end_layer - 1:
                    end_list[0] = top_layer
            elif print_sequence == "one_at_a_time":
                # Find the index of the first Layer:0
                for lnum in range(0, 10):
                    if ";LAYER:0" in data[lnum]:
                        start_at = lnum + 1
                        break
                # Get the top layer number for each model
                for lnum in range(start_at, len(data)-1):
                    if ";LAYER:" in data[lnum] and not ";LAYER:0" in data[lnum] and not ";LAYER:-" in data[lnum]:
                        end_list[len(end_list) - 1] = int(data[lnum].split(";LAYER:")[1].split("\n")[0])
                    if ";LAYER:0" in data[lnum]:
                        end_list.append(0)
                # Adjust the end list if an end layer was named
                for index, num in enumerate(end_list):
                    if num > end_layer - 1:
                        end_list[index] = end_layer - 1
        #If the gcode_to_enter is multi-line then replace the commas with newline characters
        if mycode != "":
            if "," in mycode:
                mycode = re.sub(",", "\n",mycode)
            gcode_to_add = mycode
        #Get the insertion frequency
        match when_to_insert:
            case "every_layer":
                freq = 1
            case "every_2nd":
                freq = 2
            case "every_3rd":
                freq = 3
            case "every_5th":
                freq = 5
            case "every_10th":
                freq = 10
            case "every_25th":
                freq = 25
            case "every_50th":
                freq = 50
            case "every_100th":
                freq = 100
            case "once_only":
                the_insert_layer = int(self.getSettingValueByKey("single_end_layer"))-1
            case _:
                raise ValueError(f"Unexpected insertion frequency {when_to_insert}")
        #Single insertion
        if when_to_insert == "once_only":
            # For print sequence 'All at once'
            if print_sequence == "all_at_once":
                for index, layer in enumerate(data):
                    if ";LAYER:" + str(the_insert_layer) + "\n" in layer:
                        lines = layer.split("\n")
                        lines.insert(1,gcode_to_add)
                        data[index] = "\n".join(lines)
                        return data
            # For print sequence 'One at a time'
            else:
                for index, layer in enumerate(data):
                    if ";LAYER:" + str(the_insert_layer) + "\n" in layer:
                        lines = layer.split("\n")
                        lines.insert(1,gcode_to_add)
                        data[index] = "\n".join(lines)
                return data
        # For multiple insertions
        if when_to_insert != "once_only":
            # Search from the line after the first Layer:0 so we know when a model ends if in One at a Time mode.
            first_0 = True
            next_layer = start_layer - 1
            end_layer = end_list.pop(0)
            for index, layer in enumerate(data):
                lines = layer.split("\n")
                for l_index, line in enumerate(lines):
                    if ";LAYER:" in line:
                        layer_number = int(line.split(":")[1])
                        if layer_number == next_layer and layer_number <= end_layer:
                            lines.insert(l_index + 1,gcode_to_add)
                            data[index] = "\n".join(lines)
                            next_layer += freq
                        # Reset the next_layer for one-at-a-time
                        if next_layer > int(end_layer):
                            next_layer = start_layer - 1
                        # Index to the next end_layer when a Layer:0 is encountered
                        try:
                            if not first_0 and layer_number == 0:
                                end_layer = end_list.pop(0)
                        except:
                            pass
                        # Beyond the initial Layer:0 futher Layer:0's indicate the top layer of a model.
                        if layer_number == 0:
                            first_0 = False
                        break
        return data