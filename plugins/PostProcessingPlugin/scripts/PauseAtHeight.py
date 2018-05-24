from ..Script import Script
# from cura.Settings.ExtruderManager import ExtruderManager

class PauseAtHeight(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Pause at height",
            "key": "PauseAtHeight",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "pause_at":
                {
                    "label": "Pause at",
                    "description": "Whether to pause at a certain height or at a certain layer.",
                    "type": "enum",
                    "options": {"height": "Height", "layer_no": "Layer No."},
                    "default_value": "height"
                },
                "pause_height":
                {
                    "label": "Pause Height",
                    "description": "At what height should the pause occur",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 5.0,
                    "minimum_value": "0",
                    "minimum_value_warning": "0.27",
                    "enabled": "pause_at == 'height'"
                },
                "pause_layer":
                {
                    "label": "Pause Layer",
                    "description": "At what layer should the pause occur",
                    "type": "int",
                    "value": "math.floor((pause_height - 0.27) / 0.1) + 1",
                    "minimum_value": "0",
                    "minimum_value_warning": "1",
                    "enabled": "pause_at == 'layer_no'"
                },
                "head_park_x":
                {
                    "label": "Park Print Head X",
                    "description": "What X location does the head move to when pausing.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 190
                },
                "head_park_y":
                {
                    "label": "Park Print Head Y",
                    "description": "What Y location does the head move to when pausing.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 190
                },
                "retraction_amount":
                {
                    "label": "Retraction",
                    "description": "How much filament must be retracted at pause.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0
                },
                "retraction_speed":
                {
                    "label": "Retraction Speed",
                    "description": "How fast to retract the filament.",
                    "unit": "mm/s",
                    "type": "float",
                    "default_value": 25
                },
                "extrude_amount":
                {
                    "label": "Extrude Amount",
                    "description": "How much filament should be extruded after pause. This is needed when doing a material change on Ultimaker2's to compensate for the retraction after the change. In that case 128+ is recommended.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0
                },
                "extrude_speed":
                {
                    "label": "Extrude Speed",
                    "description": "How fast to extrude the material after pause.",
                    "unit": "mm/s",
                    "type": "float",
                    "default_value": 3.3333
                },
                "redo_layers":
                {
                    "label": "Redo Layers",
                    "description": "Redo a number of previous layers after a pause to increases adhesion.",
                    "unit": "layers",
                    "type": "int",
                    "default_value": 0
                },
                "standby_temperature":
                {
                    "label": "Standby Temperature",
                    "description": "Change the temperature during the pause",
                    "unit": "°C",
                    "type": "int",
                    "default_value": 0
                },
                "resume_temperature":
                {
                    "label": "Resume Temperature",
                    "description": "Change the temperature after the pause",
                    "unit": "°C",
                    "type": "int",
                    "default_value": 0
                }
            }
        }"""

    def getNextXY(self, layer: str):
        """
        Get the X and Y values for a layer (will be used to get X and Y of
        the layer after the pause
        """
        lines = layer.split("\n")
        for line in lines:
            if self.getValue(line, "X") is not None and self.getValue(line, "Y") is not None:
                x = self.getValue(line, "X")
                y = self.getValue(line, "Y")
                return x, y
        return 0, 0

    def execute(self, data: list):
        """data is a list. Each index contains a layer"""
        pause_at = self.getSettingValueByKey("pause_at")
        pause_height = self.getSettingValueByKey("pause_height")
        pause_layer = self.getSettingValueByKey("pause_layer")
        retraction_amount = self.getSettingValueByKey("retraction_amount")
        retraction_speed = self.getSettingValueByKey("retraction_speed")
        extrude_amount = self.getSettingValueByKey("extrude_amount")
        extrude_speed = self.getSettingValueByKey("extrude_speed")
        park_x = self.getSettingValueByKey("head_park_x")
        park_y = self.getSettingValueByKey("head_park_y")
        layers_started = False
        redo_layers = self.getSettingValueByKey("redo_layers")
        standby_temperature = self.getSettingValueByKey("standby_temperature")
        resume_temperature = self.getSettingValueByKey("resume_temperature")

        # T = ExtruderManager.getInstance().getActiveExtruderStack().getProperty("material_print_temperature", "value")

        # use offset to calculate the current height: <current_height> = <current_z> - <layer_0_z>
        layer_0_z = 0.
        current_z = 0
        got_first_g_cmd_on_layer_0 = False

        nbr_negative_layers = 0

        for index, layer in enumerate(data):
            lines = layer.split("\n")

            # Scroll each line of instruction for each layer in the G-code
            for line in lines:
                # Fist positive layer reached
                if ";LAYER:0" in line:
                    layers_started = True
                # Count nbr of negative layers (raft)
                elif ";LAYER:-" in line:
                    nbr_negative_layers += 1
                if not layers_started:
                    continue

                # If a Z instruction is in the line, read the current Z
                if self.getValue(line, "Z") is not None:
                    current_z = self.getValue(line, "Z")

                if pause_at == "height":
                    # Ignore if the line is not G1 or G0
                    if self.getValue(line, "G") != 1 and self.getValue(line, "G") != 0:
                        continue

                    # This block is executed once, the first time there is a G
                    # command, to get the z offset (z for first positive layer)
                    if not got_first_g_cmd_on_layer_0:
                        layer_0_z = current_z
                        got_first_g_cmd_on_layer_0 = True

                    current_height = current_z - layer_0_z

                    if current_height < pause_height:
                        break  # Try the next layer.

                # Pause at layer
                else:
                    if not line.startswith(";LAYER:"):
                        continue
                    current_layer = line[len(";LAYER:"):]
                    try:
                        current_layer = int(current_layer)

                    # Couldn't cast to int. Something is wrong with this
                    # g-code data
                    except ValueError:
                        continue
                    if current_layer < pause_layer - nbr_negative_layers:
                        continue

                # Get X and Y from the next layer (better position for
                # the nozzle)
                next_layer = data[index + 1]
                x, y = self.getNextXY(next_layer)

                prev_layer = data[index - 1]
                prev_lines = prev_layer.split("\n")
                current_e = 0.

                # Access last layer, browse it backwards to find
                # last extruder absolute position
                for prevLine in reversed(prev_lines):
                    current_e = self.getValue(prevLine, "E", -1)
                    if current_e >= 0:
                        break

                # include a number of previous layers
                for i in range(1, redo_layers + 1):
                    prev_layer = data[index - i]
                    layer = prev_layer + layer

                    # Get extruder's absolute position at the
                    # beginning of the first layer redone
                    # see https://github.com/nallath/PostProcessingPlugin/issues/55
                    if i == redo_layers:
                        # Get X and Y from the next layer (better position for
                        # the nozzle)
                        x, y = self.getNextXY(layer)
                        prev_lines = prev_layer.split("\n")
                        for line in prev_lines:
                            new_e = self.getValue(line, 'E', current_e)
                            if new_e != current_e:
                                current_e = new_e
                                break

                prepend_gcode = ";TYPE:CUSTOM\n"
                prepend_gcode += ";added code by post processing\n"
                prepend_gcode += ";script: PauseAtHeight.py\n"
                if pause_at == "height":
                    prepend_gcode += ";current z: {z}\n".format(z=current_z)
                    prepend_gcode += ";current height: {height}\n".format(height=current_height)
                else:
                    prepend_gcode += ";current layer: {layer}\n".format(layer=current_layer)

                # Retraction
                prepend_gcode += self.putValue(M=83) + "\n"
                if retraction_amount != 0:
                    prepend_gcode += self.putValue(G=1, E=-retraction_amount, F=retraction_speed * 60) + "\n"

                # Move the head away
                prepend_gcode += self.putValue(G=1, Z=current_z + 1, F=300) + "\n"

                # This line should be ok
                prepend_gcode += self.putValue(G=1, X=park_x, Y=park_y, F=9000) + "\n"

                if current_z < 15:
                    prepend_gcode += self.putValue(G=1, Z=15, F=300) + "\n"

                # Disable the E steppers
                prepend_gcode += self.putValue(M=84, E=0) + "\n"

                # Set extruder standby temperature
                prepend_gcode += self.putValue(M=104, S=standby_temperature) + "; standby temperature\n"

                # Wait till the user continues printing
                prepend_gcode += self.putValue(M=0) + ";Do the actual pause\n"

                # Set extruder resume temperature
                prepend_gcode += self.putValue(M=109, S=resume_temperature) + "; resume temperature\n"

                # Push the filament back,
                if retraction_amount != 0:
                    prepend_gcode += self.putValue(G=1, E=retraction_amount, F=retraction_speed * 60) + "\n"

                # Optionally extrude material
                if extrude_amount != 0:
                    prepend_gcode += self.putValue(G=1, E=extrude_amount, F=extrude_speed * 60) + "\n"

                # and retract again, the properly primes the nozzle
                # when changing filament.
                if retraction_amount != 0:
                    prepend_gcode += self.putValue(G=1, E=-retraction_amount, F=retraction_speed * 60) + "\n"

                # Move the head back
                prepend_gcode += self.putValue(G=1, Z=current_z + 1, F=300) + "\n"
                prepend_gcode += self.putValue(G=1, X=x, Y=y, F=9000) + "\n"
                if retraction_amount != 0:
                    prepend_gcode += self.putValue(G=1, E=retraction_amount, F=retraction_speed * 60) + "\n"
                prepend_gcode += self.putValue(G=1, F=9000) + "\n"
                prepend_gcode += self.putValue(M=82) + "\n"

                # reset extrude value to pre pause value
                prepend_gcode += self.putValue(G=92, E=current_e) + "\n"

                layer = prepend_gcode + layer

                # Override the data of this layer with the
                # modified data
                data[index] = layer
                return data
        return data
