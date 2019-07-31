
from ..Script import Script

import re
import datetime


class DisplayRemainingTimeOnLCD(Script):

    def __init__(self):
        super().__init__()


    def getSettingDataString(self):
        return """{
            "name":"Disaplay Remaining Time on LCD",
            "key":"DisplayRemainingTimeOnLCD",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "TurnOn":
                {
                    "label": "Enable",
                    "description": "When enabled, It will write Time Left HHMMSS on the display",
                    "type": "bool",
                    "default_value": true
                }
            }
        }"""

    def execute(self, data):
        if self.getSettingValueByKey("TurnOn"):
            TotalTime = 0           # Var for total time
            TotalTimeString = ""    # Var for the string we insert
            for layer in data:
                layer_index = data.index(layer)
                lines = layer.split("\n")
                for line in lines:
                    if line.startswith(";TIME:"):
                        # At this point, we have found a line in the GCODE with ";TIME:"
                        # which is the indication of TotalTime. Looks like: ";TIME:1337", where
                        # 1337 is the total print time in seconds.
                        line_index = lines.index(line)      # We take a hold of that line
                        minString = re.split(":", line)     # Then we split it, so we can get the number

                        StringMedTal = "{}".format(minString[1])    # Here we insert that number from the
                                                                    # list into a string.

                        TotalTime = int(StringMedTal)               # Only to contert it to a int.

                        m, s = divmod(TotalTime, 60)    # Math to calculate
                        h, m = divmod(m, 60)            # hours, minutes and seconds.
                        TotalTimeString = "{:d}h{:02d}m{:02d}s".format(h, m, s) # Now we put it into the string
                        lines[line_index] = "M117 Time Left: {}".format(TotalTimeString) # And print that string instead of the original one




                    elif line.startswith(";TIME_ELAPSED:"):

                        # As we didnt find the total time (";TIME:"), we have found a elapsed time mark
                        # This time represents the time the printer have printed. So with some math;
                        # totalTime - printTime = RemainingTime.
                        line_index = lines.index(line)          # We get a hold of the line
                        myList = re.split(":", line)            # Again, we split at ":" so we can get the number
                        StringMedTal = "{}".format(myList[1])   # Then we put that number from the list, into a string

                        currentTime = float(StringMedTal)       # This time we convert to a float, as the line looks something like:
                                                                # ;TIME_ELAPSED:1234.6789
                                                                # which is total time in seconds

                        timeLeft = TotalTime - currentTime      # Here we calculate remaining time

                        m1, s1 = divmod(timeLeft, 60)           # And some math to get the total time in seconds into
                        h1, m1 = divmod(m1, 60)                 # the right format. (HH,MM,SS)
                        currentTimeString = "{:d}h{:2d}m{:2d}s".format(int(h1), int(m1), int(s1))   # Here we create the string holding our time
                        lines[line_index] = "M117 Time Left: {}".format(currentTimeString)           # And now insert that into the GCODE


                # Here we are OUT of the second for-loop
                # Which means we have found and replaces all the occurences.
                # Which also means we are ready to join the lines for that section of the GCODE file.
                final_lines = "\n".join(lines)
                data[layer_index] = final_lines
        return data
