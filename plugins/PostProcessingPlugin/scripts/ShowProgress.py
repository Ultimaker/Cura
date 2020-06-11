# Cura PostProcessingPlugin
# Author:   Louis Wouters
# Date:     01-06-2020
# Adapted from 'DisplayRemainingTimeOnLCD' by Gwylan Scheeren

# Description:  This plugin shows the current printing layer on your printers' LCD
#               Additionally it can show the total layers and/or the remaining printing time.

from ..Script import Script


class ShowProgress(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Show Progress",
            "key": "ShowProgress",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "display_total_layers":
                {
                    "label": "Display total layers",
                    "description": "This setting shows the total number of layers to print, next to the current layer.",
                    "type": "bool",
                    "default_value": true
                },
                "display_remaining_time":
                {
                    "label": "Display remaining time",
                    "description": "This setting shows the remaining printing time. Updated at the start of each layer",
                    "type": "bool",
                    "default_value": true
                },
                "speed_factor":
                {
                    "label": "Speed factor",
                    "description": "Tweak this value to get better estimates. Compute as: [Cura estimate]/[actual print time],
                    "type": "float",
                    "default_value": 1
                }
            }
        }"""

    def execute(self, data):
        # get settings
        display_total_layers = self.getSettingValueByKey("display_total_layers")
        display_remaining_time = self.getSettingValueByKey("display_remaining_time")
        speed_factor = self.getSettingValueByKey("speed_factor")

        # initialize function variables
        first_layer_index = 0
        time_total = 0
        number_of_layers = 0
        time_elapsed = 0

        # if at least one of the settings is disabled, there is enough room on the display to display "layer"
        if not display_total_layers or not display_remaining_time:
            base_display_text = "layer "
        else:
            base_display_text = ""

        # Search for the number of layers and the total time from the start code
        for index in range(len(data)):
            data_section = data[index]
            if data_section.startswith(";LAYER:"):  # We have everything we need, save the index of the first layer and exit the loop
                first_layer_index = index
                break
            else:
                for line in data_section.split("\n"):  # Separate into lines
                    if line.startswith(";LAYER_COUNT:"):
                        number_of_layers = int(line.split(":")[1])  # Save total layers in a variable
                    elif line.startswith(";TIME:"):
                        time_total = int(line.split(":")[1])  # Save total time in a variable

        # for all layers...
        for layer_counter in range(number_of_layers):
            current_layer = layer_counter + 1
            layer_index = first_layer_index + layer_counter
            display_text = base_display_text
            display_text += str(current_layer)

            # create a list where each element is a single line of code within the layer
            lines = data[layer_index].split("\n")

            # add the total number of layers if this option is checked
            if display_total_layers:
                display_text += "/" + str(number_of_layers)

            # if display_remaining_time is checked, it is calculated in this loop
            if display_remaining_time:
                time_remaining_display = " | ETA "  # initialize the time display
                m = (time_total - time_elapsed) // 60  # estimated time in minutes
                m /= speed_factor  # correct for printing time
                m = int(m)  # convert to integer
                h, m = divmod(m, 60)  # convert to hours and minutes

                # add the time remaining to the display_text
                if h > 0:  # if it's more than 1 hour left, display format = xHxxM
                    time_remaining_display += str(h) + "H"
                    if m < 10:  # add trailing zero if necessary
                        time_remaining_display += "0"
                    time_remaining_display += str(m) + "M"
                else:  # otherwise, show just the number of minutes
                    time_remaining_display += str(m) + "M"
                display_text += time_remaining_display

                # find time_elapsed at the end of the layer (used to calculate the remaining time of the next layer)
                if not current_layer == number_of_layers:  # We don't need to this if this is the last layer
                    for line_index in range(len(lines) - 1, -1, -1):
                        line = lines[line_index]  # store the line as a string
                        if line.startswith(";TIME_ELAPSED:"):
                            # update time_elapsed for the NEXT layer and exit the loop
                            time_elapsed = int(float(line.split(":")[1]))
                            break

            # insert the text AFTER the first line of the layer (in case other scripts use ";LAYER:")
            lines[0] = lines[0] + "\nM117 " + display_text
            # overwrite the layer with the modified layer
            data[layer_index] = "\n".join(lines)

        return data
