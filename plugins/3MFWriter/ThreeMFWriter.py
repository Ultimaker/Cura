# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from UM.Mesh.MeshWriter import MeshWriter
from UM.Math.Vector import Vector
from UM.Logger import Logger
from UM.Math.Matrix import Matrix
from UM.Settings.SettingRelation import RelationType

try:
    import xml.etree.cElementTree as ET
except ImportError:
    Logger.log("w", "Unable to load cElementTree, switching to slower version")
    import xml.etree.ElementTree as ET

import zipfile
import UM.Application


class ThreeMFWriter(MeshWriter):
    def __init__(self):
        super().__init__()
        self._namespaces = {
            "3mf": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02",
            "content-types": "http://schemas.openxmlformats.org/package/2006/content-types",
            "relationships": "http://schemas.openxmlformats.org/package/2006/relationships",
            "cura": "http://software.ultimaker.com/xml/cura/3mf/2015/10"
        }

        self._unit_matrix_string = self._convertMatrixToString(Matrix())
        self._archive = None
        self._store_archive = False

    def _convertMatrixToString(self, matrix):
        result = ""
        result += str(matrix._data[0,0]) + " "
        result += str(matrix._data[1,0]) + " "
        result += str(matrix._data[2,0]) + " "
        result += str(matrix._data[0,1]) + " "
        result += str(matrix._data[1,1]) + " "
        result += str(matrix._data[2,1]) + " "
        result += str(matrix._data[0,2]) + " "
        result += str(matrix._data[1,2]) + " "
        result += str(matrix._data[2,2]) + " "
        result += str(matrix._data[0,3]) + " "
        result += str(matrix._data[1,3]) + " "
        result += str(matrix._data[2,3]) + " "
        return result

    ##  Should we store the archive
    #   Note that if this is true, the archive will not be closed.
    #   The object that set this parameter is then responsible for closing it correctly!
    def setStoreArchive(self, store_archive):
        self._store_archive = store_archive

    def getArchive(self):
        return self._archive

    def write(self, stream, nodes, mode = MeshWriter.OutputMode.BinaryMode):
        self._archive = None # Reset archive
        archive = zipfile.ZipFile(stream, "w", compression = zipfile.ZIP_DEFLATED)
        try:
            model_file = zipfile.ZipInfo("3D/3dmodel.model")
            # Because zipfile is stupid and ignores archive-level compression settings when writing with ZipInfo.
            model_file.compress_type = zipfile.ZIP_DEFLATED

            # Create content types file
            content_types_file = zipfile.ZipInfo("[Content_Types].xml")
            content_types_file.compress_type = zipfile.ZIP_DEFLATED
            content_types = ET.Element("Types", xmlns = self._namespaces["content-types"])
            rels_type = ET.SubElement(content_types, "Default", Extension = "rels", ContentType = "application/vnd.openxmlformats-package.relationships+xml")
            model_type = ET.SubElement(content_types, "Default", Extension = "model", ContentType = "application/vnd.ms-package.3dmanufacturing-3dmodel+xml")

            # Create _rels/.rels file
            relations_file = zipfile.ZipInfo("_rels/.rels")
            relations_file.compress_type = zipfile.ZIP_DEFLATED
            relations_element = ET.Element("Relationships", xmlns = self._namespaces["relationships"])
            model_relation_element = ET.SubElement(relations_element, "Relationship", Target = "/3D/3dmodel.model", Id = "rel0", Type = "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel")

            model = ET.Element("model", unit = "millimeter", xmlns = self._namespaces["3mf"])
            resources = ET.SubElement(model, "resources")
            build = ET.SubElement(model, "build")

            added_nodes = []
            index = 0  # Ensure index always exists (even if there are no nodes to write)
            # Write all nodes with meshData to the file as objects inside the resource tag
            for index, n in enumerate(MeshWriter._meshNodes(nodes)):
                added_nodes.append(n)  # Save the nodes that have mesh data
                object = ET.SubElement(resources, "object", id = str(index+1), type = "model")
                mesh = ET.SubElement(object, "mesh")

                mesh_data = n.getMeshData()
                vertices = ET.SubElement(mesh, "vertices")
                verts = mesh_data.getVertices()

                if verts is None:
                    Logger.log("d", "3mf writer can't write nodes without mesh data. Skipping this node.")
                    continue  # No mesh data, nothing to do.
                if mesh_data.hasIndices():
                    for face in mesh_data.getIndices():
                        v1 = verts[face[0]]
                        v2 = verts[face[1]]
                        v3 = verts[face[2]]
                        xml_vertex1 = ET.SubElement(vertices, "vertex", x = str(v1[0]), y = str(v1[1]), z = str(v1[2]))
                        xml_vertex2 = ET.SubElement(vertices, "vertex", x = str(v2[0]), y = str(v2[1]), z = str(v2[2]))
                        xml_vertex3 = ET.SubElement(vertices, "vertex", x = str(v3[0]), y = str(v3[1]), z = str(v3[2]))

                    triangles = ET.SubElement(mesh, "triangles")
                    for face in mesh_data.getIndices():
                        triangle = ET.SubElement(triangles, "triangle", v1 = str(face[0]) , v2 = str(face[1]), v3 = str(face[2]))
                else:
                    triangles = ET.SubElement(mesh, "triangles")
                    for idx, vert in enumerate(verts):
                        xml_vertex = ET.SubElement(vertices, "vertex", x = str(vert[0]), y = str(vert[1]), z = str(vert[2]))

                        # If we have no faces defined, assume that every three subsequent vertices form a face.
                        if idx % 3 == 0:
                            triangle = ET.SubElement(triangles, "triangle", v1 = str(idx), v2 = str(idx + 1), v3 = str(idx + 2))

                # Handle per object settings
                stack = n.callDecoration("getStack")
                if stack is not None:
                    changed_setting_keys = set(stack.getTop().getAllKeys())

                    # Ensure that we save the extruder used for this object.
                    if stack.getProperty("machine_extruder_count", "value") > 1:
                        changed_setting_keys.add("extruder_nr")

                    settings_xml = ET.SubElement(object, "settings", xmlns=self._namespaces["cura"])

                    # Get values for all changed settings & save them.
                    for key in changed_setting_keys:
                        setting_xml = ET.SubElement(settings_xml, "setting", key = key)
                        setting_xml.text = str(stack.getProperty(key, "value"))

            # Add one to the index as we haven't incremented the last iteration.
            index += 1
            nodes_to_add = set()

            for node in added_nodes:
                # Check the parents of the nodes with mesh_data and ensure that they are also added.
                parent_node = node.getParent()
                while parent_node is not None:
                    if parent_node.callDecoration("isGroup"):
                        nodes_to_add.add(parent_node)
                        parent_node = parent_node.getParent()
                    else:
                        parent_node = None

            # Sort all the nodes by depth (so nodes with the highest depth are done first)
            sorted_nodes_to_add = sorted(nodes_to_add, key=lambda node: node.getDepth(), reverse = True)

            # We have already saved the nodes with mesh data, but now we also want to save nodes required for the scene
            for node in sorted_nodes_to_add:
                object = ET.SubElement(resources, "object", id=str(index + 1), type="model")
                components = ET.SubElement(object, "components")
                for child in node.getChildren():
                    if child in added_nodes:
                        component = ET.SubElement(components, "component", objectid = str(added_nodes.index(child) + 1), transform = self._convertMatrixToString(child.getLocalTransformation()))
                index += 1
                added_nodes.append(node)

            # Create a transformation Matrix to convert from our worldspace into 3MF.
            # First step: flip the y and z axis.
            transformation_matrix = Matrix()
            transformation_matrix._data[1, 1] = 0
            transformation_matrix._data[1, 2] = -1
            transformation_matrix._data[2, 1] = 1
            transformation_matrix._data[2, 2] = 0

            global_container_stack = UM.Application.getInstance().getGlobalContainerStack()
            # Second step: 3MF defines the left corner of the machine as center, whereas cura uses the center of the
            # build volume.
            if global_container_stack:
                translation_vector = Vector(x=global_container_stack.getProperty("machine_width", "value") / 2,
                                            y=global_container_stack.getProperty("machine_depth", "value") / 2,
                                            z=0)
                translation_matrix = Matrix()
                translation_matrix.setByTranslation(translation_vector)
                transformation_matrix.preMultiply(translation_matrix)

            # Find out what the final build items are and add them.
            for node in added_nodes:
                if node.getParent().callDecoration("isGroup") is None:
                    node_matrix = node.getLocalTransformation()

                    ET.SubElement(build, "item", objectid = str(added_nodes.index(node) + 1), transform = self._convertMatrixToString(node_matrix.preMultiply(transformation_matrix)))

            archive.writestr(model_file, b'<?xml version="1.0" encoding="UTF-8"?> \n' + ET.tostring(model))
            archive.writestr(content_types_file, b'<?xml version="1.0" encoding="UTF-8"?> \n' + ET.tostring(content_types))
            archive.writestr(relations_file, b'<?xml version="1.0" encoding="UTF-8"?> \n' + ET.tostring(relations_element))
        except Exception as e:
            Logger.logException("e", "Error writing zip file")
            return False
        finally:
            if not self._store_archive:
                archive.close()
            else:
                self._archive = archive

        return True
