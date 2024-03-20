# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import math

from UM.Math.Color import Color
from UM.Math.Vector import Vector
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Resources import Resources
from UM.Scene.SceneNode import SceneNode
from UM.Scene.ToolHandle import ToolHandle
from UM.Application import Application
from UM.PluginRegistry import PluginRegistry

from UM.View.RenderPass import RenderPass
from UM.View.RenderBatch import RenderBatch
from UM.View.GL.OpenGL import OpenGL

from cura.Settings.ExtruderManager import ExtruderManager
from cura.LayerPolygon import LayerPolygon

import os.path
import numpy

## RenderPass used to display g-code paths.
from .NozzleNode import NozzleNode


class SimulationPass(RenderPass):
    def __init__(self, width, height):
        super().__init__("simulationview", width, height)

        self._layer_shader = None
        self._layer_shadow_shader = None
        self._current_shader = None # This shader will be the shadow or the normal depending if the user wants to see the paths or the layers
        self._tool_handle_shader = None
        self._nozzle_shader = None
        self._disabled_shader = None
        self._old_current_layer = 0
        self._old_current_path: float = 0.0
        self._switching_layers = True  # Tracking whether the user is moving across layers (True) or across paths (False). If false, lower layers render as shadowy.
        self._gl = OpenGL.getInstance().getBindingsObject()
        self._scene = Application.getInstance().getController().getScene()
        self._extruder_manager = ExtruderManager.getInstance()

        self._layer_view = None
        self._compatibility_mode = None

        self._scene.sceneChanged.connect(self._onSceneChanged)

    def setSimulationView(self, layerview):
        self._layer_view = layerview
        self._compatibility_mode = layerview.getCompatibilityMode()

    def render(self):
        if not self._layer_shader:
            if self._compatibility_mode:
                shader_filename = "layers.shader"
                shadow_shader_filename = "layers_shadow.shader"
            else:
                shader_filename = "layers3d.shader"
                shadow_shader_filename = "layers3d_shadow.shader"
            self._layer_shader = OpenGL.getInstance().createShaderProgram(os.path.join(PluginRegistry.getInstance().getPluginPath("SimulationView"), shader_filename))
            self._layer_shadow_shader = OpenGL.getInstance().createShaderProgram(os.path.join(PluginRegistry.getInstance().getPluginPath("SimulationView"), shadow_shader_filename))
            self._current_shader = self._layer_shader
        # Use extruder 0 if the extruder manager reports extruder index -1 (for single extrusion printers)
        self._layer_shader.setUniformValue("u_active_extruder", float(max(0, self._extruder_manager.activeExtruderIndex)))
        if not self._compatibility_mode:
            self._layer_shader.setUniformValue("u_starts_color", Color(*Application.getInstance().getTheme().getColor("layerview_starts").getRgb()))

        if self._layer_view:
            self._layer_shader.setUniformValue("u_max_feedrate", self._layer_view.getMaxFeedrate())
            self._layer_shader.setUniformValue("u_min_feedrate", self._layer_view.getMinFeedrate())
            self._layer_shader.setUniformValue("u_max_thickness", self._layer_view.getMaxThickness())
            self._layer_shader.setUniformValue("u_min_thickness", self._layer_view.getMinThickness())
            self._layer_shader.setUniformValue("u_max_line_width", self._layer_view.getMaxLineWidth())
            self._layer_shader.setUniformValue("u_min_line_width", self._layer_view.getMinLineWidth())
            self._layer_shader.setUniformValue("u_max_flow_rate", self._layer_view.getMaxFlowRate())
            self._layer_shader.setUniformValue("u_min_flow_rate", self._layer_view.getMinFlowRate())
            self._layer_shader.setUniformValue("u_layer_view_type", self._layer_view.getSimulationViewType())
            self._layer_shader.setUniformValue("u_extruder_opacity", self._layer_view.getExtruderOpacities())
            self._layer_shader.setUniformValue("u_show_travel_moves", self._layer_view.getShowTravelMoves())
            self._layer_shader.setUniformValue("u_show_helpers", self._layer_view.getShowHelpers())
            self._layer_shader.setUniformValue("u_show_skin", self._layer_view.getShowSkin())
            self._layer_shader.setUniformValue("u_show_infill", self._layer_view.getShowInfill())
            self._layer_shader.setUniformValue("u_show_starts", self._layer_view.getShowStarts())
        else:
            #defaults
            self._layer_shader.setUniformValue("u_max_feedrate", 1)
            self._layer_shader.setUniformValue("u_min_feedrate", 0)
            self._layer_shader.setUniformValue("u_max_thickness", 1)
            self._layer_shader.setUniformValue("u_min_thickness", 0)
            self._layer_shader.setUniformValue("u_max_flow_rate", 1)
            self._layer_shader.setUniformValue("u_min_flow_rate", 0)
            self._layer_shader.setUniformValue("u_max_line_width", 1)
            self._layer_shader.setUniformValue("u_min_line_width", 0)
            self._layer_shader.setUniformValue("u_layer_view_type", 1)
            self._layer_shader.setUniformValue("u_extruder_opacity", [[1, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1]])
            self._layer_shader.setUniformValue("u_show_travel_moves", 0)
            self._layer_shader.setUniformValue("u_show_helpers", 1)
            self._layer_shader.setUniformValue("u_show_skin", 1)
            self._layer_shader.setUniformValue("u_show_infill", 1)
            self._layer_shader.setUniformValue("u_show_starts", 1)

        if not self._tool_handle_shader:
            self._tool_handle_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "toolhandle.shader"))

        if not self._nozzle_shader:
            self._nozzle_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "color.shader"))
            self._nozzle_shader.setUniformValue("u_color", Color(*Application.getInstance().getTheme().getColor("layerview_nozzle").getRgb()))

        if not self._disabled_shader:
            self._disabled_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "striped.shader"))
            self._disabled_shader.setUniformValue("u_diffuseColor1", Color(*Application.getInstance().getTheme().getColor("model_unslicable").getRgb()))
            self._disabled_shader.setUniformValue("u_diffuseColor2", Color(*Application.getInstance().getTheme().getColor("model_unslicable_alt").getRgb()))
            self._disabled_shader.setUniformValue("u_width", 50.0)
            self._disabled_shader.setUniformValue("u_opacity", 0.6)

        self.bind()

        tool_handle_batch = RenderBatch(self._tool_handle_shader, type = RenderBatch.RenderType.Overlay, backface_cull = True)
        disabled_batch = RenderBatch(self._disabled_shader)
        head_position = None  # Indicates the current position of the print head
        nozzle_node = None
        not_a_vector = Vector(math.nan, math.nan, math.nan)

        for node in DepthFirstIterator(self._scene.getRoot()):

            if isinstance(node, ToolHandle):
                tool_handle_batch.addItem(node.getWorldTransformation(), mesh = node.getSolidMesh())

            elif isinstance(node, NozzleNode):
                nozzle_node = node
                nozzle_node.setVisible(False)  # Don't set to true, we render it separately!

            elif getattr(node, "_outside_buildarea", False) and isinstance(node, SceneNode) and node.getMeshData() and node.isVisible() and not node.callDecoration("isNonPrintingMesh"):
                disabled_batch.addItem(node.getWorldTransformation(copy=False), node.getMeshData())

            elif isinstance(node, SceneNode) and (node.getMeshData() or node.callDecoration("isBlockSlicing")) and node.isVisible():
                layer_data = node.callDecoration("getLayerData")
                if not layer_data:
                    continue

                # Render all layers below a certain number as line mesh instead of vertices.
                if self._layer_view.getCurrentLayer() > -1 and ((not self._layer_view._only_show_top_layers) or (not self._layer_view.getCompatibilityMode())):
                    start = 0
                    end = 0
                    vertex_before_head = not_a_vector
                    vertex_after_head = not_a_vector
                    vertex_distance_ratio = 0.0
                    towards_next_vertex = 0
                    element_counts = layer_data.getElementCounts()
                    for layer in sorted(element_counts.keys()):
                        # In the current layer, we show just the indicated paths
                        if layer == self._layer_view._current_layer_num:
                            # We look for the position of the head, searching the point of the current path
                            index = int(self._layer_view.getCurrentPath()) if not math.isnan(
                                self._layer_view.getCurrentPath()) else 0
                            for polygon in layer_data.getLayer(layer).polygons:
                                # The size indicates all values in the two-dimension array, and the second dimension is
                                # always size 3 because we have 3D points.
                                if index >= polygon.data.size // 3 :
                                    index -= polygon.data.size // 3
                                    continue
                                # The head position is calculated and translated
                                ratio = self._layer_view.getCurrentPath() - math.floor(self._layer_view.getCurrentPath())
                                pos_a = Vector(polygon.data[index][0], polygon.data[index][1],
                                               polygon.data[index][2])
                                vertex_before_head = pos_a
                                vertex_distance_ratio = ratio
                                if ratio <= 0.0001 or index + 1 == len(polygon.data):
                                    # in case there multiple polygons and polygon changes, the first point has the same value as the last point in the previous polygon
                                    head_position = pos_a + node.getWorldPosition()
                                else:
                                    pos_b = Vector(polygon.data[index + 1][0],
                                                   polygon.data[index + 1][1],
                                                   polygon.data[index + 1][2])
                                    vec = pos_a * (1.0 - ratio) + pos_b * ratio
                                    head_position = vec + node.getWorldPosition()
                                    vertex_after_head = pos_b
                                    towards_next_vertex = 2  # Add two to the index to print the current and next vertices as an 'unfinished' line (to the nozzle).
                                break
                            break
                        if self._layer_view.getMinimumLayer() > layer:
                            start += element_counts[layer]
                        end += element_counts[layer]

                    # Calculate the range of paths in the last layer
                    current_layer_start = end
                    current_layer_end = end + int( self._layer_view.getCurrentPath()) * 2  # Because each point is used twice

                    # This uses glDrawRangeElements internally to only draw a certain range of lines.
                    # All the layers but the current selected layer are rendered first
                    if self._old_current_path != self._layer_view.getCurrentPath():
                        self._current_shader = self._layer_shadow_shader
                        self._switching_layers = False
                    if not self._layer_view.isSimulationRunning() and self._old_current_layer != self._layer_view.getCurrentLayer():
                        self._current_shader = self._layer_shader
                        self._switching_layers = True

                    # reset 'last vertex'
                    self._layer_shader.setUniformValue("u_last_vertex", not_a_vector)
                    self._layer_shader.setUniformValue("u_next_vertex", not_a_vector)
                    self._layer_shader.setUniformValue("u_last_line_ratio", 1.0)

                    # The first line does not have a previous line: add a MoveCombingType in front for start detection
                    # this way the first start of the layer can also be drawn
                    prev_line_types = numpy.concatenate([numpy.asarray([LayerPolygon.MoveCombingType], dtype = numpy.float32), layer_data._attributes["line_types"]["value"]])
                    # Remove the last element
                    prev_line_types = prev_line_types[0:layer_data._attributes["line_types"]["value"].size]
                    layer_data._attributes["prev_line_types"] =  {'opengl_type': 'float', 'value': prev_line_types, 'opengl_name': 'a_prev_line_type'}

                    layers_batch = RenderBatch(self._current_shader, type = RenderBatch.RenderType.Solid, mode = RenderBatch.RenderMode.Lines, range = (start, end), backface_cull = True)
                    layers_batch.addItem(node.getWorldTransformation(), layer_data)
                    layers_batch.render(self._scene.getActiveCamera())

                    # Current selected layer is rendered
                    current_layer_batch = RenderBatch(self._layer_shader, type = RenderBatch.RenderType.Solid, mode = RenderBatch.RenderMode.Lines, range = (current_layer_start, current_layer_end))
                    current_layer_batch.addItem(node.getWorldTransformation(), layer_data)
                    current_layer_batch.render(self._scene.getActiveCamera())

                    # Last line may be partial
                    if vertex_after_head != not_a_vector and vertex_after_head != not_a_vector:
                        self._layer_shader.setUniformValue("u_last_vertex", vertex_before_head)
                        self._layer_shader.setUniformValue("u_next_vertex", vertex_after_head)
                        self._layer_shader.setUniformValue("u_last_line_ratio", vertex_distance_ratio)
                        last_line_start = current_layer_end
                        last_line_end = current_layer_end + towards_next_vertex
                        last_line_batch = RenderBatch(self._layer_shader, type = RenderBatch.RenderType.Solid, mode=RenderBatch.RenderMode.Lines, range = (last_line_start, last_line_end))
                        last_line_batch.addItem(node.getWorldTransformation(), layer_data)
                        last_line_batch.render(self._scene.getActiveCamera())

                    self._old_current_layer = self._layer_view.getCurrentLayer()
                    self._old_current_path = self._layer_view.getCurrentPath()

                # Create a new batch that is not range-limited
                batch = RenderBatch(self._layer_shader, type = RenderBatch.RenderType.Solid)

                if self._layer_view.getCurrentLayerMesh():
                    batch.addItem(node.getWorldTransformation(), self._layer_view.getCurrentLayerMesh())

                if self._layer_view.getCurrentLayerJumps():
                    batch.addItem(node.getWorldTransformation(), self._layer_view.getCurrentLayerJumps())

                if len(batch.items) > 0:
                    batch.render(self._scene.getActiveCamera())

        # The nozzle is drawn when once we know the correct position of the head,
        # but the user is not using the layer slider, and the compatibility mode is not enabled
        if not self._switching_layers and not self._compatibility_mode and self._layer_view.getActivity() and nozzle_node is not None:
            if head_position is not None:
                nozzle_node.setPosition(head_position)
                nozzle_batch = RenderBatch(self._nozzle_shader, type = RenderBatch.RenderType.Transparent)
                nozzle_batch.addItem(nozzle_node.getWorldTransformation(), mesh = nozzle_node.getMeshData())
                nozzle_batch.render(self._scene.getActiveCamera())

        if len(disabled_batch.items) > 0:
            disabled_batch.render(self._scene.getActiveCamera())

        # Render toolhandles on top of the layerview
        if len(tool_handle_batch.items) > 0:
            tool_handle_batch.render(self._scene.getActiveCamera())

        self.release()

    def _onSceneChanged(self, changed_object: SceneNode):
        if changed_object.callDecoration("getLayerData"):  # Any layer data has changed.
            self._switching_layers = True
            self._old_current_layer = 0
            self._old_current_path = 0.0
