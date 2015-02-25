from UM.Qt.QtApplication import QtApplication
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Camera import Camera
from UM.Scene.Platform import Platform
from UM.Math.Vector import Vector
from UM.Math.Matrix import Matrix
from UM.Resources import Resources

from UM.Scene.BoxRenderer import BoxRenderer
from UM.Scene.Selection import Selection

from PlatformPhysics import PlatformPhysics
from BuildVolume import BuildVolume

from PyQt5.QtCore import pyqtSlot, QUrl, Qt
from PyQt5.QtGui import QColor

import os.path

class PrinterApplication(QtApplication):
    def __init__(self):
        super().__init__(name = 'cura')
        self.setRequiredPlugins(['CuraEngineBackend', 'MeshView', 'LayerView', 'STLReader','SelectionTool','CameraTool'])
        self._physics = None
        self._volume = None
        self.activeMachineChanged.connect(self._onActiveMachineChanged)
    
    def _loadPlugins(self):
        self._plugin_registry.loadPlugins({ "type": "Logger"})
        self._plugin_registry.loadPlugins({ "type": "StorageDevice" })
        self._plugin_registry.loadPlugins({ "type": "View" })
        self._plugin_registry.loadPlugins({ "type": "MeshHandler" })
        self._plugin_registry.loadPlugins({ "type": "Tool" })

        self._plugin_registry.loadPlugin('CuraEngineBackend')
    
    def run(self):
        self.showSplashMessage('Setting up scene...')

        controller = self.getController()

        controller.setActiveView("MeshView")
        controller.setCameraTool("CameraTool")
        controller.setSelectionTool("SelectionTool")

        t = controller.getTool('TranslateTool')
        if t:
            t.setYRange(0.0, 0.0)

        Selection.selectionChanged.connect(self.onSelectionChanged)

        self._physics = PlatformPhysics(controller)

        root = controller.getScene().getRoot()
        platform = Platform(root)

        self._volume = BuildVolume(root)

        self.getRenderer().setLightPosition(Vector(0, 150, 0))
        self.getRenderer().setBackgroundColor(QColor(200, 200, 200))

        camera = Camera('3d', root)
        camera.translate(Vector(-150, 150, 300))
        camera.setPerspective(True)
        camera.lookAt(Vector(0, 0, 0), Vector(0, 1, 0))

        controller.getScene().setActiveCamera('3d')

        self.setActiveMachine(self.getMachines()[0])

        self.showSplashMessage('Loading interface...')

        self.setMainQml(os.path.dirname(__file__) + "/Printer.qml")
        self.initializeEngine()
        
        if self._engine.rootObjects:
            self.closeSplash()
            self.exec_()

        self.saveMachines()

    def registerObjects(self, engine):
        engine.rootContext().setContextProperty('Printer', self)

    def onSelectionChanged(self):
        if Selection.hasSelection():
            if not self.getController().getActiveTool():
                self.getController().setActiveTool('TranslateTool')

            self.getController().getTool('CameraTool').setOrigin(Selection.getSelectedObject(0).getGlobalPosition())
        else:
            if self.getController().getActiveTool():
                self.getController().setActiveTool(None)

    @pyqtSlot(QUrl)
    def saveGCode(self, file):
        try:
            gcode = self.getController().getScene().gcode
        except AttributeError:
            return

        with open(file.toLocalFile(), 'w') as f:
            f.write(gcode)

    def _onActiveMachineChanged(self):
        machine = self.getActiveMachine()
        if machine:
            self._volume.setWidth(machine.getSettingValueByKey('machine_width'))
            self._volume.setHeight(machine.getSettingValueByKey('machine_height'))
            self._volume.setDepth(machine.getSettingValueByKey('machine_depth'))
            self._volume.rebuild()
