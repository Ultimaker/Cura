# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import TYPE_CHECKING

from Charon.VirtualFile import VirtualFile

from UM.Mesh.MeshReader import MeshReader
from UM.MimeTypeDatabase import MimeType, MimeTypeDatabase
from UM.PluginRegistry import PluginRegistry

if TYPE_CHECKING:
    from cura.Scene.CuraSceneNode import CuraSceneNode


class UFPReader(MeshReader):

    def __init__(self) -> None:
        super().__init__()

        MimeTypeDatabase.addMimeType(
            MimeType(
                name = "application/x-ufp",
                comment = "UltiMaker Format Package",
                suffixes = ["ufp"]
            )
        )
        self._supported_extensions = [".ufp"]

    def _read(self, file_name: str) -> "CuraSceneNode":
        # Open the file
        archive = VirtualFile()
        archive.open(file_name)
        # Get the gcode data from the file
        gcode_data = archive.getData("/3D/model.gcode")
        # Convert the bytes stream to string
        gcode_stream = gcode_data["/3D/model.gcode"].decode("utf-8")

        # Open the GCodeReader to parse the data
        gcode_reader = PluginRegistry.getInstance().getPluginObject("GCodeReader")  # type: ignore
        gcode_reader.preReadFromStream(gcode_stream)  # type: ignore
        return gcode_reader.readFromStream(gcode_stream, file_name)  # type: ignore
