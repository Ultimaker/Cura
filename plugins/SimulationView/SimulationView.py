# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import math
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QOpenGLContext
from PyQt6.QtWidgets import QApplication

from UM.Application import Application
from UM.Event import Event, KeyEvent
from UM.Job import Job
from UM.Logger import Logger
from UM.Math.Color import Color
from UM.Math.Matrix import Matrix
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
from cura.LayerPolygon import LayerPolygon  # To distinguish line types.
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


class SimulationView(CuraView):
    """The preview layer view. It is used to display g-code paths."""

    # Must match SimulationViewMenuComponent.qml
    LAYER_VIEW_TYPE_MATERIAL_TYPE = 0
    LAYER_VIEW_TYPE_LINE_TYPE = 1
    LAYER_VIEW_TYPE_FEEDRATE = 2
    LAYER_VIEW_TYPE_THICKNESS = 3
    SIMULATION_FACTOR = 2

    _no_layers_warning_preference = "view/no_layers_warning"

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
        self._current_path_num: float = 0.0
        self._current_time = 0.0
        self._minimum_path_num = 0
        self.currentLayerNumChanged.connect(self._onCurrentLayerNumChanged)

        self._busy = False
        self._simulation_running = False

        self._ghost_shader: Optional["ShaderProgram"] = None
        self._layer_pass: Optional[SimulationPass] = None
        self._composite_pass: Optional[CompositePass] = None
        self._old_layer_bindings: Optional[List[str]] = None
        self._simulationview_composite_shader: Optional["ShaderProgram"] = None
        self._old_composite_shader: Optional["ShaderProgram"] = None

        self._max_feedrate = sys.float_info.min
        self._min_feedrate = sys.float_info.max
        self._max_thickness = sys.float_info.min
        self._min_thickness = sys.float_info.max
        self._max_line_width = sys.float_info.min
        self._min_line_width = sys.float_info.max
        self._min_flow_rate = sys.float_info.max
        self._max_flow_rate = sys.float_info.min
        self._cumulative_line_duration_layer: Optional[int] = None
        self._cumulative_line_duration: List[float] = []

        self._global_container_stack: Optional[ContainerStack] = None
        self._proxy = None

        self._resetSettings()
        self._legend_items = None
        self._show_travel_moves = False
        self._nozzle_node: Optional[NozzleNode] = None

        Application.getInstance().getPreferences().addPreference("view/top_layer_count", 5)
        Application.getInstance().getPreferences().addPreference("view/only_show_top_layers", False)
        Application.getInstance().getPreferences().addPreference("view/force_layer_view_compatibility_mode", False)

        Application.getInstance().getPreferences().addPreference("layerview/layer_view_type", 1)  # Default to "Line Type".
        Application.getInstance().getPreferences().addPreference("layerview/extruder_opacities", "")

        Application.getInstance().getPreferences().addPreference("layerview/show_travel_moves", False)
        Application.getInstance().getPreferences().addPreference("layerview/show_helpers", True)
        Application.getInstance().getPreferences().addPreference("layerview/show_skin", True)
        Application.getInstance().getPreferences().addPreference("layerview/show_infill", True)
        Application.getInstance().getPreferences().addPreference("layerview/show_starts", True)

        self.visibleStructuresChanged.connect(self.calculateColorSchemeLimits)
        self._updateWithPreferences()

        self._solid_layers = int(Application.getInstance().getPreferences().getValue("view/top_layer_count"))
        self._only_show_top_layers = bool(Application.getInstance().getPreferences().getValue("view/only_show_top_layers"))
        self._compatibility_mode = self._evaluateCompatibilityMode()

        self._slice_first_warning_message = Message(catalog.i18nc("@info:status", "Nothing is shown because you need to slice first."),
            title=catalog.i18nc("@info:title", "No layers to show"),
            option_text=catalog.i18nc("@info:option_text",
                                      "Do not show this message again"),
            option_state=False,
            message_type=Message.MessageType.WARNING)
        self._slice_first_warning_message.optionToggled.connect(self._onDontAskMeAgain)
        CuraApplication.getInstance().getPreferences().addPreference(self._no_layers_warning_preference, True)

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
        self._extruder_opacity = [[1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0]]
        self._show_travel_moves = False
        self._show_helpers = True
        self._show_skin = True
        self._show_infill = True
        self._show_starts = True
        self.resetLayerData()

    def getActivity(self) -> bool:
        return self._activity

    def setActivity(self, activity: bool) -> None:
        if self._activity == activity:
            return
        self._activity = activity
        self._updateSliceWarningVisibility()
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

    def getCurrentPath(self) -> float:
        return self._current_path_num

    def setTime(self, time: float) -> None:
        cumulative_line_duration = self.cumulativeLineDuration()
        if len(cumulative_line_duration) > 0:
            self._current_time = time
            left_i = 0
            right_i = len(cumulative_line_duration) - 1
            total_duration = cumulative_line_duration[-1]
            # make an educated guess about where to start
            i = int(right_i * max(0.0, min(1.0, self._current_time / total_duration)))
            # binary search for the correct path
            while left_i < right_i:
                if cumulative_line_duration[i] <= self._current_time:
                    left_i = i + 1
                else:
                    right_i = i
                i = int((left_i + right_i) / 2)

            left_value = cumulative_line_duration[i - 1] if i > 0 else 0.0
            right_value = cumulative_line_duration[i]

            if not (left_value <= self._current_time <= right_value):
                Logger.warn(
                    f"Binary search error (out of bounds): index {i}: left value {left_value} right value {right_value} and current time is {self._current_time}")

            segment_duration = right_value - left_value
            fractional_value = 0.0 if segment_duration == 0.0 else (self._current_time - left_value) / segment_duration

            self.setPath(i + fractional_value)

    def advanceTime(self, time_increase: float) -> bool:
        """
        Advance the time by the given amount.

        :param time_increase: The amount of time to advance (in seconds).
        :return: True if the time was advanced, False if the end of the simulation was reached.
        """
        total_duration = 0.0
        if len(self.cumulativeLineDuration()) > 0:
            total_duration = self.cumulativeLineDuration()[-1]

        if self._current_time + time_increase > total_duration:
            # If we have reached the end of the simulation, go to the next layer.
            if self.getCurrentLayer() == self.getMaxLayers():
                # If we are already at the last layer, go to the first layer.
                self.setTime(total_duration)
                return False

            # advance to the next layer, and reset the time
            self.setLayer(self.getCurrentLayer() + 1)
            self.setTime(0.0)
        else:
            self.setTime(self._current_time + time_increase)
        return True

    def cumulativeLineDuration(self) -> List[float]:
        # Make sure _cumulative_line_duration is initialized properly
        if self.getCurrentLayer() != self._cumulative_line_duration_layer:
            #clear cache
            self._cumulative_line_duration = []
            total_duration = 0.0
            polylines = self.getLayerData()
            if polylines is not None:
                for polyline in polylines.polygons:
                    for line_duration in list((polyline.lineLengths / polyline.lineFeedrates)[0]):
                        total_duration += line_duration / SimulationView.SIMULATION_FACTOR
                        self._cumulative_line_duration.append(total_duration)
                    # for tool change we add an extra tool path
                    self._cumulative_line_duration.append(total_duration)
            # set current cached layer
            self._cumulative_line_duration_layer = self.getCurrentLayer()

        return self._cumulative_line_duration

    def getLayerData(self) -> Optional["LayerData"]:
        scene = self.getController().getScene()
        for node in DepthFirstIterator(scene.getRoot()):  # type: ignore
            layer_data = node.callDecoration("getLayerData")
            if not layer_data:
                continue
            return layer_data.getLayer(self.getCurrentLayer())
        return None

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
        self.calculateColorSchemeLimits()
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

    def beginRendering(self) -> None:
        scene = self.getController().getScene()
        renderer = self.getRenderer()
        if renderer is None:
            return

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
        """
        Set the upper end of the range of visible layers.

        If setting it below the lower end of the range, the lower end is lowered so that 1 layer stays visible.
        :param value: The new layer number to show, 0-indexed.
        """
        if self._current_layer_num != value:
            self._current_layer_num = min(max(value, 0), self._max_layers)
            self._minimum_layer_num = min(self._current_layer_num, self._minimum_layer_num)

            self._startUpdateTopLayers()
            self.currentLayerNumChanged.emit()

    def setMinimumLayer(self, value: int) -> None:
        """
        Set the lower end of the range of visible layers.

        If setting it above the upper end of the range, the upper end is increased so that 1 layer stays visible.
        :param value: The new lower end of the range of visible layers, 0-indexed.
        """
        if self._minimum_layer_num != value:
            self._minimum_layer_num = min(max(value, 0), self._max_layers)
            self._current_layer_num = max(self._current_layer_num, self._minimum_layer_num)

            self._startUpdateTopLayers()
            self.currentLayerNumChanged.emit()

    def setPath(self, value: float) -> None:
        """
        Set the upper end of the range of visible paths on the current layer.

        If setting it below the lower end of the range, the lower end is lowered so that 1 path stays visible.
        :param value: The new path index to show, 0-indexed.
        """
        if self._current_path_num != value:
            self._current_path_num = min(max(value, 0), self._max_paths)
            self._minimum_path_num = min(self._minimum_path_num, self._current_path_num)
            # update _current time when the path is changed by user
            if self._current_path_num < self._max_paths and round(self._current_path_num)== self._current_path_num:
                actual_path_num = int(self._current_path_num)
                cumulative_line_duration = self.cumulativeLineDuration()
                if actual_path_num < len(cumulative_line_duration):
                    self._current_time = cumulative_line_duration[actual_path_num]

            self._startUpdateTopLayers()
            self.currentPathNumChanged.emit()

    def setMinimumPath(self, value: int) -> None:
        """
        Set the lower end of the range of visible paths on the current layer.

        If setting it above the upper end of the range, the upper end is increased so that 1 path stays visible.
        :param value: The new lower end of the range of visible paths, 0-indexed.
        """
        if self._minimum_path_num != value:
            self._minimum_path_num = min(max(value, 0), self._max_paths)
            self._current_path_num = max(self._current_path_num, self._minimum_path_num)

            self._startUpdateTopLayers()
            self.currentPathNumChanged.emit()

    def setSimulationViewType(self, layer_view_type: int) -> None:
        """Set the layer view type

        :param layer_view_type: integer as in SimulationView.qml and this class
        """

        if layer_view_type != self._layer_view_type:
            self._layer_view_type = layer_view_type
            self.currentLayerNumChanged.emit()

    def getSimulationViewType(self) -> int:
        """Return the layer view type, integer as in SimulationView.qml and this class"""

        return self._layer_view_type

    def setExtruderOpacity(self, extruder_nr: int, opacity: float) -> None:
        """Set the extruder opacity

        :param extruder_nr: 0..15
        :param opacity: 0.0 .. 1.0
        """

        if 0 <= extruder_nr <= 15:
            self._extruder_opacity[extruder_nr // 4][extruder_nr % 4] = opacity
            self.currentLayerNumChanged.emit()

    def getExtruderOpacities(self) -> Matrix:
        # NOTE: Extruder opacities are stored in a matrix for (minor) performance reasons (w.r.t. OpenGL/shaders).
        # If more than 16 extruders are called for, this should be converted to a sampler1d.
        return Matrix(self._extruder_opacity)

    def setShowTravelMoves(self, show: bool) -> None:
        if show == self._show_travel_moves:
            return
        self._show_travel_moves = show
        self.currentLayerNumChanged.emit()
        self.visibleStructuresChanged.emit()

    def getShowTravelMoves(self) -> bool:
        return self._show_travel_moves

    def setShowHelpers(self, show: bool) -> None:
        if show == self._show_helpers:
            return
        self._show_helpers = show
        self.currentLayerNumChanged.emit()
        self.visibleStructuresChanged.emit()

    def getShowHelpers(self) -> bool:
        return self._show_helpers

    def setShowSkin(self, show: bool) -> None:
        if show == self._show_skin:
            return
        self._show_skin = show
        self.currentLayerNumChanged.emit()
        self.visibleStructuresChanged.emit()

    def getShowSkin(self) -> bool:
        return self._show_skin

    def setShowInfill(self, show: bool) -> None:
        if show == self._show_infill:
            return
        self._show_infill = show
        self.currentLayerNumChanged.emit()
        self.visibleStructuresChanged.emit()

    def getShowInfill(self) -> bool:
        return self._show_infill

    def setShowStarts(self, show: bool) -> None:
        if show == self._show_starts:
            return
        self._show_starts = show
        self.currentLayerNumChanged.emit()
        self.visibleStructuresChanged.emit()

    def getShowStarts(self) -> bool:
        return self._show_starts

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

    def getMaxLineWidth(self) -> float:
        return self._max_line_width

    def getMinLineWidth(self) -> float:
        if abs(self._min_line_width - sys.float_info.max) < 10:  # Some lenience due to floating point rounding.
            return 0.0  # If it's still max-float, there are no measurements. Use 0 then.
        return self._min_line_width

    def getMaxFlowRate(self) -> float:
        return self._max_flow_rate

    def getMinFlowRate(self) -> float:
        if abs(self._min_flow_rate - sys.float_info.max) < 10:  # Some lenience due to floating point rounding.
            return 0.0  # If it's still max-float, there are no measurements. Use 0 then.
        return self._min_flow_rate

    def calculateMaxLayers(self) -> None:
        """
        Calculates number of layers, triggers signals if the number of layers changed and makes sure the top layers are
        recalculated for legacy layer view.
        """
        scene = self.getController().getScene()

        self._old_max_layers = self._max_layers
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

    def calculateColorSchemeLimits(self) -> None:
        """
        Calculates the limits of the colour schemes, depending on the layer view data that is visible to the user.
        """
        # Before we start, save the old values so that we can tell if any of the spectrums need to change.
        old_min_feedrate = self._min_feedrate
        old_max_feedrate = self._max_feedrate
        old_min_linewidth = self._min_line_width
        old_max_linewidth = self._max_line_width
        old_min_thickness = self._min_thickness
        old_max_thickness = self._max_thickness
        old_min_flow_rate = self._min_flow_rate
        old_max_flow_rate = self._max_flow_rate

        self._min_feedrate = sys.float_info.max
        self._max_feedrate = sys.float_info.min
        self._min_line_width = sys.float_info.max
        self._max_line_width = sys.float_info.min
        self._min_thickness = sys.float_info.max
        self._max_thickness = sys.float_info.min
        self._min_flow_rate = sys.float_info.max
        self._max_flow_rate = sys.float_info.min
        self._cumulative_line_duration = {}

        # The colour scheme is only influenced by the visible lines, so filter the lines by if they should be visible.
        visible_line_types = []
        if self.getShowSkin():  # Actually "shell".
            visible_line_types.append(LayerPolygon.SkinType)
            visible_line_types.append(LayerPolygon.Inset0Type)
            visible_line_types.append(LayerPolygon.InsetXType)
        if self.getShowInfill():
            visible_line_types.append(LayerPolygon.InfillType)
        if self.getShowHelpers():
            visible_line_types.append(LayerPolygon.PrimeTowerType)
            visible_line_types.append(LayerPolygon.SkirtType)
            visible_line_types.append(LayerPolygon.SupportType)
            visible_line_types.append(LayerPolygon.SupportInfillType)
            visible_line_types.append(LayerPolygon.SupportInterfaceType)
        visible_line_types_with_extrusion = visible_line_types.copy()  # Copy before travel moves are added
        if self.getShowTravelMoves():
            visible_line_types.append(LayerPolygon.MoveCombingType)
            visible_line_types.append(LayerPolygon.MoveRetractionType)

        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            layer_data = node.callDecoration("getLayerData")
            if not layer_data:
                continue

            for layer_index in layer_data.getLayers():
                for polyline in layer_data.getLayer(layer_index).polygons:
                    is_visible = numpy.isin(polyline.types, visible_line_types)
                    visible_indices = numpy.where(is_visible)[0]
                    visible_indicies_with_extrusion = numpy.where(numpy.isin(polyline.types, visible_line_types_with_extrusion))[0]
                    if visible_indices.size == 0:  # No items to take maximum or minimum of.
                        continue
                    visible_feedrates = numpy.take(polyline.lineFeedrates, visible_indices)
                    visible_feedrates_with_extrusion = numpy.take(polyline.lineFeedrates, visible_indicies_with_extrusion)
                    visible_linewidths = numpy.take(polyline.lineWidths, visible_indices)
                    visible_linewidths_with_extrusion = numpy.take(polyline.lineWidths, visible_indicies_with_extrusion)
                    visible_thicknesses = numpy.take(polyline.lineThicknesses, visible_indices)
                    visible_thicknesses_with_extrusion = numpy.take(polyline.lineThicknesses, visible_indicies_with_extrusion)
                    self._max_feedrate = max(float(visible_feedrates.max()), self._max_feedrate)
                    if visible_feedrates_with_extrusion.size != 0:
                        flow_rates = visible_feedrates_with_extrusion * visible_linewidths_with_extrusion * visible_thicknesses_with_extrusion
                        self._min_flow_rate = min(float(flow_rates.min()), self._min_flow_rate)
                        self._max_flow_rate = max(float(flow_rates.max()), self._max_flow_rate)
                    self._min_feedrate = min(float(visible_feedrates.min()), self._min_feedrate)
                    self._max_line_width = max(float(visible_linewidths.max()), self._max_line_width)
                    self._min_line_width = min(float(visible_linewidths.min()), self._min_line_width)
                    self._max_thickness = max(float(visible_thicknesses.max()), self._max_thickness)
                    try:
                        self._min_thickness = min(float(visible_thicknesses[numpy.nonzero(visible_thicknesses)].min()), self._min_thickness)
                    except ValueError:
                        # Sometimes, when importing a GCode the line thicknesses are zero and so the minimum (avoiding the zero) can't be calculated.
                        Logger.log("w", "Min thickness can't be calculated because all the values are zero")

        if old_min_feedrate != self._min_feedrate or old_max_feedrate != self._max_feedrate \
                or old_min_linewidth != self._min_line_width or old_max_linewidth != self._max_line_width \
                or old_min_thickness != self._min_thickness or old_max_thickness != self._max_thickness \
                or old_min_flow_rate != self._min_flow_rate or old_max_flow_rate != self._max_flow_rate:
            self.colorSchemeLimitsChanged.emit()

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
    visibleStructuresChanged = Signal()
    colorSchemeLimitsChanged = Signal()

    def getProxy(self, engine, script_engine):
        """Hackish way to ensure the proxy is already created

        which ensures that the layerview.qml is already created as this caused some issues.
        """
        if self._proxy is None:
            self._proxy = SimulationViewProxy(self)
        return self._proxy

    def endRendering(self) -> None:
        pass

    def event(self, event) -> bool:
        modifiers = QApplication.keyboardModifiers()
        ctrl_is_active = modifiers & Qt.KeyboardModifier.ControlModifier
        shift_is_active = modifiers & Qt.KeyboardModifier.ShiftModifier
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

            self.calculateColorSchemeLimits()
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
            renderer = self.getRenderer()
            if renderer is None:
                return False

            renderer.addRenderPass(layer_pass)

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
                self._composite_pass = cast(CompositePass, renderer.getRenderPass("composite"))

            self._old_layer_bindings = self._composite_pass.getLayerBindings()[:]  # make a copy so we can restore to it later
            self._composite_pass.getLayerBindings().append("simulationview")
            self._old_composite_shader = self._composite_pass.getCompositeShader()
            self._composite_pass.setCompositeShader(self._simulationview_composite_shader)
            self._updateSliceWarningVisibility()

        elif event.type == Event.ViewDeactivateEvent:
            self._controller.getScene().getRoot().childrenChanged.disconnect(self._onSceneChanged)
            Application.getInstance().getPreferences().preferenceChanged.disconnect(self._onPreferencesChanged)
            self._slice_first_warning_message.hide()
            Application.getInstance().globalContainerStackChanged.disconnect(self._onGlobalStackChanged)
            if self._nozzle_node:
                self._nozzle_node.setParent(None)

            renderer = self.getRenderer()
            if renderer is None:
                return False

            if self._layer_pass is not None:
                renderer.removeRenderPass(self._layer_pass)
            if self._composite_pass:
                self._composite_pass.setLayerBindings(cast(List[str], self._old_layer_bindings))
                self._composite_pass.setCompositeShader(cast(ShaderProgram, self._old_composite_shader))

        return False

    def getCurrentLayerMesh(self):
        return self._current_layer_mesh

    def getCurrentLayerJumps(self):
        return self._current_layer_jumps

    def _onGlobalStackChanged(self) -> None:
        self._global_container_stack = Application.getInstance().getGlobalContainerStack()
        if self._global_container_stack:
            self._extruder_count = self._global_container_stack.getProperty("machine_extruder_count", "value")
            self.globalStackChanged.emit()

    def _onCurrentLayerNumChanged(self) -> None:
        self.calculateMaxPathsOnLayer(self._current_layer_num)
        scene = Application.getInstance().getController().getScene()
        scene.sceneChanged.emit(scene.getRoot())

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
        self.setShowStarts(bool(Application.getInstance().getPreferences().getValue("layerview/show_starts")))

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
            "layerview/show_starts",
            }:
            return

        self._updateWithPreferences()

    def _updateSliceWarningVisibility(self):
        if not self.getActivity()\
                and not CuraApplication.getInstance().getPreferences().getValue("general/auto_slice")\
                and CuraApplication.getInstance().getPreferences().getValue(self._no_layers_warning_preference):
            self._slice_first_warning_message.show()
        else:
            self._slice_first_warning_message.hide()

    def _onDontAskMeAgain(self, checked: bool) -> None:
        CuraApplication.getInstance().getPreferences().setValue(self._no_layers_warning_preference, not checked)

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
