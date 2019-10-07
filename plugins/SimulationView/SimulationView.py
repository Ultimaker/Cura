# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QOpenGLContext
from PyQt5.QtWidgets import QApplication

from UM.Application import Application
from UM.Event import Event, KeyEvent
from UM.Job import Job
from UM.Logger import Logger
from UM.Math.Color import Color
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Message import Message
from UM.Platform import Platform
from UM.PluginRegistry import PluginRegistry
from UM.Qt.QtApplication import QtApplication
from UM.Resources import Resources
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator

from UM.Scene.Selection import Selection
from UM.Signal import Signal
from UM.View.CompositePass import CompositePass
from UM.View.GL.OpenGL import OpenGL
from UM.View.GL.OpenGLContext import OpenGLContext
from UM.View.GL.ShaderProgram import ShaderProgram

from UM.i18n import i18nCatalog
from cura.CuraView import CuraView
from cura.Scene.ConvexHullNode import ConvexHullNode
from cura.CuraApplication import CuraApplication

from .NozzleNode import NozzleNode
from .SimulationPass import SimulationPass
from .SimulationViewProxy import SimulationViewProxy
import numpy
import os.path

from typing import Optional, TYPE_CHECKING, List, cast

if TYPE_CHECKING:
    from UM.Scene.SceneNode import SceneNode
    from UM.Scene.Scene import Scene
    from UM.Settings.ContainerStack import ContainerStack

catalog = i18nCatalog("cura")


