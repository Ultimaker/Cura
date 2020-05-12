# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

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


import os.path

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
        self._old_current_layer = 0
        self._old_current_path = 0
        self._switching_layers = True # It tracks when the user is moving the layers' slider
        self._gl = OpenGL.getInstance().getBindingsObject()
        self._scene = Application.getInstance().getController().getScene()
        self._extruder_manager = ExtruderManager.getInstance()

        self._layer_view = None
        self._compatibility_mode = None

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
        if self._layer_view:
            self._layer_shader.setUniformValue("u_max_feedrate", self._layer_view.getMaxFeedrate())
            self._layer_shader.setUniformValue("u_min_feedrate", self._layer_view.getMinFeedrate())
            self._layer_shader.setUniformValue("u_max_thickness", self._layer_view.getMaxThickness())
            self._layer_shader.setUniformValue("u_min_thickness", self._layer_view.getMinThickness())
            self._layer_shader.setUniformValue("u_layer_view_type", self._layer_view.getSimulationViewType())
            self._layer_shader.setUniformValue("u_extruder_opacity", self._layer_view.getExtruderOpacities())
            self._layer_shader.setUniformValue("u_show_travel_moves", self._layer_view.getShowTravelMoves())
            self._layer_shader.setUniformValue("u_show_helpers", self._layer_view.getShowHelpers())
            self._layer_shader.setUniformValue("u_show_skin", self._layer_view.getShowSkin())
            self._layer_shader.setUniformValue("u_show_infill", self._layer_view.getShowInfill())
        else:
            #defaults
            self._layer_shader.setUniformValue("u_max_feedrate", 1)
            self._layer_shader.setUniformValue("u_min_feedrate", 0)
            self._layer_shader.setUniformValue("u_max_thickness", 1)
            self._layer_shader.setUniformValue("u_min_thickness", 0)
            self._layer_shader.setUniformValue("u_layer_view_type", 1)
            self._layer_shader.setUniformValue("u_extruder_opacity", [[1, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1]])
            self._layer_shader.setUniformValue("u_show_travel_moves", 0)
            self._layer_shader.setUniformValue("u_show_helpers", 1)
            self._layer_shader.setUniformValue("u_show_skin", 1)
            self._layer_shader.setUniformValue("u_show_infill", 1)

        if not self._tool_handle_shader:
            self._tool_handle_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "toolhandle.shader"))

        if not self._nozzle_shader:
            self._nozzle_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "color.shader"))
            self._nozzle_shader.setUniformValue("u_color", Color(*Application.getInstance().getTheme().getColor("layerview_nozzle").getRgb()))

        self.bind()

        tool_handle_batch = RenderBatch(self._tool_handle_shader, type = RenderBatch.RenderType.Overlay, backface_cull = True)
        head_position = None  # Indicates the current position of the print head
        nozzle_node = None

        for node in DepthFirstIterator(self._scene.getRoot()):

            if isinstance(node, ToolHandle):
                tool_handle_batch.addItem(node.getWorldTransformation(), mesh = node.getSolidMesh())

            elif isinstance(node, NozzleNode):
                nozzle_node = node
                nozzle_node.setVisible(False)

            elif isinstance(node, SceneNode) and (node.getMeshData() or node.callDecoration("isBlockSlicing")) and node.isVisible():
                layer_data = node.callDecoration("getLayerData")
                if not layer_data:
                    continue

                # Render all layers below a certain number as line mesh instead of vertices.
                if self._layer_view._current_layer_num > -1 and ((not self._layer_view._only_show_top_layers) or (not self._layer_view.getCompatibilityMode())):
                    start = 0
                    end = 0
                    element_counts = layer_data.getElementCounts()
                    for layer in sorted(element_counts.keys()):
                        # In the current layer, we show just the indicated paths
                        if layer == self._layer_view._current_layer_num:
                            # We look for the position of the head, searching the point of the current path
                            index = self._layer_view._current_path_num
                            offset = 0
                            for polygon in layer_data.getLayer(layer).polygons:
                                # The size indicates all values in the two-dimension array, and the second dimension is
                                # always size 3 because we have 3D points.
                                if index >= polygon.data.size // 3 - offset:
                                    index -= polygon.data.size // 3 - offset
                                    offset = 1  # This is to avoid the first point when there is more than one polygon, since has the same value as the last point in the previous polygon
                                    continue
                                # The head position is calculated and translated
                                head_position = Vector(polygon.data[index+offset][0], polygon.data[index+offset][1], polygon.data[index+offset][2]) + node.getWorldPosition()
                                break
                            break
                        if self._layer_view._minimum_layer_num > layer:
                            start += element_counts[layer]
                        end += element_counts[layer]

                    # Calculate the range of paths in the last layer
                    current_layer_start = end
                    current_layer_end = end + self._layer_view._current_path_num * 2 # Because each point is used twice

                    # This uses glDrawRangeElements internally to only draw a certain range of lines.
                    # All the layers but the current selected layer are rendered first
                    if self._old_current_path != self._layer_view._current_path_num:
                        self._current_shader = self._layer_shadow_shader
                        self._switching_layers = False
                    if not self._layer_view.isSimulationRunning() and self._old_current_layer != self._layer_view._current_layer_num:
                        self._current_shader = self._layer_shader
                        self._switching_layers = True

                    layers_batch = RenderBatch(self._current_shader, type = RenderBatch.RenderType.Solid, mode = RenderBatch.RenderMode.Lines, range = (start, end), backface_cull = True)
                    layers_batch.addItem(node.getWorldTransformation(), layer_data)
                    layers_batch.render(self._scene.getActiveCamera())

                    # Current selected layer is rendered
                    current_layer_batch = RenderBatch(self._layer_shader, type = RenderBatch.RenderType.Solid, mode = RenderBatch.RenderMode.Lines, range = (current_layer_start, current_layer_end))
                    current_layer_batch.addItem(node.getWorldTransformation(), layer_data)
                    current_layer_batch.render(self._scene.getActiveCamera())

                    self._old_current_layer = self._layer_view._current_layer_num
                    self._old_current_path = self._layer_view._current_path_num

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
                nozzle_node.setVisible(True)
                nozzle_node.setPosition(head_position)
                nozzle_batch = RenderBatch(self._nozzle_shader, type = RenderBatch.RenderType.Transparent)
                nozzle_batch.addItem(nozzle_node.getWorldTransformation(), mesh = nozzle_node.getMeshData())
                nozzle_batch.render(self._scene.getActiveCamera())

        # Render toolhandles on top of the layerview
        if len(tool_handle_batch.items) > 0:
            tool_handle_batch.render(self._scene.getActiveCamera())

        self.release()
