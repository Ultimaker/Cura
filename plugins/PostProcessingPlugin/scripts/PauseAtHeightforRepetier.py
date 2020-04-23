from UM.Logger import Logger
from ..Script import Script
class PauseAtHeightforRepetier(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name":"Pause at height for repetier",
            "key": "PauseAtHeightforRepetier",
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
                },
                "head_park_x":
                {
                    "label": "Park print head X",
                    "description": "What x location does the head move to when pausing.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 5.0
                },
                "head_park_y":
                {
                    "label": "Park print head Y",
                    "description": "What y location does the head move to when pausing.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 5.0
                },
                "head_move_Z":
                {
                    "label": "Head move Z",
                    "description": "The Hieght of Z-axis retraction before parking.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 15.0
                },
                "retraction_amount":
                {
                    "label": "Retraction",
                    "description": "How much fillament must be retracted at pause.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 5.0
                },
                "extrude_amount":
                {
                    "label": "Extrude amount",
                    "description": "How much filament should be extruded after pause. This is needed when doing a material change on Ultimaker2's to compensate for the retraction after the change. In that case 128+ is recommended.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 90.0
                },
                "redo_layers":
                {
                    "label": "Redo layers",
                    "description": "Redo a number of previous layers after a pause to increases adhesion.",
                    "unit": "layers",
                    "type": "int",
                    "default_value": 0
                },
                ,
                "custom_gcode_before_pause":
                {
                    "label": "GCODE Before Pause",
                    "description": "Any custom GCODE to run before the pause, for example, M300 S300 P1000 to beep.",
                    "type": "str",
                    "default_value": ""
                },
                "custom_gcode_after_pause":
                {
                    "label": "GCODE After Pause",
                    "description": "Any custom GCODE to run after the pause, for example, M300 S300 P1000 to beep.",
                    "type": "str",
                    "default_value": ""
                }
            }
        }"""

    def execute(self, data):
        x = 0.
        y = 0.
        current_extrusion_f = 0
        current_z = 0.
        pause_z = self.getSettingValueByKey("pause_height")
        retraction_amount = self.getSettingValueByKey("retraction_amount")
        extrude_amount = self.getSettingValueByKey("extrude_amount")
        park_x = self.getSettingValueByKey("head_park_x")
        park_y = self.getSettingValueByKey("head_park_y")
        move_Z = self.getSettingValueByKey("head_move_Z")
        layers_started = False
        redo_layers = self.getSettingValueByKey("redo_layers")
        gcode_before = self.getSettingValueByKey("custom_gcode_before_pause")
        gcode_after = self.getSettingValueByKey("custom_gcode_after_pause")

        for layer in data:
            lines = layer.split("\n")
            for line in lines:
                if ";LAYER:0" in line:
                    layers_started = True
                    continue

                if not layers_started:
                    continue

                if self.getValue(line, 'G') == 1 or self.getValue(line, 'G') == 0:
                    current_z = self.getValue(line, 'Z')
                    if self.getValue(line, 'F') is not None and self.getValue(line, 'E') is not None:
                        current_extrusion_f = self.getValue(line, 'F', current_extrusion_f)
                    x = self.getValue(line, 'X', x)
                    y = self.getValue(line, 'Y', y)
                    if current_z is not None:
                        if current_z >= pause_z:

                            index = data.index(layer)
                            prevLayer = data[index-1]
                            prevLines = prevLayer.split("\n")
                            current_e = 0.
                            for prevLine in reversed(prevLines):
                                current_e = self.getValue(prevLine, 'E', -1)
                                if current_e >= 0:
                                    break

                            prepend_gcode = ";TYPE:CUSTOM\n"
                            prepend_gcode += ";added code by post processing\n"
                            prepend_gcode += ";script: PauseAtHeightforRepetier.py\n"
                            prepend_gcode += ";current z: %f \n" % (current_z)
                            prepend_gcode += ";current X: %f \n" % (x)
                            prepend_gcode += ";current Y: %f \n" % (y)

                            #Retraction
                            prepend_gcode += "M83\n"
                            if retraction_amount != 0:
                                prepend_gcode += "G1 E-%f F6000\n" % (retraction_amount)

                            #Move the head away
                            prepend_gcode += "G1 Z%f F300\n" % (1 + current_z)
                            prepend_gcode += "G1 X%f Y%f F9000\n" % (park_x, park_y)
                            if current_z < move_Z:
                                prepend_gcode += "G1 Z%f F300\n" % (current_z + move_Z)

                            #Disable the E steppers
                            prepend_gcode += "M84 E0\n"

                            # Set a custom GCODE section before pause
                            if gcode_before:
                                prepend_gcode += gcode_before + "\n"

                            #Wait till the user continues printing
                            prepend_gcode += "@pause now change filament and press continue printing ;Do the actual pause\n"

                            # Set a custom GCODE section before pause
                            if gcode_after:
                                prepend_gcode += gcode_after + "\n"

                            #Push the filament back,
                            if retraction_amount != 0:
                                prepend_gcode += "G1 E%f F6000\n" % (retraction_amount)

                            # Optionally extrude material
                            if extrude_amount != 0:
                                prepend_gcode += "G1 E%f F200\n" % (extrude_amount)
                                prepend_gcode += "@info wait for cleaning nozzle from previous filament\n"
                                prepend_gcode += "@pause  remove the waste filament from parking area and press continue printing\n"

                            # and retract again, the properly primes the nozzle when changing filament.
                            if retraction_amount != 0:
                                prepend_gcode += "G1 E-%f F6000\n" % (retraction_amount)

                            #Move the head back
                            prepend_gcode += "G1 Z%f F300\n" % (1 + current_z)
                            prepend_gcode +="G1 X%f Y%f F9000\n" % (x, y)
                            if retraction_amount != 0:
                                prepend_gcode +="G1 E%f F6000\n" % (retraction_amount)

                            if current_extrusion_f != 0:
                                prepend_gcode += self.putValue(G=1, F=current_extrusion_f) + " ; restore extrusion feedrate\n"
                            else:
                                Logger.log("w", "No previous feedrate found in gcode, feedrate for next layer(s) might be incorrect")

                            prepend_gcode +="M82\n"

                            # reset extrude value to pre pause value
                            prepend_gcode +="G92 E%f\n" % (current_e)

                            layer = prepend_gcode + layer

                            # include a number of previous layers
                            for i in range(1, redo_layers + 1):
                                prevLayer = data[index-i]
                                layer = prevLayer + layer

                            data[index] = layer #Override the data of this layer with the modified data
                            return data
                        break
        return data
