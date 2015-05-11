# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Mesh.MeshWriter import MeshWriter
from UM.Logger import Logger
from UM.Application import Application
import io


class GCodeWriter(MeshWriter):
    def __init__(self):
        super().__init__()
        self._gcode = None

    def write(self, file_name, storage_device, mesh_data):
        if "gcode" in file_name:
            scene = Application.getInstance().getController().getScene()
            gcode_list = getattr(scene, "gcode_list")
            if gcode_list:
                f = storage_device.openFile(file_name, "wt")
                Logger.log("d", "Writing GCode to file %s", file_name)
                for gcode in gcode_list:
                    f.write(gcode)
                storage_device.closeFile(f)
                return True

        return False
