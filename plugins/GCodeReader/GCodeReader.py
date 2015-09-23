# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Mesh.MeshReader import MeshReader

from cura.LayerData import LayerData
from cura.LayerDataDecorator import LayerDataDecorator

import os

class GCodeReader(MeshReader):
    def __init__(self):
        super().__init__()
        self._supported_extension = ".gcode"

    def read(self, file_name):
        extension = os.path.splitext(file_name)[1]
        if extension.lower() == self._supported_extension:
            with open (file_name,"rt") as f:
                for line in f:
                    pass