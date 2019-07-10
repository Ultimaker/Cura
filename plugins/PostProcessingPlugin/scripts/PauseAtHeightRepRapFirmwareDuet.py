from ..Script import Script

class PauseAtHeightRepRapFirmwareDuet(Script):

    def getSettingDataString(self):
        return """{
            "name": "Pause at height for RepRapFirmware DuetWifi / Duet Ethernet / Duet Maestro",
            "key": "PauseAtHeightRepRapFirmwareDuet",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "pause_height":
                {
                    "label": "Pause height",
                    "description": "At what height should the pause occur",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 5.0
                }
            }
        }"""

    def execute(self, data):
        current_z = 0.
        pause_z = self.getSettingValueByKey("pause_height")

        layers_started = False
        for layer_number, layer in enumerate(data):
            lines = layer.split("\n")
            for line in lines:
                if ";LAYER:0" in line:
                    layers_started = True
                    continue

                if not layers_started:
                    continue

                if self.getValue(line, 'G') == 1 or self.getValue(line, 'G') == 0:
                    current_z = self.getValue(line, 'Z')
                    if current_z != None:
                        if current_z >= pause_z:
                            prepend_gcode = ";TYPE:CUSTOM\n"
                            prepend_gcode += "; -- Pause at height (%.2f mm) --\n" % pause_z
                            prepend_gcode += self.putValue(M = 226) + "\n"
                            layer = prepend_gcode + layer

                            data[layer_number] = layer # Override the data of this layer with the modified data
                            return data
                        break
        return data
