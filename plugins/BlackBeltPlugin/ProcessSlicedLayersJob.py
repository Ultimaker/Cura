#Copyright (c) 2017 Ultimaker B.V.
#Cura is released under the terms of the AGPLv3 or higher.

import gc

from UM.Job import Job
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode
from UM.Application import Application
from UM.Mesh.MeshData import MeshData
from UM.Preferences import Preferences
from UM.View.GL.OpenGLContext import OpenGLContext

from UM.Message import Message
from UM.i18n import i18nCatalog
from UM.Logger import Logger

from UM.Math.Vector import Vector
from UM.Math.Matrix import Matrix

from cura.Settings.ExtruderManager import ExtruderManager
from cura import LayerDataBuilder
from cura import LayerDataDecorator
from cura import LayerPolygon

import numpy
from time import time
from cura.Settings.ExtrudersModel import ExtrudersModel
catalog = i18nCatalog("cura")


##  Return a 4-tuple with floats 0-1 representing the html color code
#
#   \param color_code html color code, i.e. "#FF0000" -> red
def colorCodeToRGBA(color_code):
    if color_code is None:
        Logger.log("w", "Unable to convert color code, returning default")
        return [0, 0, 0, 1]
    return [
        int(color_code[1:3], 16) / 255,
        int(color_code[3:5], 16) / 255,
        int(color_code[5:7], 16) / 255,
        1.0]


