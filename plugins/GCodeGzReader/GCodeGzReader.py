# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import gzip
import tempfile

from io import StringIO, BufferedIOBase #To write the g-code to a temporary buffer, and for typing.
from typing import List

from UM.Logger import Logger
from UM.Mesh.MeshReader import MeshReader #The class we're extending/implementing.
from UM.PluginRegistry import PluginRegistry
from UM.Scene.SceneNode import SceneNode #For typing.

##  A file writer that writes gzipped g-code.
#
#   If you're zipping g-code, you might as well use gzip!
class GCodeGzReader(MeshReader):

    def __init__(self):
        super(GCodeGzReader, self).__init__()
        self._supported_extensions = [".gcode.gz", ".gz"]

    def read(self, file_name):
        with open(file_name, "rb") as file:
            file_data = file.read()
        uncompressed_gcode = gzip.decompress(file_data)
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(uncompressed_gcode)
            PluginRegistry.getInstance().getPluginObject("GCodeReader").preRead(temp_file.name)
            result = PluginRegistry.getInstance().getPluginObject("GCodeReader").read(temp_file.name)

        return result
