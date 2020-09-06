# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from ..Script import Script

from UM.Application import Application #To get the current printer's settings.
from UM.Logger import Logger

from typing import List, Tuple

class PauseAtHeight(Script):
    def __init__(self) -> None:
        super().__init__()

    def getSettingDataString(self) -> str:
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
                    "options": {"height": "Height", "layer_no": "Layer Number"},
                    "default_value": "height"
                },
                "pause_height":
                {
                    "label": "Pause Height",
                    "description": "At what height should the pause occur?",
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
                    "description": "At what layer should the pause occur?",
                    "type": "int",
                    "value": "math.floor((pause_height - 0.27) / 0.1) + 1",
                    "minimum_value": "0",
                    "minimum_value_warning": "1",
                    "enabled": "pause_at == 'layer_no'"
                },
                "pause_method":
                {
                    "label": "Method",
                    "description": "The method or gcode command to use for pausing.",
                    "type": "enum",
                    "options": {"marlin": "Marlin (M0)", "griffin": "Griffin (M0, firmware retract)", "bq": "BQ (M25)", "reprap": "RepRap (M226)", "repetier": "Repetier (@pause)"},
                    "default_value": "marlin",
                    "value": "\\\"griffin\\\" if machine_gcode_flavor==\\\"Griffin\\\" else \\\"reprap\\\" if machine_gcode_flavor==\\\"RepRap (RepRap)\\\" else \\\"repetier\\\" if machine_gcode_flavor==\\\"Repetier\\\" else \\\"bq\\\" if \\\"BQ\\\" in machine_name or \\\"Flying Bear Ghost 4S\\\" in machine_name  else \\\"marlin\\\""
                },                    
                "disarm_timeout":
                {
                    "label": "Disarm timeout",
                    "description": "After this time steppers are going to disarm (meaning that they can easily lose their positions). Set this to 0 if you don't want to set any duration.",
                    "type": "int",
                    "value": "0",
                    "minimum_value": "0",
                    "minimum_value_warning": "0",
                    "maximum_value_warning": "1800",
                    "unit": "s"
                },
                "head_park_x":
                {
                    "label": "Park Print Head X",
                    "description": "What X location does the head move to when pausing.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 190,
                    "enabled": "pause_method != \\\"griffin\\\""
                },
                "head_park_y":
                {
                    "label": "Park Print Head Y",
                    "description": "What Y location does the head move to when pausing.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 190,
                    "enabled": "pause_method != \\\"griffin\\\""
                },
                "head_move_z":
                {
                    "label": "Head move Z",
                    "description": "The Height of Z-axis retraction before parking.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 15.0,
                    "enabled": "pause_method == \\\"repetier\\\""
                },
                "retraction_amount":
                {
                    "label": "Retraction",
                    "description": "How much filament must be retracted at pause.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0,
                    "enabled": "pause_method != \\\"griffin\\\""
                },
                "retraction_speed":
                {
                    "label": "Retraction Speed",
                    "description": "How fast to retract the filament.",
                    "unit": "mm/s",
                    "type": "float",
                    "default_value": 25,
                    "enabled": "pause_method not in [\\\"griffin\\\", \\\"repetier\\\"]"
                },
                "extrude_amount":
                {
                    "label": "Extrude Amount",
                    "description": "How much filament should be extruded after pause. This is needed when doing a material change on Ultimaker2's to compensate for the retraction after the change. In that case 128+ is recommended.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0,
                    "enabled": "pause_method != \\\"griffin\\\""
                },
                "extrude_speed":
                {
                    "label": "Extrude Speed",
                    "description": "How fast to extrude the material after pause.",
                    "unit": "mm/s",
                    "type": "float",
                    "default_value": 3.3333,
                    "enabled": "pause_method not in [\\\"griffin\\\", \\\"repetier\\\"]"
                },
                "redo_layer":
                {
                    "label": "Redo Layer",
                    "description": "Redo the last layer before the pause, to get the filament flowing again after having oozed a bit during the pause.",
                    "type": "bool",
                    "default_value": false
                },
                "standby_temperature":
                {
                    "label": "Standby Temperature",
                    "description": "Change the temperature during the pause.",
                    "unit": "°C",
                    "type": "int",
                    "default_value": 0,
                    "enabled": "pause_method not in [\\\"griffin\\\", \\\"repetier\\\"]"
                },
                "display_text":
                {
                    "label": "Display Text",
                    "description": "Text that should appear on the display while paused. If left empty, there will not be any message.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "pause_method != \\\"repetier\\\""
                },
                "machine_name":
                {
                    "label": "Machine Type",
                    "description": "The name of your 3D printer model. This setting is controlled by the script and will not be visible.",
                    "default_value": "Unknown",
                    "type": "str",
                    "enabled": false
                },
                "machine_gcode_flavor":
                {
                    "label": "G-code flavor",
                    "description": "The type of g-code to be generated. This setting is controlled by the script and will not be visible.",
                    "type": "enum",
                    "options":
                    {
                        "RepRap (Marlin/Sprinter)": "Marlin",
                        "RepRap (Volumetric)": "Marlin (Volumetric)",
                        "RepRap (RepRap)": "RepRap",
                        "UltiGCode": "Ultimaker 2",
                        "Griffin": "Griffin",
                        "Makerbot": "Makerbot",
                        "BFB": "Bits from Bytes",
                        "MACH3": "Mach3",
                        "Repetier": "Repetier"
                    },
                    "default_value": "RepRap (Marlin/Sprinter)",
                    "enabled": false,
                    "default_value": ""
                },
                "custom_gcode_before_pause":
                {
                    "label": "G-code Before Pause",
                    "description": "Any custom g-code to run before the pause, for example, M300 S440 P200 to beep.",
                    "type": "str",
                    "default_value": ""
                },
                "custom_gcode_after_pause":
                {
                    "label": "G-code After Pause",
                    "description": "Any custom g-code to run after the pause, for example, M300 S440 P200 to beep.",
                    "type": "str",
                    "default_value": ""
                }
            }
        }"""

    ##  Copy machine name and gcode flavor from global stack so we can use their value in the script stack
    def initialize(self) -> None:
        super().initialize()

        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack is None or self._instance is None:
            return

        for key in ["machine_name", "machine_gcode_flavor"]:
            self._instance.setProperty(key, "value", global_container_stack.getProperty(key, "value"))

    ##  Get the X and Y values for a layer (will be used to get X and Y of the
    #   layer after the pause).
    def getNextXY(self, layer: str) -> Tuple[float, float]:
        """Get the X and Y values for a layer (will be used to get X and Y of the layer after the pause)."""
        lines = layer.split("\n")
        for line in lines:
            if line.startswith(("G0", "G1", "G2", "G3")):
                if self.getValue(line, "X") is not None and self.getValue(line, "Y") is not None:
                    x = self.getValue(line, "X")
                    y = self.getValue(line, "Y")
                    return x, y
        return 0, 0

    def execute(self, data: List[str]) -> List[str]:
        """Inserts the pause commands.

        :param data: List of layers.
        :return: New list of layers.
        """
        pause_at = self.getSettingValueByKey("pause_at")
        pause_height = self.getSettingValueByKey("pause_height")
        pause_layer = self.getSettingValueByKey("pause_layer")
        disarm_timeout = self.getSettingValueByKey("disarm_timeout")
        retraction_amount = self.getSettingValueByKey("retraction_amount")
        retraction_speed = self.getSettingValueByKey("retraction_speed")
        extrude_amount = self.getSettingValueByKey("extrude_amount")
        extrude_speed = self.getSettingValueByKey("extrude_speed")
        extrude_relative = self.getSettingValueByKey("relative_extrusion")
        park_x = self.getSettingValueByKey("head_park_x")
        park_y = self.getSettingValueByKey("head_park_y")
        move_z = self.getSettingValueByKey("head_move_z")
        layers_started = False
        redo_layer = self.getSettingValueByKey("redo_layer")
        standby_temperature = self.getSettingValueByKey("standby_temperature")
        firmware_retract = Application.getInstance().getGlobalContainerStack().getProperty("machine_firmware_retract", "value")
        control_temperatures = Application.getInstance().getGlobalContainerStack().getProperty("machine_nozzle_temp_enabled", "value")
        initial_layer_height = Application.getInstance().getGlobalContainerStack().getProperty("layer_height_0", "value")
        display_text = self.getSettingValueByKey("display_text")
        gcode_before = self.getSettingValueByKey("custom_gcode_before_pause")
        gcode_after = self.getSettingValueByKey("custom_gcode_after_pause")

        pause_method = self.getSettingValueByKey("pause_method")
        pause_command = {
            "marlin": self.putValue(M = 0),
            "griffin": self.putValue(M = 0),
            "bq": self.putValue(M = 25),
            "reprap": self.putValue(M = 226),
            "repetier": self.putValue("@pause now change filament and press continue printing")
        }[pause_method]

        # T = ExtruderManager.getInstance().getActiveExtruderStack().getProperty("material_print_temperature", "value")

        # use offset to calculate the current height: <current_height> = <current_z> - <layer_0_z>
        layer_0_z = 0
        current_z = 0
        current_height = 0
        current_layer = 0
        current_extrusion_f = 0
        got_first_g_cmd_on_layer_0 = False
        current_t = 0 #Tracks the current extruder for tracking the target temperature.
        target_temperature = {} #Tracks the current target temperature for each extruder.

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

                #Track the latest printing temperature in order to resume at the correct temperature.
                if line.startswith("T"):
                    current_t = self.getValue(line, "T")
                m = self.getValue(line, "M")
                if m is not None and (m == 104 or m == 109) and self.getValue(line, "S") is not None:
                    extruder = current_t
                    if self.getValue(line, "T") is not None:
                        extruder = self.getValue(line, "T")
                    target_temperature[extruder] = self.getValue(line, "S")

                if not layers_started:
                    continue

                # Look for the feed rate of an extrusion instruction
                if self.getValue(line, "F") is not None and self.getValue(line, "E") is not None:
                    current_extrusion_f = self.getValue(line, "F")

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
                        layer_0_z = current_z - initial_layer_height
                        got_first_g_cmd_on_layer_0 = True

                    current_height = current_z - layer_0_z
                    if current_height < pause_height:
                        continue  # Scan the enitre layer, z-changes are not always on the same/first line.

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

                # Maybe redo the last layer.
                if redo_layer:
                    prev_layer = data[index - 1]
                    layer = prev_layer + layer

                    # Get extruder's absolute position at the
                    # beginning of the redone layer.
                    # see https://github.com/nallath/PostProcessingPlugin/issues/55
                    # Get X and Y from the next layer (better position for
                    # the nozzle)
                    x, y = self.getNextXY(layer)
                    prev_lines = prev_layer.split("\n")
                    for lin in prev_lines:
                        new_e = self.getValue(lin, "E", current_e)
                        if new_e != current_e:
                            current_e = new_e
                            break

                prepend_gcode = ";TYPE:CUSTOM\n"
                prepend_gcode += ";added code by post processing\n"
                prepend_gcode += ";script: PauseAtHeight.py\n"
                if pause_at == "height":
                    prepend_gcode += ";current z: {z}\n".format(z = current_z)
                    prepend_gcode += ";current height: {height}\n".format(height = current_height)
                else:
                    prepend_gcode += ";current layer: {layer}\n".format(layer = current_layer)

                if pause_method == "repetier":
                    #Retraction
                    if not extrude_relative:  # Should already be in relative mode, then.
                        prepend_gcode += self.putValue(M = 83) + " ; switch to relative E values for any needed retraction\n"
                    if retraction_amount != 0:
                        prepend_gcode += self.putValue(G = 1, E = retraction_amount, F = 6000) + "\n"

                    #Move the head away
                    prepend_gcode += self.putValue(G = 1, Z = current_z + 1, F = 300) + " ; move up a millimeter to get out of the way\n"
                    prepend_gcode += self.putValue(G = 1, X = park_x, Y = park_y, F = 9000) + "\n"
                    if current_z < move_z:
                        prepend_gcode += self.putValue(G = 1, Z = current_z + move_z, F = 300) + "\n"

                    #Disable the E steppers
                    prepend_gcode += self.putValue(M = 84, E = 0) + "\n"

                elif pause_method != "griffin":
                    # Retraction
                    if not extrude_relative:  # Should already be in relative mode, then.
                        prepend_gcode += self.putValue(M = 83) + " ; switch to relative E values for any needed retraction\n"
                    if retraction_amount != 0:
                        if firmware_retract: #Can't set the distance directly to what the user wants. We have to choose ourselves.
                            retraction_count = 1 if control_temperatures else 3 #Retract more if we don't control the temperature.
                            for i in range(retraction_count):
                                prepend_gcode += self.putValue(G = 10) + "\n"
                        else:
                            prepend_gcode += self.putValue(G = 1, E = -retraction_amount, F = retraction_speed * 60) + "\n"

                    # Move the head away
                    prepend_gcode += self.putValue(G = 1, Z = current_z + 1, F = 300) + " ; move up a millimeter to get out of the way\n"

                    # This line should be ok
                    prepend_gcode += self.putValue(G = 1, X = park_x, Y = park_y, F = 9000) + "\n"

                    if current_z < 15:
                        prepend_gcode += self.putValue(G = 1, Z = 15, F = 300) + " ; too close to bed--move to at least 15mm\n"

                    if control_temperatures:
                        # Set extruder standby temperature
                        prepend_gcode += self.putValue(M = 104, S = standby_temperature) + " ; standby temperature\n"

                if display_text:
                    prepend_gcode += "M117 " + display_text + "\n"

                # Set the disarm timeout
                if disarm_timeout > 0:
                    prepend_gcode += self.putValue(M = 18, S = disarm_timeout) + " ; Set the disarm timeout\n"

                # Set a custom GCODE section before pause
                if gcode_before:
                    prepend_gcode += gcode_before + "\n"

                # Wait till the user continues printing
                prepend_gcode += pause_command + " ; Do the actual pause\n"

                # Set a custom GCODE section before pause
                if gcode_after:
                    prepend_gcode += gcode_after + "\n"

                if pause_method == "repetier":
                    #Push the filament back,
                    if retraction_amount != 0:
                        prepend_gcode += self.putValue(G = 1, E = retraction_amount, F = 6000) + "\n"

                    # Optionally extrude material
                    if extrude_amount != 0:
                        prepend_gcode += self.putValue(G = 1, E = extrude_amount, F = 200) + "\n"
                        prepend_gcode += self.putValue("@info wait for cleaning nozzle from previous filament") + "\n"
                        prepend_gcode += self.putValue("@pause remove the waste filament from parking area and press continue printing") + "\n"

                    # and retract again, the properly primes the nozzle when changing filament.
                    if retraction_amount != 0:
                        prepend_gcode += self.putValue(G = 1, E = -retraction_amount, F = 6000) + "\n"

                    #Move the head back
                    prepend_gcode += self.putValue(G = 1, Z = current_z + 1, F = 300) + "\n"
                    prepend_gcode += self.putValue(G = 1, X = x, Y = y, F = 9000) + "\n"
                    if retraction_amount != 0:
                        prepend_gcode += self.putValue(G = 1, E = retraction_amount, F = 6000) + "\n"

                    if current_extrusion_f != 0:
                        prepend_gcode += self.putValue(G = 1, F = current_extrusion_f) + " ; restore extrusion feedrate\n"
                    else:
                        Logger.log("w", "No previous feedrate found in gcode, feedrate for next layer(s) might be incorrect")

                    if not extrude_relative:
                        prepend_gcode += self.putValue(M = 82) + "\n"

                        # reset extrude value to pre pause value
                        prepend_gcode += self.putValue(G = 92, E = current_e) + "\n"

                elif pause_method != "griffin":
                    if control_temperatures:
                        # Set extruder resume temperature
                        prepend_gcode += self.putValue(M = 109, S = int(target_temperature.get(current_t, 0))) + " ; resume temperature\n"

                    # Push the filament back,
                    if retraction_amount != 0:
                        prepend_gcode += self.putValue(G = 1, E = retraction_amount, F = retraction_speed * 60) + "\n"

                    # Optionally extrude material
                    if extrude_amount != 0:
                        prepend_gcode += self.putValue(G = 1, E = extrude_amount, F = extrude_speed * 60) + "\n"

                    # and retract again, the properly primes the nozzle
                    # when changing filament.
                    if retraction_amount != 0:
                        prepend_gcode += self.putValue(G = 1, E = -retraction_amount, F = retraction_speed * 60) + "\n"

                    # Move the head back
                    if current_z < 15:
                        prepend_gcode += self.putValue(G = 1, Z = current_z + 1, F = 300) + "\n"
                    prepend_gcode += self.putValue(G = 1, X = x, Y = y, F = 9000) + "\n"
                    prepend_gcode += self.putValue(G = 1, Z = current_z, F = 300) + " ; move back down to resume height\n"
                    if retraction_amount != 0:
                        if firmware_retract: #Can't set the distance directly to what the user wants. We have to choose ourselves.
                            retraction_count = 1 if control_temperatures else 3 #Retract more if we don't control the temperature.
                            for i in range(retraction_count):
                                prepend_gcode += self.putValue(G = 11) + "\n"
                        else:
                            prepend_gcode += self.putValue(G = 1, E = retraction_amount, F = retraction_speed * 60) + "\n"

                    if current_extrusion_f != 0:
                        prepend_gcode += self.putValue(G = 1, F = current_extrusion_f) + " ; restore extrusion feedrate\n"
                    else:
                        Logger.log("w", "No previous feedrate found in gcode, feedrate for next layer(s) might be incorrect")

                    if not extrude_relative:
                        prepend_gcode += self.putValue(M = 82) + " ; switch back to absolute E values\n"

                if not extrude_relative:
                    # reset extrude value to pre pause value
                    prepend_gcode += self.putValue(G = 92, E = current_e) + "\n"

                layer = prepend_gcode + layer

                # Override the data of this layer with the
                # modified data
                data[index] = layer
                return data
        return data
