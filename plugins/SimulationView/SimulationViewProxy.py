# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QObject, pyqtSignal, pyqtProperty
from UM.FlameProfiler import pyqtSlot
from UM.Application import Application

import SimulationView


class SimulationViewProxy(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_layer = 0
        self._controller = Application.getInstance().getController()
        self._controller.activeViewChanged.connect(self._onActiveViewChanged)
        self._onActiveViewChanged()
        self.is_simulationView_selected = False

    currentLayerChanged = pyqtSignal()
    currentPathChanged = pyqtSignal()
    maxLayersChanged = pyqtSignal()
    maxPathsChanged = pyqtSignal()
    activityChanged = pyqtSignal()
    globalStackChanged = pyqtSignal()
    preferencesChanged = pyqtSignal()
    busyChanged = pyqtSignal()

    @pyqtProperty(bool, notify=activityChanged)
    def layerActivity(self):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            return active_view.getActivity()
        return False

    @pyqtProperty(int, notify=maxLayersChanged)
    def numLayers(self):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            return active_view.getMaxLayers()
        return 0

    @pyqtProperty(int, notify=currentLayerChanged)
    def currentLayer(self):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            return active_view.getCurrentLayer()
        return 0

    @pyqtProperty(int, notify=currentLayerChanged)
    def minimumLayer(self):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            return active_view.getMinimumLayer()
        return 0

    @pyqtProperty(int, notify=maxPathsChanged)
    def numPaths(self):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            return active_view.getMaxPaths()
        return 0

    @pyqtProperty(int, notify=currentPathChanged)
    def currentPath(self):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            return active_view.getCurrentPath()
        return 0

    @pyqtProperty(int, notify=currentPathChanged)
    def minimumPath(self):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            return active_view.getMinimumPath()
        return 0

    @pyqtProperty(bool, notify=busyChanged)
    def busy(self):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            return active_view.isBusy()
        return False

    @pyqtProperty(bool, notify=preferencesChanged)
    def compatibilityMode(self):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            return active_view.getCompatibilityMode()
        return False

    @pyqtSlot(int)
    def setCurrentLayer(self, layer_num):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            active_view.setLayer(layer_num)

    @pyqtSlot(int)
    def setMinimumLayer(self, layer_num):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            active_view.setMinimumLayer(layer_num)

    @pyqtSlot(int)
    def setCurrentPath(self, path_num):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            active_view.setPath(path_num)

    @pyqtSlot(int)
    def setMinimumPath(self, path_num):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            active_view.setMinimumPath(path_num)

    @pyqtSlot(int)
    def setSimulationViewType(self, layer_view_type):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            active_view.setSimulationViewType(layer_view_type)

    @pyqtSlot(result=int)
    def getSimulationViewType(self):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            return active_view.getSimulationViewType()
        return 0

    @pyqtSlot(bool)
    def setSimulationRunning(self, running):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            active_view.setSimulationRunning(running)

    @pyqtSlot(result=bool)
    def getSimulationRunning(self):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            return active_view.isSimulationRunning()
        return False

    @pyqtSlot(result=float)
    def getMinFeedrate(self):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            return active_view.getMinFeedrate()
        return 0

    @pyqtSlot(result=float)
    def getMaxFeedrate(self):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            return active_view.getMaxFeedrate()
        return 0

    @pyqtSlot(result=float)
    def getMinThickness(self):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            return active_view.getMinThickness()
        return 0

    @pyqtSlot(result=float)
    def getMaxThickness(self):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            return active_view.getMaxThickness()
        return 0

    # Opacity 0..1
    @pyqtSlot(int, float)
    def setExtruderOpacity(self, extruder_nr, opacity):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            active_view.setExtruderOpacity(extruder_nr, opacity)

    @pyqtSlot(int)
    def setShowTravelMoves(self, show):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            active_view.setShowTravelMoves(show)

    @pyqtSlot(int)
    def setShowHelpers(self, show):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            active_view.setShowHelpers(show)

    @pyqtSlot(int)
    def setShowSkin(self, show):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            active_view.setShowSkin(show)

    @pyqtSlot(int)
    def setShowInfill(self, show):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            active_view.setShowInfill(show)

    @pyqtProperty(int, notify=globalStackChanged)
    def extruderCount(self):
        active_view = self._controller.getActiveView()
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            return active_view.getExtruderCount()
        return 0

    def _layerActivityChanged(self):
        self.activityChanged.emit()

    def _onLayerChanged(self):
        self.currentLayerChanged.emit()
        self._layerActivityChanged()

    def _onPathChanged(self):
        self.currentPathChanged.emit()
        self._layerActivityChanged()

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
        if isinstance(active_view, SimulationView.SimulationView.SimulationView):
            # remove other connection if once the SimulationView was created.
            if self.is_simulationView_selected:
                active_view.currentLayerNumChanged.disconnect(self._onLayerChanged)
                active_view.currentPathNumChanged.disconnect(self._onPathChanged)
                active_view.maxLayersChanged.disconnect(self._onMaxLayersChanged)
                active_view.maxPathsChanged.disconnect(self._onMaxPathsChanged)
                active_view.busyChanged.disconnect(self._onBusyChanged)
                active_view.activityChanged.disconnect(self._onActivityChanged)
                active_view.globalStackChanged.disconnect(self._onGlobalStackChanged)
                active_view.preferencesChanged.disconnect(self._onPreferencesChanged)

            self.is_simulationView_selected = True
            active_view.currentLayerNumChanged.connect(self._onLayerChanged)
            active_view.currentPathNumChanged.connect(self._onPathChanged)
            active_view.maxLayersChanged.connect(self._onMaxLayersChanged)
            active_view.maxPathsChanged.connect(self._onMaxPathsChanged)
            active_view.busyChanged.connect(self._onBusyChanged)
            active_view.activityChanged.connect(self._onActivityChanged)
            active_view.globalStackChanged.connect(self._onGlobalStackChanged)
            active_view.preferencesChanged.connect(self._onPreferencesChanged)
