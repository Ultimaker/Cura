# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty
from UM.FlameProfiler import pyqtSlot
from UM.Application import Application

if TYPE_CHECKING:
    from .SimulationView import SimulationView


class SimulationViewProxy(QObject):
    def __init__(self, simulation_view: "SimulationView", parent=None) -> None:
        super().__init__(parent)
        self._simulation_view = simulation_view
        self._current_layer = 0
        self._controller = Application.getInstance().getController()
        self._controller.activeViewChanged.connect(self._onActiveViewChanged)
        self.is_simulationView_selected = False
        self._onActiveViewChanged()

    currentLayerChanged = pyqtSignal()
    currentPathChanged = pyqtSignal()
    maxLayersChanged = pyqtSignal()
    maxPathsChanged = pyqtSignal()
    activityChanged = pyqtSignal()
    globalStackChanged = pyqtSignal()
    preferencesChanged = pyqtSignal()
    busyChanged = pyqtSignal()
    colorSchemeLimitsChanged = pyqtSignal()

    @pyqtProperty(bool, notify=activityChanged)
    def layerActivity(self):
        return self._simulation_view.getActivity()

    @pyqtProperty(int, notify=maxLayersChanged)
    def numLayers(self):
        return self._simulation_view.getMaxLayers()

    @pyqtProperty(int, notify=currentLayerChanged)
    def currentLayer(self):
        return self._simulation_view.getCurrentLayer()

    @pyqtProperty(int, notify=currentLayerChanged)
    def minimumLayer(self):
        return self._simulation_view.getMinimumLayer()

    @pyqtProperty(int, notify=maxPathsChanged)
    def numPaths(self):
        return self._simulation_view.getMaxPaths()

    @pyqtProperty(float, notify=currentPathChanged)
    def currentPath(self):
        return self._simulation_view.getCurrentPath()

    @pyqtSlot(float, result=bool)
    def advanceTime(self, duration: float) -> bool:
        return self._simulation_view.advanceTime(duration)

    @pyqtProperty(int, notify=currentPathChanged)
    def minimumPath(self):
        return self._simulation_view.getMinimumPath()

    @pyqtProperty(bool, notify=busyChanged)
    def busy(self):
        return self._simulation_view.isBusy()

    @pyqtProperty(bool, notify=preferencesChanged)
    def compatibilityMode(self):
        return self._simulation_view.getCompatibilityMode()

    @pyqtProperty(int, notify=globalStackChanged)
    def extruderCount(self):
        return self._simulation_view.getExtruderCount()

    @pyqtSlot(int)
    def setCurrentLayer(self, layer_num):
        self._simulation_view.setLayer(layer_num)

    @pyqtSlot(int)
    def setMinimumLayer(self, layer_num):
        self._simulation_view.setMinimumLayer(layer_num)

    @pyqtSlot(float)
    def setCurrentPath(self, path_num: float):
        self._simulation_view.setPath(path_num)

    @pyqtSlot(int)
    def setMinimumPath(self, path_num):
        self._simulation_view.setMinimumPath(path_num)

    @pyqtSlot(int)
    def setSimulationViewType(self, layer_view_type):
        self._simulation_view.setSimulationViewType(layer_view_type)

    @pyqtSlot(result=int)
    def getSimulationViewType(self):
        return self._simulation_view.getSimulationViewType()

    @pyqtSlot(bool)
    def setSimulationRunning(self, running):
        self._simulation_view.setSimulationRunning(running)

    @pyqtSlot(result=bool)
    def getSimulationRunning(self):
        return self._simulation_view.isSimulationRunning()

    @pyqtProperty(float, notify = colorSchemeLimitsChanged)
    def minFeedrate(self):
        return self._simulation_view.getMinFeedrate()

    @pyqtProperty(float, notify = colorSchemeLimitsChanged)
    def maxFeedrate(self):
        return self._simulation_view.getMaxFeedrate()

    @pyqtProperty(float, notify = colorSchemeLimitsChanged)
    def minThickness(self):
        return self._simulation_view.getMinThickness()

    @pyqtProperty(float, notify = colorSchemeLimitsChanged)
    def maxThickness(self):
        return self._simulation_view.getMaxThickness()

    @pyqtProperty(float, notify = colorSchemeLimitsChanged)
    def maxLineWidth(self):
        return self._simulation_view.getMaxLineWidth()

    @pyqtProperty(float, notify = colorSchemeLimitsChanged)
    def minLineWidth(self):
        return self._simulation_view.getMinLineWidth()

    @pyqtProperty(float, notify=colorSchemeLimitsChanged)
    def maxFlowRate(self):
        return self._simulation_view.getMaxFlowRate()

    @pyqtProperty(float, notify=colorSchemeLimitsChanged)
    def minFlowRate(self):
        return self._simulation_view.getMinFlowRate()

    # Opacity 0..1
    @pyqtSlot(int, float)
    def setExtruderOpacity(self, extruder_nr, opacity):
        self._simulation_view.setExtruderOpacity(extruder_nr, opacity)

    @pyqtSlot(int)
    def setShowTravelMoves(self, show):
        self._simulation_view.setShowTravelMoves(show)

    @pyqtSlot(int)
    def setShowHelpers(self, show):
        self._simulation_view.setShowHelpers(show)

    @pyqtSlot(int)
    def setShowSkin(self, show):
        self._simulation_view.setShowSkin(show)

    @pyqtSlot(int)
    def setShowInfill(self, show):
        self._simulation_view.setShowInfill(show)

    def _layerActivityChanged(self):
        self.activityChanged.emit()

    def _onLayerChanged(self):
        self.currentLayerChanged.emit()
        self._layerActivityChanged()

    def _onColorSchemeLimitsChanged(self):
        self.colorSchemeLimitsChanged.emit()

    def _onPathChanged(self):
        self.currentPathChanged.emit()
        self._layerActivityChanged()

        scene = Application.getInstance().getController().getScene()
        scene.sceneChanged.emit(scene.getRoot())

    def _onMaxLayersChanged(self):
        self.maxLayersChanged.emit()

    def _onMaxPathsChanged(self):
        self.maxPathsChanged.emit()

    def _onBusyChanged(self):
        self.busyChanged.emit()

    def _onActivityChanged(self):
        self.activityChanged.emit()

    def _onGlobalStackChanged(self):
        self.globalStackChanged.emit()

    def _onPreferencesChanged(self):
        self.preferencesChanged.emit()

    def _onActiveViewChanged(self):
        active_view = self._controller.getActiveView()
        if active_view == self._simulation_view:
            self._simulation_view.currentLayerNumChanged.connect(self._onLayerChanged)
            self._simulation_view.colorSchemeLimitsChanged.connect(self._onColorSchemeLimitsChanged)
            self._simulation_view.currentPathNumChanged.connect(self._onPathChanged)
            self._simulation_view.maxLayersChanged.connect(self._onMaxLayersChanged)
            self._simulation_view.maxPathsChanged.connect(self._onMaxPathsChanged)
            self._simulation_view.busyChanged.connect(self._onBusyChanged)
            self._simulation_view.activityChanged.connect(self._onActivityChanged)
            self._simulation_view.globalStackChanged.connect(self._onGlobalStackChanged)
            self._simulation_view.preferencesChanged.connect(self._onPreferencesChanged)
            self.is_simulationView_selected = True
        elif self.is_simulationView_selected:
            # Disconnect all of em again.
            self.is_simulationView_selected = False
            self._simulation_view.currentLayerNumChanged.disconnect(self._onLayerChanged)
            self._simulation_view.colorSchemeLimitsChanged.connect(self._onColorSchemeLimitsChanged)
            self._simulation_view.currentPathNumChanged.disconnect(self._onPathChanged)
            self._simulation_view.maxLayersChanged.disconnect(self._onMaxLayersChanged)
            self._simulation_view.maxPathsChanged.disconnect(self._onMaxPathsChanged)
            self._simulation_view.busyChanged.disconnect(self._onBusyChanged)
            self._simulation_view.activityChanged.disconnect(self._onActivityChanged)
            self._simulation_view.globalStackChanged.disconnect(self._onGlobalStackChanged)
            self._simulation_view.preferencesChanged.disconnect(self._onPreferencesChanged)
