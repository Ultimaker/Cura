# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Mesh.MeshReader import MeshReader
from UM.MimeTypeDatabase import MimeType, MimeTypeDatabase
from cura.Scene.CuraSceneNode import CuraSceneNode


class UFPReader(MeshReader):

    def __init__(self) -> None:
        super().__init__()

        MimeTypeDatabase.addMimeType(
            MimeType(
                name = "application/x-ufp",
                comment = "Cura UFP File",
                suffixes = ["ufp"]
            )
        )
        self._supported_extensions = [".ufp"]

    def _read(self, file_name: str) -> CuraSceneNode:
        print("Reading", file_name)