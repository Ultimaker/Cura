# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Mesh.MeshWriter import MeshWriter
from UM.Logger import Logger
from UM.Application import Application
import io
import re


class GCodeWriter(MeshWriter):
    def __init__(self):
        super().__init__()

    def write(self, stream, node, mode = MeshWriter.OutputMode.TextMode):
        if mode != MeshWriter.OutputMode.TextMode:
            Logger.log("e", "GCode Writer does not support non-text mode")
            return False

        scene = Application.getInstance().getController().getScene()
        gcode_list = getattr(scene, "gcode_list")
        if gcode_list:
            
            # start extrusion safety check
            check_lines = []
            for layer in gcode_list:
                check_lines.extend(layer.split("\n"))
            cur_extrude = 0.0;
            extrude_safety = 10.0;
            for i, line in enumerate(check_lines):
                match = re.search(r'E([0-9.]+)', line)
                if match:
                    extrude = float( match.group(1) )
                    if extrude > cur_extrude + extrude_safety:
                        Logger.log("e", "GCode is not safe! Extrusion gap from "+str(cur_extrude)+" to "+str(extrude))
                        return False
                    cur_extrude = extrude
            # end extrusion safety check                        

            for gcode in gcode_list:
                stream.write(gcode)
            return True

        return False
