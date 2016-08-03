from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, pyqtProperty
from UM.Application import Application

import LayerView

class LayerViewProxy(QObject):
    def __init__(self, parent = None):
        super().__init__(parent)
        self._current_layer = 0
        self._controller = Application.getInstance().getController()
        self._controller.activeViewChanged.connect(self._onActiveViewChanged)
        self._onActiveViewChanged()
    
    currentLayerChanged = pyqtSignal()
    maxLayersChanged = pyqtSignal()
    activityChanged = pyqtSignal()

    @pyqtProperty(bool, notify = activityChanged)
    def getLayerActivity(self):
        active_view = self._controller.getActiveView()
        if type(active_view) == LayerView.LayerView.LayerView:
            return active_view.getLayerPass().getActivity()

    @pyqtProperty(int, notify = maxLayersChanged)
    def numLayers(self):
        active_view = self._controller.getActiveView()
        if type(active_view) == LayerView.LayerView.LayerView:
            return active_view.getLayerPass().getMaxLayers()
        #return 100
    
    @pyqtProperty(int, notify = currentLayerChanged)
    def currentLayer(self):
        active_view = self._controller.getActiveView()
        if type(active_view) == LayerView.LayerView.LayerView:
            return active_view.getLayerPass().getCurrentLayer()

    busyChanged = pyqtSignal()
    @pyqtProperty(bool, notify = busyChanged)
    def busy(self):
        active_view = self._controller.getActiveView()
        if type(active_view) == LayerView.LayerView.LayerView:
            return active_view.isBusy()

        return False
    
    @pyqtSlot(int)
    def setCurrentLayer(self, layer_num):
        active_view = self._controller.getActiveView()
        if type(active_view) == LayerView.LayerView.LayerView:
            active_view.getLayerPass().setLayer(layer_num)

    def _layerActivityChanged(self):
        self.activityChanged.emit()
            
    def _onLayerChanged(self):
        self.currentLayerChanged.emit()
        self._layerActivityChanged()
        
    def _onMaxLayersChanged(self):
        self.maxLayersChanged.emit()

    def _onBusyChanged(self):
        self.busyChanged.emit()
        
    def _onActiveViewChanged(self):
        active_view = self._controller.getActiveView()
        if type(active_view) == LayerView.LayerView.LayerView:
            active_view.getLayerPass().currentLayerNumChanged.connect(self._onLayerChanged)
            active_view.getLayerPass().maxLayersChanged.connect(self._onMaxLayersChanged)
            active_view.busyChanged.connect(self._onBusyChanged)
