# Copyright (c) 2015 Ultimaker B.V.
# Copyright (c) 2013 David Braam
# Uranium is released under the terms of the AGPLv3 or higher.

from UM.Mesh.MeshReader import MeshReader
from UM.Mesh.MeshBuilder import MeshBuilder
import os
from UM.Scene.SceneNode import SceneNode
from UM.Math.Vector import Vector

from UM.Job import Job

class GCODEReader(MeshReader):
    def __init__(self):
        super(GCODEReader, self).__init__()
        self._supported_extensions = [".gcode", ".g"]

    def read(self, file_name):
        scene_node = None

        extension = os.path.splitext(file_name)[1]
        if extension.lower() in self._supported_extensions:
            scene_node = SceneNode()

            mesh_builder = MeshBuilder()
            mesh_builder.setFileName(file_name)

            mesh_builder.addCube(
                width=5,
                height=5,
                depth=5,
                center=Vector(0, 2.5, 0)
            )

            scene_node.setMeshData(mesh_builder.build())

            scene_node.setEnabled(False)
            scene_node.setSelectable(False)

        return scene_node