## The preview layer view. It is used to display g-code paths.
class SimulationView(CuraView):
    # Must match SimulationViewMenuComponent.qml
    LAYER_VIEW_TYPE_MATERIAL_TYPE = 0
    LAYER_VIEW_TYPE_LINE_TYPE = 1
    LAYER_VIEW_TYPE_FEEDRATE = 2
    LAYER_VIEW_TYPE_THICKNESS = 3

    def __init__(self, parent = None) -> None:
        super().__init__(parent)

        self._max_layers = 0
        self._current_layer_num = 0
        self._minimum_layer_num = 0
        self._current_layer_mesh = None
        self._current_layer_jumps = None
        self._top_layers_job = None  # type: Optional["_CreateTopLayersJob"]
        self._activity = False
        self._old_max_layers = 0

        self._max_paths = 0
        self._current_path_num = 0
        self._minimum_path_num = 0
        self.currentLayerNumChanged.connect(self._onCurrentLayerNumChanged)

        self._busy = False
        self._simulation_running = False

        self._ghost_shader = None  # type: Optional["ShaderProgram"]
        self._layer_pass = None  # type: Optional[SimulationPass]
        self._composite_pass = None  # type: Optional[CompositePass]
        self._old_layer_bindings = None  # type: Optional[List[str]]
        self._simulationview_composite_shader = None  # type: Optional["ShaderProgram"]
        self._old_composite_shader = None  # type: Optional["ShaderProgram"]

        self._max_feedrate = sys.float_info.min
        self._min_feedrate = sys.float_info.max
        self._max_thickness = sys.float_info.min
        self._min_thickness = sys.float_info.max

        self._global_container_stack = None  # type: Optional[ContainerStack]
        self._proxy = None

        self._resetSettings()
        self._legend_items = None
        self._show_travel_moves = False
        self._nozzle_node = None  # type: Optional[NozzleNode]

        Application.getInstance().getPreferences().addPreference("view/top_layer_count", 5)
        Application.getInstance().getPreferences().addPreference("view/only_show_top_layers", False)
        Application.getInstance().getPreferences().addPreference("view/force_layer_view_compatibility_mode", False)

        Application.getInstance().getPreferences().addPreference("layerview/layer_view_type", 0)
        Application.getInstance().getPreferences().addPreference("layerview/extruder_opacities", "")

        Application.getInstance().getPreferences().addPreference("layerview/show_travel_moves", False)
        Application.getInstance().getPreferences().addPreference("layerview/show_helpers", True)
        Application.getInstance().getPreferences().addPreference("layerview/show_skin", True)
        Application.getInstance().getPreferences().addPreference("layerview/show_infill", True)

        self._updateWithPreferences()

        self._solid_layers = int(Application.getInstance().getPreferences().getValue("view/top_layer_count"))
        self._only_show_top_layers = bool(Application.getInstance().getPreferences().getValue("view/only_show_top_layers"))
        self._compatibility_mode = self._evaluateCompatibilityMode()

        self._wireprint_warning_message = Message(catalog.i18nc("@info:status", "Cura does not accurately display layers when Wire Printing is enabled"),
                                                  title = catalog.i18nc("@info:title", "Simulation View"))

        QtApplication.getInstance().engineCreatedSignal.connect(self._onEngineCreated)

    def _onEngineCreated(self) -> None:
        plugin_path = PluginRegistry.getInstance().getPluginPath(self.getPluginId())
        if plugin_path:
            self.addDisplayComponent("main", os.path.join(plugin_path, "SimulationViewMainComponent.qml"))
            self.addDisplayComponent("menu", os.path.join(plugin_path, "SimulationViewMenuComponent.qml"))
        else:
            Logger.log("e", "Unable to find the path for %s", self.getPluginId())

    def _evaluateCompatibilityMode(self) -> bool:
        return OpenGLContext.isLegacyOpenGL() or bool(Application.getInstance().getPreferences().getValue("view/force_layer_view_compatibility_mode"))

    def _resetSettings(self) -> None:
        self._layer_view_type = 0  # type: int # 0 is material color, 1 is color by linetype, 2 is speed, 3 is layer thickness
        self._extruder_count = 0
        self._extruder_opacity = [1.0, 1.0, 1.0, 1.0]
        self._show_travel_moves = False
        self._show_helpers = True
        self._show_skin = True
        self._show_infill = True
        self.resetLayerData()

    def getActivity(self) -> bool:
        return self._activity

    def setActivity(self, activity: bool) -> None:
        if self._activity == activity:
            return
        self._activity = activity
        self.activityChanged.emit()

    def getSimulationPass(self) -> SimulationPass:
        if not self._layer_pass:
            # Currently the RenderPass constructor requires a size > 0
            # This should be fixed in RenderPass's constructor.
            self._layer_pass = SimulationPass(1, 1)
            self._compatibility_mode = self._evaluateCompatibilityMode()
            self._layer_pass.setSimulationView(self)
        return self._layer_pass

    def getCurrentLayer(self) -> int:
        return self._current_layer_num

    def getMinimumLayer(self) -> int:
        return self._minimum_layer_num

    def getMaxLayers(self) -> int:
        return self._max_layers

    def getCurrentPath(self) -> int:
        return self._current_path_num

    def getMinimumPath(self) -> int:
        return self._minimum_path_num

    def getMaxPaths(self) -> int:
        return self._max_paths

    def getNozzleNode(self) -> NozzleNode:
        if not self._nozzle_node:
            self._nozzle_node = NozzleNode()
        return self._nozzle_node

    def _onSceneChanged(self, node: "SceneNode") -> None:
        if node.getMeshData() is None:
            return
        self.setActivity(False)
        self.calculateMaxLayers()
        self.calculateMaxPathsOnLayer(self._current_layer_num)

    def isBusy(self) -> bool:
        return self._busy

    def setBusy(self, busy: bool) -> None:
        if busy != self._busy:
            self._busy = busy
            self.busyChanged.emit()

    def isSimulationRunning(self) -> bool:
        return self._simulation_running

    def setSimulationRunning(self, running: bool) -> None:
        self._simulation_running = running

    def resetLayerData(self) -> None:
        self._current_layer_mesh = None
        self._current_layer_jumps = None
        self._max_feedrate = sys.float_info.min
        self._min_feedrate = sys.float_info.max
        self._max_thickness = sys.float_info.min
        self._min_thickness = sys.float_info.max

    def beginRendering(self) -> None:
        scene = self.getController().getScene()
        renderer = self.getRenderer()

        if not self._ghost_shader:
            self._ghost_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "color.shader"))
            theme = CuraApplication.getInstance().getTheme()
            if theme is not None:
                self._ghost_shader.setUniformValue("u_color", Color(*theme.getColor("layerview_ghost").getRgb()))

        for node in DepthFirstIterator(scene.getRoot()):
            # We do not want to render ConvexHullNode as it conflicts with the bottom layers.
            # However, it is somewhat relevant when the node is selected, so do render it then.
            if type(node) is ConvexHullNode and not Selection.isSelected(cast(ConvexHullNode, node).getWatchedNode()):
                continue

            if not node.render(renderer):
                if (node.getMeshData()) and node.isVisible():
                    renderer.queueNode(node, transparent = True, shader = self._ghost_shader)

    def setLayer(self, value: int) -> None:
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

    def setMinimumLayer(self, value: int) -> None:
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

    def setPath(self, value: int) -> None:
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

    def setMinimumPath(self, value: int) -> None:
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
    def setSimulationViewType(self, layer_view_type: int) -> None:
        self._layer_view_type = layer_view_type
        self.currentLayerNumChanged.emit()

    ##  Return the layer view type, integer as in SimulationView.qml and this class
    def getSimulationViewType(self) -> int:
        return self._layer_view_type

    ##  Set the extruder opacity
    #
    #   \param extruder_nr 0..3
    #   \param opacity 0.0 .. 1.0
    def setExtruderOpacity(self, extruder_nr: int, opacity: float) -> None:
        if 0 <= extruder_nr <= 3:
            self._extruder_opacity[extruder_nr] = opacity
            self.currentLayerNumChanged.emit()

    def getExtruderOpacities(self)-> List[float]:
        return self._extruder_opacity

    def setShowTravelMoves(self, show):
        self._show_travel_moves = show
        self.currentLayerNumChanged.emit()

    def getShowTravelMoves(self):
        return self._show_travel_moves

    def setShowHelpers(self, show: bool) -> None:
        self._show_helpers = show
        self.currentLayerNumChanged.emit()

    def getShowHelpers(self) -> bool:
        return self._show_helpers

    def setShowSkin(self, show: bool) -> None:
        self._show_skin = show
        self.currentLayerNumChanged.emit()

    def getShowSkin(self) -> bool:
        return self._show_skin

    def setShowInfill(self, show: bool) -> None:
        self._show_infill = show
        self.currentLayerNumChanged.emit()

    def getShowInfill(self) -> bool:
        return self._show_infill

    def getCompatibilityMode(self) -> bool:
        return self._compatibility_mode

    def getExtruderCount(self) -> int:
        return self._extruder_count

    def getMinFeedrate(self) -> float:
        if abs(self._min_feedrate - sys.float_info.max) < 10: # Some lenience due to floating point rounding.
            return 0.0 # If it's still max-float, there are no measurements. Use 0 then.
        return self._min_feedrate

    def getMaxFeedrate(self) -> float:
        return self._max_feedrate

    def getMinThickness(self) -> float:
        if abs(self._min_thickness - sys.float_info.max) < 10: # Some lenience due to floating point rounding.
            return 0.0 # If it's still max-float, there are no measurements. Use 0 then.
        return self._min_thickness

    def getMaxThickness(self) -> float:
        return self._max_thickness

    def calculateMaxLayers(self) -> None:
        scene = self.getController().getScene()

        self._old_max_layers = self._max_layers
        ## Recalculate num max layers
        new_max_layers = -1
        for node in DepthFirstIterator(scene.getRoot()):  # type: ignore
            layer_data = node.callDecoration("getLayerData")
            if not layer_data:
                continue

            self.setActivity(True)
            min_layer_number = sys.maxsize
            max_layer_number = -sys.maxsize
            for layer_id in layer_data.getLayers():

                # If a layer doesn't contain any polygons, skip it (for infill meshes taller than print objects
                if len(layer_data.getLayer(layer_id).polygons) < 1:
                    continue

                # Store the max and min feedrates and thicknesses for display purposes
                for p in layer_data.getLayer(layer_id).polygons:
                    self._max_feedrate = max(float(p.lineFeedrates.max()), self._max_feedrate)
                    self._min_feedrate = min(float(p.lineFeedrates.min()), self._min_feedrate)
                    self._max_thickness = max(float(p.lineThicknesses.max()), self._max_thickness)
                    try:
                        self._min_thickness = min(float(p.lineThicknesses[numpy.nonzero(p.lineThicknesses)].min()), self._min_thickness)
                    except ValueError:
                        # Sometimes, when importing a GCode the line thicknesses are zero and so the minimum (avoiding
                        # the zero) can't be calculated
                        Logger.log("i", "Min thickness can't be calculated because all the values are zero")
                if max_layer_number < layer_id:
                    max_layer_number = layer_id
                if min_layer_number > layer_id:
                    min_layer_number = layer_id
            layer_count = max_layer_number - min_layer_number

            if new_max_layers < layer_count:
                new_max_layers = layer_count

        if new_max_layers >= 0 and new_max_layers != self._old_max_layers:
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

    def calculateMaxPathsOnLayer(self, layer_num: int) -> None:
        # Update the currentPath
        scene = self.getController().getScene()
        for node in DepthFirstIterator(scene.getRoot()):  # type: ignore
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
        if self._proxy is None:
            self._proxy = SimulationViewProxy(self)
        return self._proxy

    def endRendering(self) -> None:
        pass

    def event(self, event) -> bool:
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
            # Start listening to changes.
            Application.getInstance().getPreferences().preferenceChanged.connect(self._onPreferencesChanged)
            self._controller.getScene().getRoot().childrenChanged.connect(self._onSceneChanged)

            self.calculateMaxLayers()
            self.calculateMaxPathsOnLayer(self._current_layer_num)

            # FIX: on Max OS X, somehow QOpenGLContext.currentContext() can become None during View switching.
            # This can happen when you do the following steps:
            #   1. Start Cura
            #   2. Load a model
            #   3. Switch to Custom mode
            #   4. Select the model and click on the per-object tool icon
            #   5. Switch view to Layer view or X-Ray
            #   6. Cura will very likely crash
            # It seems to be a timing issue that the currentContext can somehow be empty, but I have no clue why.
            # This fix tries to reschedule the view changing event call on the Qt thread again if the current OpenGL
            # context is None.
            if Platform.isOSX():
                if QOpenGLContext.currentContext() is None:
                    Logger.log("d", "current context of OpenGL is empty on Mac OS X, will try to create shaders later")
                    CuraApplication.getInstance().callLater(lambda e=event: self.event(e))
                    return False

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
                plugin_path = cast(str, PluginRegistry.getInstance().getPluginPath("SimulationView"))
                self._simulationview_composite_shader = OpenGL.getInstance().createShaderProgram(os.path.join(plugin_path, "simulationview_composite.shader"))
                theme = CuraApplication.getInstance().getTheme()
                if theme is not None:
                    self._simulationview_composite_shader.setUniformValue("u_background_color", Color(*theme.getColor("viewport_background").getRgb()))
                    self._simulationview_composite_shader.setUniformValue("u_outline_color", Color(*theme.getColor("model_selection_outline").getRgb()))

            if not self._composite_pass:
                self._composite_pass = cast(CompositePass, self.getRenderer().getRenderPass("composite"))

            self._old_layer_bindings = self._composite_pass.getLayerBindings()[:]  # make a copy so we can restore to it later
            self._composite_pass.getLayerBindings().append("simulationview")
            self._old_composite_shader = self._composite_pass.getCompositeShader()
            self._composite_pass.setCompositeShader(self._simulationview_composite_shader)

        elif event.type == Event.ViewDeactivateEvent:
            self._controller.getScene().getRoot().childrenChanged.disconnect(self._onSceneChanged)
            Application.getInstance().getPreferences().preferenceChanged.disconnect(self._onPreferencesChanged)
            self._wireprint_warning_message.hide()
            Application.getInstance().globalContainerStackChanged.disconnect(self._onGlobalStackChanged)
            if self._global_container_stack:
                self._global_container_stack.propertyChanged.disconnect(self._onPropertyChanged)
            if self._nozzle_node:
                self._nozzle_node.setParent(None)
            self.getRenderer().removeRenderPass(self._layer_pass)
            if self._composite_pass:
                self._composite_pass.setLayerBindings(cast(List[str], self._old_layer_bindings))
                self._composite_pass.setCompositeShader(cast(ShaderProgram, self._old_composite_shader))

        return False

    def getCurrentLayerMesh(self):
        return self._current_layer_mesh

    def getCurrentLayerJumps(self):
        return self._current_layer_jumps

    def _onGlobalStackChanged(self) -> None:
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

    def _onPropertyChanged(self, key: str, property_name: str) -> None:
        if key == "wireframe_enabled" and property_name == "value":
            if self._global_container_stack and self._global_container_stack.getProperty("wireframe_enabled", "value"):
                self._wireprint_warning_message.show()
            else:
                self._wireprint_warning_message.hide()

    def _onCurrentLayerNumChanged(self) -> None:
        self.calculateMaxPathsOnLayer(self._current_layer_num)

    def _startUpdateTopLayers(self) -> None:
        if not self._compatibility_mode:
            return

        if self._top_layers_job:
            self._top_layers_job.finished.disconnect(self._updateCurrentLayerMesh)
            self._top_layers_job.cancel()

        self.setBusy(True)

        self._top_layers_job = _CreateTopLayersJob(self._controller.getScene(), self._current_layer_num, self._solid_layers)
        self._top_layers_job.finished.connect(self._updateCurrentLayerMesh)  # type: ignore  # mypy doesn't understand the whole private class thing that's going on here.
        self._top_layers_job.start()  # type: ignore

    def _updateCurrentLayerMesh(self, job: "_CreateTopLayersJob") -> None:
        self.setBusy(False)

        if not job.getResult():
            return
        self.resetLayerData()  # Reset the layer data only when job is done. Doing it now prevents "blinking" data.
        self._current_layer_mesh = job.getResult().get("layers")
        if self._show_travel_moves:
            self._current_layer_jumps = job.getResult().get("jumps")
        self._controller.getScene().sceneChanged.emit(self._controller.getScene().getRoot())

        self._top_layers_job = None

    def _updateWithPreferences(self) -> None:
        self._solid_layers = int(Application.getInstance().getPreferences().getValue("view/top_layer_count"))
        self._only_show_top_layers = bool(Application.getInstance().getPreferences().getValue("view/only_show_top_layers"))
        self._compatibility_mode = self._evaluateCompatibilityMode()

        self.setSimulationViewType(int(float(Application.getInstance().getPreferences().getValue("layerview/layer_view_type"))))

        for extruder_nr, extruder_opacity in enumerate(Application.getInstance().getPreferences().getValue("layerview/extruder_opacities").split("|")):
            try:
                opacity = float(extruder_opacity)
            except ValueError:
                opacity = 1.0
            self.setExtruderOpacity(extruder_nr, opacity)

        self.setShowTravelMoves(bool(Application.getInstance().getPreferences().getValue("layerview/show_travel_moves")))
        self.setShowHelpers(bool(Application.getInstance().getPreferences().getValue("layerview/show_helpers")))
        self.setShowSkin(bool(Application.getInstance().getPreferences().getValue("layerview/show_skin")))
        self.setShowInfill(bool(Application.getInstance().getPreferences().getValue("layerview/show_infill")))

        self._startUpdateTopLayers()
        self.preferencesChanged.emit()

    def _onPreferencesChanged(self, preference: str) -> None:
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
    def __init__(self, scene: "Scene", layer_number: int, solid_layers: int) -> None:
        super().__init__()

        self._scene = scene
        self._layer_number = layer_number
        self._solid_layers = solid_layers
        self._cancel = False

    def run(self) -> None:
        layer_data = None
        for node in DepthFirstIterator(self._scene.getRoot()):  # type: ignore
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

    def cancel(self) -> None:
        self._cancel = True
        super().cancel()
