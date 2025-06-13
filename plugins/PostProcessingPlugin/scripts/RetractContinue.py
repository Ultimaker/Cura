# Copyright (c) 2023 UltiMaker B.V.
# The PostProcessingPlugin is released under the terms of the LGPLv3 or higher.

from ..Script import Script

from UM.Application import Application  # To get current absolute/relative setting.
from UM.Math.Vector import Vector

from typing import List, Tuple


class RetractContinue(Script):
    """Continues retracting during all travel moves."""

    def getSettingDataString(self) -> str:
        return """{
            "name": "Retract Continue",
            "key": "RetractContinue",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "extra_retraction_speed":
                {
                    "label": "Extra Retraction Ratio",
                    "description": "How much does it retract during the travel move, by ratio of the travel length.",
                    "type": "float",
                    "default_value": 0.05
                }
            }
        }"""

    def _getTravelMove(self, travel_move: str, default_pos: Vector) -> Tuple[Vector, float]:
        travel = Vector(
            self.getValue(travel_move, "X", default_pos.x),
            self.getValue(travel_move, "Y", default_pos.y),
            self.getValue(travel_move, "Z", default_pos.z)
        )
        f = self.getValue(travel_move, "F", -1.0)
        return travel, f

    def _travelMoveString(self, travel: Vector, f: float, e: float) -> str:
        # Note that only G1 moves are written, since extrusion is included.
        if f <= 0.0:
            return f"G1 X{travel.x:.5f} Y{travel.y:.5f} Z{travel.z:.5f} E{e:.5f}"
        else:
            return f"G1 F{f:.5f} X{travel.x:.5f} Y{travel.y:.5f} Z{travel.z:.5f} E{e:.5f}"

    def execute(self, data: List[str]) -> List[str]:
        current_e = 0.0
        to_compensate = 0  # Used when extrusion mode is relative.
        is_active = False  # Whether retract-continue is in effect.

        current_pos = Vector(0.0, 0.0, 0.0)
        last_pos = Vector(0.0, 0.0, 0.0)

        extra_retraction_speed = self.getSettingValueByKey("extra_retraction_speed")
        relative_extrusion = Application.getInstance().getGlobalContainerStack().getProperty(
            "relative_extrusion", "value"
        )

        for layer_number, layer in enumerate(data):
            lines = layer.split("\n")
            for line_number, line in enumerate(lines):

                # Focus on move-type lines.
                code_g = self.getValue(line, "G")
                if code_g not in [0, 1]:
                    continue

                # Track X,Y,Z location.
                last_pos = last_pos.set(current_pos.x, current_pos.y, current_pos.z)
                current_pos = current_pos.set(
                    self.getValue(line, "X", current_pos.x),
                    self.getValue(line, "Y", current_pos.y),
                    self.getValue(line, "Z", current_pos.z)
                )

                # Track extrusion 'axis' position.
                last_e = current_e
                e_value = self.getValue(line, "E")
                if e_value:
                    current_e = (current_e if relative_extrusion else 0) + e_value

                # Handle lines: Detect retractions and compensate relative if G1, potential retract-continue if G0.
                if code_g == 1:
                    if last_e > (current_e + 0.0001):  # Account for floating point inaccuracies.

                        # There is a retraction, each following G0 command needs to continue the retraction.
                        is_active = True
                        continue

                    elif relative_extrusion and is_active:

                        # If 'relative', the first G1 command after the total retraction will have to compensate more.
                        travel, f = self._getTravelMove(lines[line_number], current_pos)
                        lines[line_number] = self._travelMoveString(travel, f, to_compensate + e_value)
                        to_compensate = 0.0

                    # There is no retraction (see continue in the retract-clause) and everything else has been handled.
                    is_active = False

                elif code_g == 0:
                    if not is_active:
                        continue

                    # The retract-continue is active, so each G0 until the next extrusion needs to continue retraction.
                    travel, f = self._getTravelMove(lines[line_number], current_pos)
                    travel_length = (current_pos - last_pos).length()
                    extra_retract = travel_length * extra_retraction_speed
                    new_e = (0 if relative_extrusion else current_e) - extra_retract
                    to_compensate += extra_retract
                    current_e -= extra_retract
                    lines[line_number] = self._travelMoveString(travel, f, new_e)

            new_layer = "\n".join(lines)
            data[layer_number] = new_layer

        return data
