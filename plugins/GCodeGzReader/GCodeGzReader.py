# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import gzip

from UM.Mesh.MeshReader import MeshReader #The class we're extending/implementing.
from UM.PluginRegistry import PluginRegistry


##  A file reader that reads gzipped g-code.
#
#   If you're zipping g-code, you might as well use gzip!
class GCodeGzReader(MeshReader):

    def __init__(self):
        super().__init__()
        self._supported_extensions = [".gcode.gz"]

    def read(self, file_name):
        with open(file_name, "rb") as file:
            file_data = file.read()
        uncompressed_gcode = gzip.decompress(file_data).decode("utf-8")
        PluginRegistry.getInstance().getPluginObject("GCodeReader").preReadFromStream(uncompressed_gcode)
        result = PluginRegistry.getInstance().getPluginObject("GCodeReader").readFromStream(uncompressed_gcode)

        return result
