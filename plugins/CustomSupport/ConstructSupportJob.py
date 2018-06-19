# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtGui import QImage

from UM.Job import Job #The interface we're implementing.
from UM.Logger import Logger

##  Background task to process an image of where the user would like support.
#
#   The coordinates on the cursor are projected onto the scene to place a mesh
#   that creates or removes support.
class ConstructSupportJob(Job):
    def __init__(self, buffer: QImage):
        super().__init__()
        self._buffer = buffer

    def run(self):
        Logger.log("d", "Constructing/removing support.")
        #TODO