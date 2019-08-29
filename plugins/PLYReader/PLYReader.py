# Copyright (c) 2019 Ultimaker B.V., fieldOfView
# Cura is released under the terms of the LGPLv3 or higher.

# The _toMeshData function is taken from the AMFReader class which was built by fieldOfView.

import numpy  # To create the mesh data.
import os.path  # To create the mesh name for the resulting mesh.
import trimesh  # To load the PLY files into a Trimesh.

from UM.Mesh.MeshData import MeshData, calculateNormalsFromIndexedVertices
from UM.Mesh.MeshReader import MeshReader
from UM.MimeTypeDatabase import MimeTypeDatabase, MimeType

from cura.CuraApplication import CuraApplication
from cura.Scene.BuildPlateDecorator import BuildPlateDecorator
from cura.Scene.CuraSceneNode import CuraSceneNode
from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator

##  Class that leverages Trimesh to read PLY files (Stanford Triangle Format).
class PLYReader(MeshReader):
    def __init__(self) -> None:
        super().__init__()

        self._supported_extensions = [".ply"]
        MimeTypeDatabase.addMimeType(
            MimeType(
                name = "application/x-ply",  # Wikipedia lists the MIME type as "text/plain" but that won't do as it's not unique to PLY files.
                comment = "Stanford Triangle Format",
                suffixes = ["ply"]
            )
        )

    ##  Reads the PLY file.
    #   \param file_name The file path of the PLY file. This is assumed to be a
    #   PLY file; it's not checked again.
    #   \return A scene node that contains the PLY file's contents.
    def _read(self, file_name: str) -> CuraSceneNode:
        mesh = trimesh.load(file_name)
        mesh.merge_vertices()
        mesh.remove_unreferenced_vertices()
        mesh.fix_normals()
        mesh_data = self._toMeshData(mesh)

        file_base_name = os.path.basename(file_name)
        new_node = CuraSceneNode()
        new_node.setMeshData(mesh_data)
        new_node.setSelectable(True)
        new_node.setName(file_base_name)
        new_node.addDecorator(BuildPlateDecorator(CuraApplication.getInstance().getMultiBuildPlateModel().activeBuildPlate))
        new_node.addDecorator(SliceableObjectDecorator())
        return new_node

    def _toMeshData(self, tri_node: trimesh.base.Trimesh) -> MeshData:
        tri_faces = tri_node.faces
        tri_vertices = tri_node.vertices

        indices = []
        vertices = []

        index_count = 0
        face_count = 0
        for tri_face in tri_faces:
            face = []
            for tri_index in tri_face:
                vertices.append(tri_vertices[tri_index])
                face.append(index_count)
                index_count += 1
            indices.append(face)
            face_count += 1

        vertices = numpy.asarray(vertices, dtype = numpy.float32)
        indices = numpy.asarray(indices, dtype = numpy.int32)
        normals = calculateNormalsFromIndexedVertices(vertices, indices, face_count)

        mesh_data = MeshData(vertices = vertices, indices = indices, normals = normals)
        return mesh_data