class ProcessSlicedLayersJob(Job):
    def __init__(self, layers):
        super().__init__()
        self._layers = layers
        self._scene = Application.getInstance().getController().getScene()
        self._progress = None
        self._abort_requested = False

    ##  Aborts the processing of layers.
    #
    #   This abort is made on a best-effort basis, meaning that the actual
    #   job thread will check once in a while to see whether an abort is
    #   requested and then stop processing by itself. There is no guarantee
    #   that the abort will stop the job any time soon or even at all.
    def abort(self):
        self._abort_requested = True

    def run(self):
        start_time = time()
        if Application.getInstance().getController().getActiveView().getPluginId() == "LayerView":
            self._progress = Message(catalog.i18nc("@info:status", "Processing Layers"), 0, False, -1)
            self._progress.show()
            Job.yieldThread()
            if self._abort_requested:
                if self._progress:
                    self._progress.hide()
                return

        Application.getInstance().getController().activeViewChanged.connect(self._onActiveViewChanged)

        new_node = SceneNode()

        ## Remove old layer data (if any)
        for node in DepthFirstIterator(self._scene.getRoot()):
            if node.callDecoration("getLayerData"):
                node.getParent().removeChild(node)
                break
            if self._abort_requested:
                if self._progress:
                    self._progress.hide()
                return

        # Force garbage collection.
        # For some reason, Python has a tendency to keep the layer data
        # in memory longer than needed. Forcing the GC to run here makes
        # sure any old layer data is really cleaned up before adding new.
        gc.collect()

        mesh = MeshData()
        layer_data = LayerDataBuilder.LayerDataBuilder()
        layer_count = len(self._layers)

        # Find the minimum layer number
        # When using a raft, the raft layers are sent as layers < 0. Instead of allowing layers < 0, we
        # instead simply offset all other layers so the lowest layer is always 0.
        min_layer_number = 0
        for layer in self._layers:
            if layer.id < min_layer_number:
                min_layer_number = layer.id

        current_layer = 0

        for layer in self._layers:
            abs_layer_number = layer.id + abs(min_layer_number)

            layer_data.addLayer(abs_layer_number)
            this_layer = layer_data.getLayer(abs_layer_number)
            layer_data.setLayerHeight(abs_layer_number, layer.height)

            for p in range(layer.repeatedMessageCount("path_segment")):
                polygon = layer.getRepeatedMessage("path_segment", p)

                extruder = polygon.extruder

                line_types = numpy.fromstring(polygon.line_type, dtype="u1")  # Convert bytearray to numpy array
                line_types = line_types.reshape((-1,1))

                points = numpy.fromstring(polygon.points, dtype="f4")  # Convert bytearray to numpy array
                if polygon.point_type == 0: # Point2D
                    points = points.reshape((-1,2))  # We get a linear list of pairs that make up the points, so make numpy interpret them correctly.
                else:  # Point3D
                    points = points.reshape((-1,3))

                line_widths = numpy.fromstring(polygon.line_width, dtype="f4")  # Convert bytearray to numpy array
                line_widths = line_widths.reshape((-1,1))  # We get a linear list of pairs that make up the points, so make numpy interpret them correctly.

                # In the future, line_thicknesses should be given by CuraEngine as well.
                # Currently the infill layer thickness also translates to line width
                line_thicknesses = numpy.zeros(line_widths.shape, dtype="f4")
                line_thicknesses[:] = layer.thickness / 1000  # from micrometer to millimeter

                # Create a new 3D-array, copy the 2D points over and insert the right height.
                # This uses manual array creation + copy rather than numpy.insert since this is
                # faster.
                new_points = numpy.empty((len(points), 3), numpy.float32)
                if polygon.point_type == 0:  # Point2D
                    new_points[:, 0] = points[:, 0]
                    new_points[:, 1] = layer.height / 1000  # layer height value is in backend representation
                    new_points[:, 2] = -points[:, 1]
                else: # Point3D
                    new_points[:, 0] = points[:, 0]
                    new_points[:, 1] = points[:, 2]
                    new_points[:, 2] = -points[:, 1]

                this_poly = LayerPolygon.LayerPolygon(extruder, line_types, new_points, line_widths, line_thicknesses)
                this_poly.buildCache()

                this_layer.polygons.append(this_poly)

                Job.yieldThread()
            Job.yieldThread()
            current_layer += 1
            progress = (current_layer / layer_count) * 99
            # TODO: Rebuild the layer data mesh once the layer has been processed.
            # This needs some work in LayerData so we can add the new layers instead of recreating the entire mesh.

            if self._abort_requested:
                if self._progress:
                    self._progress.hide()
                return
            if self._progress:
                self._progress.setProgress(progress)

        # We are done processing all the layers we got from the engine, now create a mesh out of the data

        # Find out colors per extruder
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        manager = ExtruderManager.getInstance()
        extruders = list(manager.getMachineExtruders(global_container_stack.getId()))
        if extruders:
            material_color_map = numpy.zeros((len(extruders), 4), dtype=numpy.float32)
            for extruder in extruders:
                position = int(extruder.getMetaDataEntry("position", default="0"))  # Get the position
                try:
                    default_color = ExtrudersModel.defaultColors[position]
                except IndexError:
                    default_color = "#e0e000"
                color_code = extruder.material.getMetaDataEntry("color_code", default=default_color)
                color = colorCodeToRGBA(color_code)
                material_color_map[position, :] = color
        else:
            # Single extruder via global stack.
            material_color_map = numpy.zeros((1, 4), dtype=numpy.float32)
            color_code = global_container_stack.material.getMetaDataEntry("color_code", default="#e0e000")
            color = colorCodeToRGBA(color_code)
            material_color_map[0, :] = color

        # We have to scale the colors for compatibility mode
        if OpenGLContext.isLegacyOpenGL() or bool(Preferences.getInstance().getValue("view/force_layer_view_compatibility_mode")):
            line_type_brightness = 0.5  # for compatibility mode
        else:
            line_type_brightness = 1.0
        layer_mesh = layer_data.build(material_color_map, line_type_brightness)

        if self._abort_requested:
            if self._progress:
                self._progress.hide()
            return

        # Add LayerDataDecorator to scene node to indicate that the node has layer data
        decorator = LayerDataDecorator.LayerDataDecorator()
        decorator.setLayerData(layer_mesh)
        new_node.addDecorator(decorator)

        new_node.setMeshData(mesh)
        # Set build volume as parent, the build volume can move as a result of raft settings.
        # It makes sense to set the build volume as parent: the print is actually printed on it.
        new_node_parent = Application.getInstance().getBuildVolume()
        new_node.setParent(new_node_parent)  # Note: After this we can no longer abort!

        settings = Application.getInstance().getGlobalContainerStack()
        if not settings.getProperty("machine_center_is_zero", "value"):
            new_node.setPosition(Vector(-settings.getProperty("machine_width", "value") / 2, 0.0, settings.getProperty("machine_depth", "value") / 2))

        transform = self._scene.getRoot().callDecoration("getTransformMatrix")
        if transform and transform != Matrix():
            transform_matrix = new_node.getLocalTransformation().preMultiply(transform.getInverse())
            new_node.setTransformation(transform_matrix)
            new_node.translate(Vector(0, 0, self._scene.getRoot().callDecoration("getSceneFrontOffset")), SceneNode.TransformSpace.World)

        if self._progress:
            self._progress.setProgress(100)

        view = Application.getInstance().getController().getActiveView()
        if view.getPluginId() == "LayerView":
            view.resetLayerData()

        if self._progress:
            self._progress.hide()

        # Clear the unparsed layers. This saves us a bunch of memory if the Job does not get destroyed.
        self._layers = None

        Logger.log("d", "Processing layers took %s seconds", time() - start_time)

    def _onActiveViewChanged(self):
        if self.isRunning():
            if Application.getInstance().getController().getActiveView().getPluginId() == "LayerView":
                if not self._progress:
                    self._progress = Message(catalog.i18nc("@info:status", "Processing Layers"), 0, False, 0, catalog.i18nc("@info:title", "Information"))
                if self._progress.getProgress() != 100:
                    self._progress.show()
            else:
                if self._progress:
                    self._progress.hide()
