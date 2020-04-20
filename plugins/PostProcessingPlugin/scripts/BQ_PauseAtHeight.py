from ..Script import Script
class BQ_PauseAtHeight(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name":"Pause at height (BQ Printers)",
            "key": "BQ_PauseAtHeight",
            "metadata":{},
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
        pause_z = self.getSettingValueByKey("pause_height")
        for layer in data: 
            lines = layer.split("\n")
            for line in lines:
                if self.getValue(line, 'G') == 1 or self.getValue(line, 'G') == 0:
                    current_z = self.getValue(line, 'Z')
                    if current_z is not None:
                        if current_z >= pause_z:
                            prepend_gcode = ";TYPE:CUSTOM\n"
                            prepend_gcode += "; -- Pause at height (%.2f mm) --\n" % pause_z

                            # Insert Pause gcode
                            prepend_gcode += "M25        ; Pauses the print and waits for the user to resume it\n"
                            
                            index = data.index(layer) 
                            layer = prepend_gcode + layer
                            data[index] = layer # Override the data of this layer with the modified data
                            return data
                        break
        return data
