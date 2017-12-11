# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from UM.Application import Application
from UM.Event import Event, KeyEvent
from UM.Job import Job
from UM.Logger import Logger
from UM.Math.Color import Color
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Message import Message
from UM.PluginRegistry import PluginRegistry
from UM.Preferences import Preferences
from UM.Resources import Resources
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.Selection import Selection
from UM.Signal import Signal
from UM.View.GL.OpenGL import OpenGL
from UM.View.GL.OpenGLContext import OpenGLContext
from UM.View.View import View
from UM.i18n import i18nCatalog
from cura.ConvexHullNode import ConvexHullNode

from .NozzleNode import NozzleNode
from .SimulationPass import SimulationPass
from .SimulationViewProxy import SimulationViewProxy

catalog = i18nCatalog("cura")

import numpy
import os.path

## View used to display g-code paths.
class SimulationView(View):
    # Must match SimulationView.qml
    LAYER_VIEW_TYPE_MATERIAL_TYPE = 0
    LAYER_VIEW_TYPE_LINE_TYPE = 1
    LAYER_VIEW_TYPE_FEEDRATE = 2
    LAYER_VIEW_TYPE_THICKNESS = 3

    def __init__(self):
        super().__init__()

        self._max_layers = 0
        self._current_layer_num = 0
        self._minimum_layer_num = 0
        self._current_layer_mesh = None
        self._current_layer_jumps = None
        self._top_layers_job = None
        self._activity = False
        self._old_max_layers = 0

        self._max_paths = 0
        self._current_path_num = 0
        self._minimum_path_num = 0
        self.currentLayerNumChanged.connect(self._onCurrentLayerNumChanged)

        self._busy = False
        self._simulation_running = False

        self._ghost_shader = None
        self._layer_pass = None
        self._composite_pass = None
        self._old_layer_bindings = None
        self._simulationview_composite_shader = None
        self._old_composite_shader = None

        self._global_container_stack = None
        self._proxy = SimulationViewProxy()
        self._controller.getScene().getRoot().childrenChanged.connect(self._onSceneChanged)

        self._resetSettings()
        self._legend_items = None
        self._show_travel_moves = False
        self._nozzle_node = None

        Preferences.getInstance().addPreference("view/top_layer_count", 5)
        Preferences.getInstance().addPreference("view/only_show_top_layers", False)
        Preferences.getInstance().addPreference("view/force_layer_view_compatibility_mode", False)

        Preferences.getInstance().addPreference("layerview/layer_view_type", 0)
        Preferences.getInstance().addPreference("layerview/extruder_opacities", "")

        Preferences.getInstance().addPreference("layerview/show_travel_moves", False)
        Preferences.getInstance().addPreference("layerview/show_helpers", True)
        Preferences.getInstance().addPreference("layerview/show_skin", True)
        Preferences.getInstance().addPreference("layerview/show_infill", True)

        Preferences.getInstance().preferenceChanged.connect(self._onPreferencesChanged)
        self._updateWithPreferences()

        self._solid_layers = int(Preferences.getInstance().getValue("view/top_layer_count"))
        self._only_show_top_layers = bool(Preferences.getInstance().getValue("view/only_show_top_layers"))
        self._compatibility_mode = True  # for safety

        self._wireprint_warning_message = Message(catalog.i18nc("@info:status", "Cura does not accurately display layers when Wire Printing is enabled"),
                                                  title = catalog.i18nc("@info:title", "Simulation View"))

    def _resetSettings(self):
        self._layer_view_type = 0  # 0 is material color, 1 is color by linetype, 2 is speed
        self._extruder_count = 0
        self._extruder_opacity = [1.0, 1.0, 1.0, 1.0]
        self._show_travel_moves = 0
        self._show_helpers = 1
        self._show_skin = 1
        self._show_infill = 1
        self.resetLayerData()

    def getActivity(self):
        return self._activity

    def setActivity(self, activity):
        if self._activity == activity:
            return
        self._activity = activity
        self.activityChanged.emit()

    def getSimulationPass(self):
        if not self._layer_pass:
            # Currently the RenderPass constructor requires a size > 0
            # This should be fixed in RenderPass's constructor.
            self._layer_pass = SimulationPass(1, 1)
            self._compatibility_mode = OpenGLContext.isLegacyOpenGL() or bool(Preferences.getInstance().getValue("view/force_layer_view_compatibility_mode"))
            self._layer_pass.setSimulationView(self)
        return self._layer_pass

    def getCurrentLayer(self):
        return self._current_layer_num

    def getMinimumLayer(self):
        return self._minimum_layer_num

    def getMaxLayers(self):
        return self._max_layers

    def getCurrentPath(self):
        return self._current_path_num

    def getMinimumPath(self):
        return self._minimum_path_num

    def getMaxPaths(self):
        return self._max_paths

    def getNozzleNode(self):
        if not self._nozzle_node:
            self._nozzle_node = NozzleNode()
        return self._nozzle_node

    def _onSceneChanged(self, node):
        self.setActivity(False)
        self.calculateMaxLayers()
        self.calculateMaxPathsOnLayer(self._current_layer_num)

    def isBusy(self):
        return self._busy

    def setBusy(self, busy):
        if busy != self._busy:
            self._busy = busy
            self.busyChanged.emit()

    def isSimulationRunning(self):
        return self._simulation_running

    def setSimulationRunning(self, running):
        self._simulation_running = running

    def resetLayerData(self):
        self._current_layer_mesh = None
        self._current_layer_jumps = None
        self._max_feedrate = sys.float_info.min
        self._min_feedrate = sys.float_info.max
        self._max_thickness = sys.float_info.min
        self._min_thickness = sys.float_info.max

    def beginRendering(self):
        scene = self.getController().getScene()
        renderer = self.getRenderer()

        if not self._ghost_shader:
            self._ghost_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "color.shader"))
            self._ghost_shader.setUniformValue("u_color", Color(*Application.getInstance().getTheme().getColor("layerview_ghost").getRgb()))

        for node in DepthFirstIterator(scene.getRoot()):
            # We do not want to render ConvexHullNode as it conflicts with the bottom layers.
            # However, it is somewhat relevant when the node is selected, so do render it then.
            if type(node) is ConvexHullNode and not Selection.isSelected(node.getWatchedNode()):
                continue

            if not node.render(renderer):
                if (node.getMeshData()) and node.isVisible():
                    renderer.queueNode(node, transparent = True, shader = self._ghost_shader)

    def setLayer(self, value):
        if self._current_layer_num != value:
            self._current_layer_num = value
            if self._current_layer_num < 0:
                self._current_layer_num = 0
            if self._current_layer_num > self._max_layers:
                self._current_layer_num = self._max_layers
            if self._current_layer_num < self._minimum_layer_num:
                self._minimum_layer_num = self._current_layer_num

            self._startUpdateTopLayers()

            self.currentLayerNumChanged.emit()

    def setMinimumLayer(self, value):
        if self._minimum_layer_num != value:
            self._minimum_layer_num = value
            if self._minimum_layer_num < 0:
                self._minimum_layer_num = 0
            if self._minimum_layer_num > self._max_layers:
                self._minimum_layer_num = self._max_layers
            if self._minimum_layer_num > self._current_layer_num:
                self._current_layer_num = self._minimum_layer_num

            self._startUpdateTopLayers()

            self.currentLayerNumChanged.emit()

    def setPath(self, value):
        if self._current_path_num != value:
            self._current_path_num = value
            if self._current_path_num < 0:
                self._current_path_num = 0
            if self._current_path_num > self._max_paths:
                self._current_path_num = self._max_paths
            if self._current_path_num < self._minimum_path_num:
                self._minimum_path_num = self._current_path_num

            self._startUpdateTopLayers()

            self.currentPathNumChanged.emit()

    def setMinimumPath(self, value):
        if self._minimum_path_num != value:
            self._minimum_path_num = value
            if self._minimum_path_num < 0:
                self._minimum_path_num = 0
            if self._minimum_path_num > self._max_layers:
                self._minimum_path_num = self._max_layers
            if self._minimum_path_num > self._current_path_num:
                self._current_path_num = self._minimum_path_num

            self._startUpdateTopLayers()

            self.currentPathNumChanged.emit()

    ##  Set the layer view type
    #
    #   \param layer_view_type integer as in SimulationView.qml and this class
    def setSimulationViewType(self, layer_view_type):
        self._layer_view_type = layer_view_type
        self.currentLayerNumChanged.emit()

    ##  Return the layer view type, integer as in SimulationView.qml and this class
    def getSimulationViewType(self):
        return self._layer_view_type

    ##  Set the extruder opacity
    #
    #   \param extruder_nr 0..3
    #   \param opacity 0.0 .. 1.0
    def setExtruderOpacity(self, extruder_nr, opacity):
        if 0 <= extruder_nr <= 3:
            self._extruder_opacity[extruder_nr] = opacity
            self.currentLayerNumChanged.emit()

    def getExtruderOpacities(self):
        return self._extruder_opacity

    def setShowTravelMoves(self, show):
        self._show_travel_moves = show
        self.currentLayerNumChanged.emit()

    def getShowTravelMoves(self):
        return self._show_travel_moves

    def setShowHelpers(self, show):
        self._show_helpers = show
        self.currentLayerNumChanged.emit()

    def getShowHelpers(self):
        return self._show_helpers

    def setShowSkin(self, show):
        self._show_skin = show
        self.currentLayerNumChanged.emit()

    def getShowSkin(self):
        return self._show_skin

    def setShowInfill(self, show):
        self._show_infill = show
        self.currentLayerNumChanged.emit()

    def getShowInfill(self):
        return self._show_infill

    def getCompatibilityMode(self):
        return self._compatibility_mode

    def getExtruderCount(self):
        return self._extruder_count

    def getMinFeedrate(self):
        return self._min_feedrate

    def getMaxFeedrate(self):
        return self._max_feedrate

    def getMinThickness(self):
        return self._min_thickness

    def getMaxThickness(self):
        return self._max_thickness

    def calculateMaxLayers(self):
        scene = self.getController().getScene()

        self._old_max_layers = self._max_layers
        ## Recalculate num max layers
        new_max_layers = 0
        for node in DepthFirstIterator(scene.getRoot()):
            layer_data = node.callDecoration("getLayerData")
            if not layer_data:
                continue

            self.setActivity(True)
            min_layer_number = sys.maxsize
            max_layer_number = -sys.maxsize
            for layer_id in layer_data.getLayers():
                # Store the max and min feedrates and thicknesses for display purposes
                for p in layer_data.getLayer(layer_id).polygons:
                    self._max_feedrate = max(float(p.lineFeedrates.max()), self._max_feedrate)
                    self._min_feedrate = min(float(p.lineFeedrates.min()), self._min_feedrate)
                    self._max_thickness = max(float(p.lineThicknesses.max()), self._max_thickness)
                    self._min_thickness = min(float(p.lineThicknesses.min()), self._min_thickness)
                if max_layer_number < layer_id:
                    max_layer_number = layer_id
                if min_layer_number > layer_id:
                    min_layer_number = layer_id
            layer_count = max_layer_number - min_layer_number

            if new_max_layers < layer_count:
                new_max_layers = layer_count

        if new_max_layers > 0 and new_max_layers != self._old_max_layers:
            self._max_layers = new_max_layers

            # The qt slider has a bit of weird behavior that if the maxvalue needs to be changed first
            # if it's the largest value. If we don't do this, we can have a slider block outside of the
            # slider.
            if new_max_layers > self._current_layer_num:
                self.maxLayersChanged.emit()
                self.setLayer(int(self._max_layers))
            else:
                self.setLayer(int(self._max_layers))
                self.maxLayersChanged.emit()
        self._startUpdateTopLayers()

    def calculateMaxPathsOnLayer(self, layer_num):
        # Update the currentPath
        scene = self.getController().getScene()
        for node in DepthFirstIterator(scene.getRoot()):
            layer_data = node.callDecoration("getLayerData")
            if not layer_data:
                continue

            layer = layer_data.getLayer(layer_num)
            if layer is None:
                return
            new_max_paths = layer.lineMeshElementCount()
            if new_max_paths >= 0 and new_max_paths != self._max_paths:
                self._max_paths = new_max_paths
                self.maxPathsChanged.emit()

            self.setPath(int(new_max_paths))

    maxLayersChanged = Signal()
    maxPathsChanged = Signal()
    currentLayerNumChanged = Signal()
    currentPathNumChanged = Signal()
    globalStackChanged = Signal()
    preferencesChanged = Signal()
    busyChanged = Signal()
    activityChanged = Signal()

    ##  Hackish way to ensure the proxy is already created, which ensures that the layerview.qml is already created
    #   as this caused some issues.
    def getProxy(self, engine, script_engine):
        return self._proxy

    def endRendering(self):
        pass

    def event(self, event):
        modifiers = QApplication.keyboardModifiers()
        ctrl_is_active = modifiers & Qt.ControlModifier
        shift_is_active = modifiers & Qt.ShiftModifier
        if event.type == Event.KeyPressEvent and ctrl_is_active:
            amount = 10 if shift_is_active else 1
            if event.key == KeyEvent.UpKey:
                self.setLayer(self._current_layer_num + amount)
                return True
            if event.key == KeyEvent.DownKey:
                self.setLayer(self._current_layer_num - amount)
                return True

        if event.type == Event.ViewActivateEvent:
            # Make sure the SimulationPass is created
            layer_pass = self.getSimulationPass()
            self.getRenderer().addRenderPass(layer_pass)

            # Make sure the NozzleNode is add to the root
            nozzle = self.getNozzleNode()
            nozzle.setParent(self.getController().getScene().getRoot())
            nozzle.setVisible(False)

            Application.getInstance().globalContainerStackChanged.connect(self._onGlobalStackChanged)
            self._onGlobalStackChanged()

            if not self._simulationview_composite_shader:
                self._simulationview_composite_shader = OpenGL.getInstance().createShaderProgram(os.path.join(PluginRegistry.getInstance().getPluginPath("SimulationView"), "simulationview_composite.shader"))
                theme = Application.getInstance().getTheme()
                self._simulationview_composite_shader.setUniformValue("u_background_color", Color(*theme.getColor("viewport_background").getRgb()))
                self._simulationview_composite_shader.setUniformValue("u_outline_color", Color(*theme.getColor("model_selection_outline").getRgb()))

            if not self._composite_pass:
                self._composite_pass = self.getRenderer().getRenderPass("composite")

            self._old_layer_bindings = self._composite_pass.getLayerBindings()[:] # make a copy so we can restore to it later
            self._composite_pass.getLayerBindings().append("simulationview")
            self._old_composite_shader = self._composite_pass.getCompositeShader()
            self._composite_pass.setCompositeShader(self._simulationview_composite_shader)

        elif event.type == Event.ViewDeactivateEvent:
            self._wireprint_warning_message.hide()
            Application.getInstance().globalContainerStackChanged.disconnect(self._onGlobalStackChanged)
            if self._global_container_stack:
                self._global_container_stack.propertyChanged.disconnect(self._onPropertyChanged)

            self._nozzle_node.setParent(None)
            self.getRenderer().removeRenderPass(self._layer_pass)
            self._composite_pass.setLayerBindings(self._old_layer_bindings)
            self._composite_pass.setCompositeShader(self._old_composite_shader)

    def getCurrentLayerMesh(self):
        return self._current_layer_mesh

    def getCurrentLayerJumps(self):
        return self._current_layer_jumps

    def _onGlobalStackChanged(self):
        if self._global_container_stack:
            self._global_container_stack.propertyChanged.disconnect(self._onPropertyChanged)
        self._global_container_stack = Application.getInstance().getGlobalContainerStack()
        if self._global_container_stack:
            self._global_container_stack.propertyChanged.connect(self._onPropertyChanged)
            self._extruder_count = self._global_container_stack.getProperty("machine_extruder_count", "value")
            self._onPropertyChanged("wireframe_enabled", "value")
            self.globalStackChanged.emit()
        else:
            self._wireprint_warning_message.hide()

    def _onPropertyChanged(self, key, property_name):
        if key == "wireframe_enabled" and property_name == "value":
            if self._global_container_stack.getProperty("wireframe_enabled", "value"):
                self._wireprint_warning_message.show()
            else:
                self._wireprint_warning_message.hide()

    def _onCurrentLayerNumChanged(self):
        self.calculateMaxPathsOnLayer(self._current_layer_num)

    def _startUpdateTopLayers(self):
        if not self._compatibility_mode:
            return

        if self._top_layers_job:
            self._top_layers_job.finished.disconnect(self._updateCurrentLayerMesh)
            self._top_layers_job.cancel()

        self.setBusy(True)

        self._top_layers_job = _CreateTopLayersJob(self._controller.getScene(), self._current_layer_num, self._solid_layers)
        self._top_layers_job.finished.connect(self._updateCurrentLayerMesh)
        self._top_layers_job.start()

    def _updateCurrentLayerMesh(self, job):
        self.setBusy(False)

        if not job.getResult():
            return
        self.resetLayerData()  # Reset the layer data only when job is done. Doing it now prevents "blinking" data.
        self._current_layer_mesh = job.getResult().get("layers")
        if self._show_travel_moves:
            self._current_layer_jumps = job.getResult().get("jumps")
        self._controller.getScene().sceneChanged.emit(self._controller.getScene().getRoot())

        self._top_layers_job = None

    def _updateWithPreferences(self):
        self._solid_layers = int(Preferences.getInstance().getValue("view/top_layer_count"))
        self._only_show_top_layers = bool(Preferences.getInstance().getValue("view/only_show_top_layers"))
        self._compatibility_mode = OpenGLContext.isLegacyOpenGL() or bool(
            Preferences.getInstance().getValue("view/force_layer_view_compatibility_mode"))

        self.setSimulationViewType(int(float(Preferences.getInstance().getValue("layerview/layer_view_type"))));

        for extruder_nr, extruder_opacity in enumerate(Preferences.getInstance().getValue("layerview/extruder_opacities").split("|")):
            try:
                opacity = float(extruder_opacity)
            except ValueError:
                opacity = 1.0
            self.setExtruderOpacity(extruder_nr, opacity)

        self.setShowTravelMoves(bool(Preferences.getInstance().getValue("layerview/show_travel_moves")))
        self.setShowHelpers(bool(Preferences.getInstance().getValue("layerview/show_helpers")))
        self.setShowSkin(bool(Preferences.getInstance().getValue("layerview/show_skin")))
        self.setShowInfill(bool(Preferences.getInstance().getValue("layerview/show_infill")))

        self._startUpdateTopLayers()
        self.preferencesChanged.emit()

    def _onPreferencesChanged(self, preference):
        if preference not in {
            "view/top_layer_count",
            "view/only_show_top_layers",
            "view/force_layer_view_compatibility_mode",
            "layerview/layer_view_type",
            "layerview/extruder_opacities",
            "layerview/show_travel_moves",
            "layerview/show_helpers",
            "layerview/show_skin",
            "layerview/show_infill",
            }:
            return

        self._updateWithPreferences()


