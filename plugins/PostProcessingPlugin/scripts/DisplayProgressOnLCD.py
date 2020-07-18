# Cura PostProcessingPlugin
# Author:   Mathias Lyngklip Kjeldgaard, Alexander Gee, ftk
# Date:     July 31, 2019
# Modified: July 18, 2020

# Description:  This plugin displays progress on the LCD. It can output the estimated time remaining and the completion percentage.

from ..Script import Script

import re
import datetime

class DisplayProgressOnLCD(Script):

    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Display Progress On LCD",
            "key": "DisplayProgressOnLCD",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "time_remaining":
                {
                    "label": "Time Remaining (message)",
                    "description": "When enabled, write Time Left: HHMMSS on the display using M117. This is updated every layer.",
                    "type": "bool",
                    "default_value": false
                },
                "time_remainingM73":
                {
                    "label": "Time Remaining (M73)",
                    "description": "When enabled, set the remaining time on the LCD using Marlin's M73 R command. This is updated every layer.",
                    "type": "bool",
                    "default_value": false
                },
                "percentage":
                {
                    "label": "Percentage",
                    "description": "When enabled, set the completion bar percentage on the LCD using Marlin's M73 P command.",
                    "type": "bool",
                    "default_value": false
                }
            }
        }"""

    # Get the time value from a line as a float.
    # Example line ;TIME_ELAPSED:1234.6789 or ;TIME:1337
    def getTimeValue(self, line):
        list_split = re.split(":", line)  # Split at ":" so we can get the numerical value
        return float(list_split[1])  # Convert the numerical portion to a float

    def outputTime(self, lines, line_index, time_left):
        # Do some math to get the time left in seconds into the right format. (HH,MM,SS)
        m, s = divmod(time_left, 60)
        h, m = divmod(m, 60)
        # Create the string
        current_time_string = "{:d}h{:02d}m{:02d}s".format(int(h), int(m), int(s))
        # And now insert that into the GCODE
        lines.insert(line_index, "M117 Time Left {}".format(current_time_string))

    def execute(self, data):
        output_time = self.getSettingValueByKey("time_remaining")
        output_timeM73 = self.getSettingValueByKey("time_remainingM73")
        output_percentage = self.getSettingValueByKey("percentage")
        line_set = {}
        if output_percentage or output_time:
            total_time = -1
            previous_layer_end_percentage = 0
            for layer in data:
                layer_index = data.index(layer)
                lines = layer.split("\n")

                for line in lines:
                    if line.startswith(";TIME:") and total_time == -1:
                        # This line represents the total time required to print the gcode
                        total_time = self.getTimeValue(line)
                        line_index = lines.index(line)

                        if output_time:
                            self.outputTime(lines, line_index, total_time)
                        if output_percentage:
                            # Emit 0 percent to sure Marlin knows we are overriding the completion percentage
                            lines.insert(line_index, "M73 P0")

                    elif line.startswith(";TIME_ELAPSED:"):
                        # We've found one of the time elapsed values which are added at the end of layers
                        
                        # If we have seen this line before then skip processing it. We can see lines multiple times because we are adding
                        # intermediate percentages before the line being processed. This can cause the current line to shift back and be
                        # encountered more than once
                        if line in line_set:
                            continue
                        line_set[line] = True

                        # If total_time was not already found then noop
                        if total_time == -1:
                            continue

                        current_time = self.getTimeValue(line)
                        line_index = lines.index(line)
                        
                        if output_time:
                            # Here we calculate remaining time
                            self.outputTime(lines, line_index, total_time - current_time)

                        if output_timeM73:
                            lines.insert(line_index, "M73 R{}".format(int((total_time - current_time)/60)))

                        if output_percentage:
                            # Calculate percentage value this layer ends at
                            layer_end_percentage = int((current_time / total_time) * 100)

                            # Figure out how many percent of the total time is spent in this layer
                            layer_percentage_delta = layer_end_percentage - previous_layer_end_percentage
                            
                            # If this layer represents less than 1 percent then we don't need to emit anything, continue to the next layer
                            if layer_percentage_delta != 0:
                                # Grab the index of the current line and figure out how many lines represent one percent
                                step = line_index / layer_percentage_delta

                                for percentage in range(1, layer_percentage_delta + 1):
                                    # We add the percentage value here as while processing prior lines we will have inserted
                                    # percentage lines before the current one. Failing to do this will upset the spacing
                                    percentage_line_index = int((percentage * step) + percentage)

                                    # Due to integer truncation of the total time value in the gcode the percentage we 
                                    # calculate may slightly exceed 100, as that is not valid we cap the value here
                                    output = min(percentage + previous_layer_end_percentage, 100)
                                    
                                    # Now insert the sanitized percentage into the GCODE
                                    lines.insert(percentage_line_index, "M73 P{}".format(output))

                                previous_layer_end_percentage = layer_end_percentage

                # Join up the lines for this layer again and store them in the data array
                data[layer_index] = "\n".join(lines)
        return data
