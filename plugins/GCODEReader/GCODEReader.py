# Copyright (c) 2015 Ultimaker B.V.
# Copyright (c) 2013 David Braam
# Uranium is released under the terms of the AGPLv3 or higher.

from UM.Mesh.MeshReader import MeshReader
from UM.Mesh.MeshBuilder import MeshBuilder
import os
from UM.Scene.SceneNode import SceneNode
from UM.Math.Vector import Vector
from UM.Math.AxisAlignedBox import AxisAlignedBox
from UM.Application import Application

from cura import LayerDataBuilder
from cura import LayerDataDecorator
from cura import LayerPolygon

import numpy


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

            # mesh_builder = MeshBuilder()
            # mesh_builder.setFileName(file_name)
            #
            # mesh_builder.addCube(
            #     width=5,
            #     height=5,
            #     depth=5,
            #     center=Vector(0, 2.5, 0)
            # )
            #
            # scene_node.setMeshData(mesh_builder.build())

            def getBoundingBox():
                return AxisAlignedBox(minimum=Vector(0, 0, 0), maximum=Vector(10, 10, 10))

            scene_node.getBoundingBox = getBoundingBox
            scene_node.gcode = True

            layer_data = LayerDataBuilder.LayerDataBuilder()
            layer_count = 1
            for id in range(layer_count):
                layer_data.addLayer(id)
                this_layer = layer_data.getLayer(id)
                layer_data.setLayerHeight(id, 1)
                layer_data.setLayerThickness(id, 1)

                extruder = 1
                line_types = numpy.empty((1, 1), numpy.int32)
                line_types[0, 0] = 6
                line_widths = numpy.empty((1, 1), numpy.int32)
                line_widths[0, 0] = 1
                points = numpy.empty((2, 3), numpy.float32)
                points[0, 0] = 0
                points[0, 1] = 0
                points[0, 2] = 0
                points[1, 0] = 10
                points[1, 1] = 10
                points[1, 2] = 10

                this_poly = LayerPolygon.LayerPolygon(layer_data, extruder, line_types, points, line_widths)
                this_poly.buildCache()

                this_layer.polygons.append(this_poly)

            layer_mesh = layer_data.build()
            decorator = LayerDataDecorator.LayerDataDecorator()
            decorator.setLayerData(layer_mesh)
            scene_node.addDecorator(decorator)

            scene_node_parent = Application.getInstance().getBuildVolume()
            scene_node.setParent(scene_node_parent)

            view = Application.getInstance().getController().getActiveView()
            if view.getPluginId() == "LayerView":
                view.resetLayerData()

            #scene_node.setEnabled(False)
            #scene_node.setSelectable(False)

        return scene_node
