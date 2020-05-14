# Cura PostProcessingPlugin
# Author:   Mathias Lyngklip Kjeldgaard, Alexander Gee
# Date:     July 31, 2019
# Modified: May 13, 2020

# Description:  This plugin displays progress on the LCD. It can output the estimated time remaining and the completion percentage.

from ..Script import Script

import re
import datetime

class DisplayPercentCompleteOnLCD(Script):

    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name":"Display Percent Complete on LCD",
            "key":"DisplayPercentCompleteOnLCD",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "TimeRemaining":
                {
                    "label": "Enable",
                    "description": "When enabled, write Time Left: HHMMSS on the display using M117. This is updated every layer.",
                    "type": "bool",
                    "default_value": false
                }
            }
            {
                "Percentage":
                {
                    "label": "Enable",
                    "description": "When enabled, set the completion bar percentage on the LCD using Marlin's M73 command.",
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

    def execute(self, data):
        output_time = self.getSettingValueByKey("TimeRemaining")
        output_percentage = self.getSettingValueByKey("Percentage")
        if (output_percentage or output_time) == True:
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

                        if (output_time):
                            m, s = divmod(total_time, 60)    # Math to calculate
                            h, m = divmod(m, 60)             # hours, minutes and seconds.
                            total_time_string = "{:d}h{:02d}m{:02d}s".format(h, m, s)           # Now we put it into the string
                            lines.insert(line_index, "M117 Time Left {}".format(total_time_string))   # And print that string instead of the original one
                        if (output_percentage):
                            # Emit 0 percent to sure Marlin knows we are overriding the completion percentage
                            lines.insert(line_index,"M73 P0")


                    elif line.startswith(";TIME_ELAPSED:"):
                        # We've found one of the time elapsed values which are added at the end of layers

                        # If total_time was not already found then noop
                        if (total_time == -1):
                            continue

                        current_time = self.getTimeValue(line)
                        line_index = lines.index(line)
                        
                        if (output_time):
                            # Here we calculate remaining time and do some math to get the total time in seconds into the right format. (HH,MM,SS)
                            time_left = total_time - current_time
                            m1, s1 = divmod(time_left, 60)
                            h1, m1 = divmod(m1, 60)
                             # Here we create the string holding our time
                            current_time_string = "{:d}h{:2d}m{:2d}s".format(int(h1), int(m1), int(s1))
                             # And now insert that into the GCODE
                            lines.insert(line_index, "M117 Time Left {}".format(current_time_string))

                        if (output_percentage):
                            # Calculate percentage value this layer ends at
                            layer_end_percentage = int((current_time / total_time) * 100)

                            # Figure out how many percent of the total time is spent in this layer
                            layer_percentage_delta = layer_end_percentage - previous_layer_end_percentage
                            
                            # If this layer represents less than 1 percent then we don't need to emit anything, continue to the next layer
                            if (layer_percentage_delta != 0):
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
                data[layer_index] =  "\n".join(lines)
        return data
