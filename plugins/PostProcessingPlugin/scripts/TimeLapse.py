# Created by Wayne Porter

from ..Script import Script

class TimeLapse(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Time Lapse",
            "key": "TimeLapse",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "trigger_cmd":
                {
                    "label": "Trigger camera command",
                    "description": "Gcode command used to trigger camera.",
                    "type": "str",
                    "default_value": "M240"
                },
                "pause_length":
                {
                    "label": "Pause length",
                    "description": "How long to wait (in ms) after camera was triggered.",
                    "type": "int",
                    "default_value": 700,
                    "minimum_value": 0,
                    "unit": "ms"
                },
                "head_park_x":
                {
                    "label": "Park Print Head X",
                    "description": "What X location does the head move to for photo.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0
                },
                "head_park_y":
                {
                    "label": "Park Print Head Y",
                    "description": "What Y location does the head move to for photo.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 190
                },
                "park_feed_rate":
                {
                    "label": "Park Feed Rate",
                    "description": "How fast does the head move to the park coordinates.",
                    "unit": "mm/s",
                    "type": "float",
                    "default_value": 9000
                }
            }
        }"""

    def execute(self, data):
        in_layer = False
        feed_rate = self.getSettingValueByKey("park_feed_rate")
        x_park = self.getSettingValueByKey("head_park_x")
        y_park = self.getSettingValueByKey("head_park_y")
        trigger_cmd = self.getSettingValueByKey("trigger_cmd")
        pause_length = self.getSettingValueByKey("pause_length")

        gcode_to_append = self.putValue(G = 90) + ";Absolute positioning\n"
        gcode_to_append += self.putValue(G = 1, F = feed_rate, X = x_park, Y = y_park) + ";Move into position\n"
        gcode_to_append += trigger_cmd + ";Snap Photo\n"
        gcode_to_append += self.putValue(G = 4, P = pause_length) + ";Wait for camera\n"
        for layer in data:
            # Check that a layer is being printed
            lines = layer.split("\n")
            if ";LAYER:" in lines[0]:
                in_layer = True
            else:
                in_layer = False

            if in_layer:
                index = data.index(layer)
                layer += gcode_to_append

                data[index] = layer

        return data
