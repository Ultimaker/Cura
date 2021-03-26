from ..Script import Script
# from cura.Settings.ExtruderManager import ExtruderManager

class PauseAtHeightDynamical3D(Script):
    def __init__(self):
        super().__init__()
        self._script_list = []  # type: List[Script]
        self._selected_script_index = -1

    def getSettingDataString(self):
        return """{
            "name":"Pause at height - Dynamical3D",
            "key": "PauseAtHeightDynamical3D",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "pause_height":
                {
                    "label": "Pause Height",
                    "description": "At what height should the pause occur.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 5.0
                }
            }
        }"""

    def execute(self, data: list):

        """data is a list. Each index contains a layer"""

        current_z = 0.
        layers_started = False
        pause_height = self.getSettingValueByKey("pause_height")

        # use offset to calculate the current height: <current_height> = <current_z> - <layer_0_z>
        layer_0_z = 0.
        got_first_g_cmd_on_layer_0 = False
        for layer in data:
            lines = layer.split("\n")
            for line in lines:
                if ";LAYER:0" in line:
                    layers_started = True
                    continue

                if not layers_started:
                    continue

                if (self.getValue(line, 'G') == 1 or self.getValue(line, 'G') == 0) and 'X' in line and 'Y' in line and 'Z' in line:
                    current_z = self.getValue(line, 'Z')
                    if not got_first_g_cmd_on_layer_0:
                        layer_0_z = current_z
                        got_first_g_cmd_on_layer_0 = True

                    if current_z is not None:
                        current_height = current_z - layer_0_z
                        if current_height >= pause_height:
                            index = data.index(layer)

                            prepend_gcode = ";TYPE:CUSTOM\n"
                            prepend_gcode += ";added code by post processing\n"
                            prepend_gcode += ";script: Pause at height - Dynamical3D.py\n"
                            prepend_gcode += ";current z: %f \n" % current_z
                            prepend_gcode += ";current height: %f \n" % current_height
                            prepend_gcode += "M0 ;stop\n"
                            layer = prepend_gcode + layer

                            # Override the data of this layer with the
                            # modified data
                            data[index] = layer
                            return data
                        break
        return data