class _CreateTopLayersJob(Job):
    def __init__(self, scene, layer_number, solid_layers):
        super().__init__()

        self._scene = scene
        self._layer_number = layer_number
        self._solid_layers = solid_layers
        self._cancel = False

    def run(self):
        layer_data = None
        for node in DepthFirstIterator(self._scene.getRoot()):
            layer_data = node.callDecoration("getLayerData")
            if layer_data:
                break

        if self._cancel or not layer_data:
            return

        layer_mesh = MeshBuilder()
        for i in range(self._solid_layers):
            layer_number = self._layer_number - i
            if layer_number < 0:
                continue

            try:
                layer = layer_data.getLayer(layer_number).createMesh()
            except Exception:
                Logger.logException("w", "An exception occurred while creating layer mesh.")
                return

            if not layer or layer.getVertices() is None:
                continue

            layer_mesh.addIndices(layer_mesh.getVertexCount() + layer.getIndices())
            layer_mesh.addVertices(layer.getVertices())

            # Scale layer color by a brightness factor based on the current layer number
            # This will result in a range of 0.5 - 1.0 to multiply colors by.
            brightness = numpy.ones((1, 4), dtype=numpy.float32) * (2.0 - (i / self._solid_layers)) / 2.0
            brightness[0, 3] = 1.0
            layer_mesh.addColors(layer.getColors() * brightness)

            if self._cancel:
                return

            Job.yieldThread()

        if self._cancel:
            return

        Job.yieldThread()
        jump_mesh = layer_data.getLayer(self._layer_number).createJumps()
        if not jump_mesh or jump_mesh.getVertices() is None:
            jump_mesh = None

        self.setResult({"layers": layer_mesh.build(), "jumps": jump_mesh})

    def cancel(self):
        self._cancel = True
        super().cancel()

