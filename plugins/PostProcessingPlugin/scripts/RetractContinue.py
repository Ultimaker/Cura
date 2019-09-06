# Copyright (c) 2019 Ultimaker B.V.
# The PostProcessingPlugin is released under the terms of the AGPLv3 or higher.

import math

from ..Script import Script

##  Continues retracting during all travel moves.
class RetractContinue(Script):
    def getSettingDataString(self):
        return """{
            "name": "Retract Continue",
            "key": "RetractContinue",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "extra_retraction_speed":
                {
                    "label": "Extra Retraction Speed",
                    "description": "How much does it retract during the travel move, by ratio of the travel length.",
                    "type": "float",
                    "default_value": 0.05
                }
            }
        }"""

    def execute(self, data):
        current_e = 0
        current_x = 0
        current_y = 0
        extra_retraction_speed = self.getSettingValueByKey("extra_retraction_speed")

        for layer_number, layer in enumerate(data):
            lines = layer.split("\n")
            for line_number, line in enumerate(lines):
                if self.getValue(line, "G") in {0, 1}:  # Track X,Y location.
                    current_x = self.getValue(line, "X", current_x)
                    current_y = self.getValue(line, "Y", current_y)
                if self.getValue(line, "G") == 1:
                    if self.getValue(line, "E"):
                        new_e = self.getValue(line, "E")
                        if new_e >= current_e:  # Not a retraction.
                            continue
                        # A retracted travel move may consist of multiple commands, due to combing.
                        # This continues retracting over all of these moves and only unretracts at the end.
                        delta_line = 1
                        dx = current_x  # Track the difference in X for this move only to compute the length of the travel.
                        dy = current_y
                        while line_number + delta_line < len(lines) and self.getValue(lines[line_number + delta_line], "G") != 1:
                            travel_move = lines[line_number + delta_line]
                            if self.getValue(travel_move, "G") != 0:
                                delta_line += 1
                                continue
                            travel_x = self.getValue(travel_move, "X", dx)
                            travel_y = self.getValue(travel_move, "Y", dy)
                            f = self.getValue(travel_move, "F", "no f")
                            length = math.sqrt((travel_x - dx) * (travel_x - dx) + (travel_y - dy) * (travel_y - dy))  # Length of the travel move.
                            new_e -= length * extra_retraction_speed  # New retraction is by ratio of this travel move.
                            if f == "no f":
                                new_travel_move = "G1 X{travel_x} Y{travel_y} E{new_e}".format(travel_x = travel_x, travel_y = travel_y, new_e = new_e)
                            else:
                                new_travel_move = "G1 F{f} X{travel_x} Y{travel_y} E{new_e}".format(f = f, travel_x = travel_x, travel_y = travel_y, new_e = new_e)
                            lines[line_number + delta_line] = new_travel_move

                            delta_line += 1
                            dx = travel_x
                            dy = travel_y

                        current_e = new_e

            new_layer = "\n".join(lines)
            data[layer_number] = new_layer

        return data