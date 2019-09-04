# Copyright (c) 2019 Ultimaker B.V., fieldOfView
# Cura is released under the terms of the LGPLv3 or higher.

# The _toMeshData function is taken from the AMFReader class which was built by fieldOfView.

from typing import Any, List, Union, TYPE_CHECKING
import numpy  # To create the mesh data.
import os.path  # To create the mesh name for the resulting mesh.
import trimesh  # To load the files into a Trimesh.

from UM.Mesh.MeshData import MeshData, calculateNormalsFromIndexedVertices  # To construct meshes from the Trimesh data.
from UM.Mesh.MeshReader import MeshReader  # The plug-in type we're extending.
from UM.MimeTypeDatabase import MimeTypeDatabase, MimeType  # To add file types that we can open.
from UM.Scene.GroupDecorator import GroupDecorator  # Added to the parent node if we load multiple nodes at once.

from cura.CuraApplication import CuraApplication
from cura.Scene.BuildPlateDecorator import BuildPlateDecorator  # Added to the resulting scene node.
from cura.Scene.ConvexHullDecorator import ConvexHullDecorator  # Added to group nodes if we load multiple nodes at once.
from cura.Scene.CuraSceneNode import CuraSceneNode  # To create a node in the scene after reading the file.
from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator  # Added to the resulting scene node.

if TYPE_CHECKING:
    from UM.Scene.SceneNode import SceneNode

##  Class that leverages Trimesh to import files.
class TrimeshReader(MeshReader):
    def __init__(self) -> None:
        super().__init__()

        self._supported_extensions = [".ctm", ".dae", ".gltf", ".glb", ".ply", ".zae"]
        MimeTypeDatabase.addMimeType(
            MimeType(
                name = "application/x-ctm",
                comment = "Open Compressed Triangle Mesh",
                suffixes = ["ctm"]
            )
        )
        MimeTypeDatabase.addMimeType(
            MimeType(
                name = "model/vnd.collada+xml",
                comment = "COLLADA Digital Asset Exchange",
                suffixes = ["dae"]
            )
        )
        MimeTypeDatabase.addMimeType(
            MimeType(
                name = "model/gltf-binary",
                comment = "glTF Binary",
                suffixes = ["glb"]
            )
        )
        MimeTypeDatabase.addMimeType(
            MimeType(
                name = "model/gltf+json",
                comment = "glTF Embedded JSON",
                suffixes = ["gltf"]
            )
        )
        # Trimesh seems to have a bug when reading .off files.
        #MimeTypeDatabase.addMimeType(
        #    MimeType(
        #        name = "application/x-off",
        #        comment = "Geomview Object File Format",
        #        suffixes = ["off"]
        #    )
        #)
        MimeTypeDatabase.addMimeType(
            MimeType(
                name = "application/x-ply",  # Wikipedia lists the MIME type as "text/plain" but that won't do as it's not unique to PLY files.
                comment = "Stanford Triangle Format",
                suffixes = ["ply"]
            )
        )
        MimeTypeDatabase.addMimeType(
            MimeType(
                name = "model/vnd.collada+xml+zip",
                comment = "Compressed COLLADA Digital Asset Exchange",
                suffixes = ["zae"]
            )
        )

    ##  Reads a file using Trimesh.
    #   \param file_name The file path. This is assumed to be one of the file
    #   types that Trimesh can read. It will not be checked again.
    #   \return A scene node that contains the file's contents.
    def _read(self, file_name: str) -> Union["SceneNode", List["SceneNode"]]:
        # CURA-6739
        # GLTF files are essentially JSON files. If you directly give a file name to trimesh.load(), it will
        # try to figure out the format, but for GLTF, it loads it as a binary file with flags "rb", and the json.load()
        # doesn't like it. For some reason, this seems to happen with 3.5.7, but not 3.7.1. Below is a workaround to
        # pass a file object that has been opened with "r" instead "rb" to load a GLTF file.
        if file_name.endswith(".gltf"):
            mesh_or_scene = trimesh.load(open(file_name, "r", encoding = "utf-8"), file_type = "gltf")
        else:
            mesh_or_scene = trimesh.load(file_name)

        meshes = []  # type: List[Union[trimesh.Trimesh, trimesh.Scene, Any]]
        if isinstance(mesh_or_scene, trimesh.Trimesh):
            meshes = [mesh_or_scene]
        elif isinstance(mesh_or_scene, trimesh.Scene):
            meshes = [mesh for mesh in mesh_or_scene.geometry.values()]

        active_build_plate = CuraApplication.getInstance().getMultiBuildPlateModel().activeBuildPlate
        nodes = []  # type: List[SceneNode]
        for mesh in meshes:
            if not isinstance(mesh, trimesh.Trimesh):  # Trimesh can also receive point clouds, 2D paths, 3D paths or metadata. Skip those.
                continue
            mesh.merge_vertices()
            mesh.remove_unreferenced_vertices()
            mesh.fix_normals()
            mesh_data = self._toMeshData(mesh)

            file_base_name = os.path.basename(file_name)
            new_node = CuraSceneNode()
            new_node.setMeshData(mesh_data)
            new_node.setSelectable(True)
            new_node.setName(file_base_name if len(meshes) == 1 else "{file_base_name} {counter}".format(file_base_name = file_base_name, counter = str(len(nodes) + 1)))
            new_node.addDecorator(BuildPlateDecorator(active_build_plate))
            new_node.addDecorator(SliceableObjectDecorator())
            nodes.append(new_node)

        if len(nodes) == 1:
            return nodes[0]
        # Add all nodes to a group so they stay together.
        group_node = CuraSceneNode()
        group_node.addDecorator(GroupDecorator())
        group_node.addDecorator(ConvexHullDecorator())
        group_node.addDecorator(BuildPlateDecorator(active_build_plate))
        for node in nodes:
            node.setParent(group_node)
        return group_node

    ##  Converts a Trimesh to Uranium's MeshData.
    #   \param tri_node A Trimesh containing the contents of a file that was
    #   just read.
    #   \return Mesh data from the Trimesh in a way that Uranium can understand
    #   it.
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