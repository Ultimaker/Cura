# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Job import Job
from UM.Application import Application

class ProcessGCodeLayerJob(Job):
    def __init__(self, message):
        super().__init__()

        self._scene = Application.getInstance().getController().getScene()
        self._message = message

    def run(self):
        active_build_plate_id = Application.getInstance().getMultiBuildPlateModel().activeBuildPlate
        gcode_list = self._scene.gcode_dict[active_build_plate_id]
        gcode_list.append(self._message.data.decode("utf-8", "replace"))
