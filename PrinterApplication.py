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

from PyQt5.QtCore import pyqtSlot, QUrl

import os.path

class PrinterApplication(QtApplication):
    def __init__(self):
        super().__init__()
        self.setApplicationName('printer')
        self._machine_settings.loadSettingsFromFile(Resources.getPath(Resources.SettingsLocation, "ultimaker2.json"))
        self._physics = None
    
    def _loadPlugins(self):
        self._plugin_registry.loadPlugins({ "type": "Logger"})
        self._plugin_registry.loadPlugins({ "type": "StorageDevice" })
        self._plugin_registry.loadPlugins({ "type": "View" })
        self._plugin_registry.loadPlugins({ "type": "MeshHandler" })
        self._plugin_registry.loadPlugins({ "type": "Tool" })

        self._plugin_registry.loadPlugin('CuraEngineBackend')
    
    def run(self):
        
        
        controller = self.getController()

        controller.setActiveView("MeshView")
        controller.setCameraTool("CameraTool")
        controller.setSelectionTool("SelectionTool")

        t = controller.getTool('TranslateTool')
        if t:
            t.setYRange(0.0, 0.0)

        Selection.selectionChanged.connect(self.onSelectionChanged)

        self._physics = PlatformPhysics(controller)

        try:
            self.getMachineSettings().loadValuesFromFile(Resources.getPath(Resources.SettingsLocation, 'ultimaker2.cfg'))
        except FileNotFoundError:
            pass

        root = controller.getScene().getRoot()
        platform = Platform(root)

        volume = BuildVolume(root)
        volume.translate(Vector(0, 73, 0))
        volume.scale(150.0)

        self.getRenderer().setLightPosition(Vector(0, 150, 0))

        camera = Camera('3d', root)
        camera.translate(Vector(0, 150, 150))
        proj = Matrix()
        proj.setPerspective(45, 640/480, 1, 500)
        camera.setProjectionMatrix(proj)
        camera.setPerspective(True)
        camera.lookAt(Vector(0, 0, 0), Vector(0, 1, 0))

        camera = Camera('left', root)
        camera.translate(Vector(-150, 50, 0))
        proj = Matrix()
        proj.setOrtho(-200, 200, -200, 200, 1, 500)
        camera.setProjectionMatrix(proj)
        camera.lookAt(Vector(0, 50, 0), Vector(0, 1, 0))
        camera.setLocked(True)

        camera = Camera('top', root)
        camera.translate(Vector(0, 150, 0))
        proj = Matrix()
        proj.setOrtho(-200, 200, -200, 200, 1, 500)
        camera.setProjectionMatrix(proj)
        camera.lookAt(Vector(0, 0, 0), Vector(0, 0, -1))
        camera.setLocked(True)

        camera = Camera('front', root)
        camera.translate(Vector(0, 50, 150))
        proj = Matrix()
        proj.setOrtho(-200, 200, -200, 200, 1, 500)
        camera.setProjectionMatrix(proj)
        camera.lookAt(Vector(0, 50, 0), Vector(0, 1, 0))
        camera.setLocked(True)

        controller.getScene().setActiveCamera('3d')

        self.setMainQml(os.path.dirname(__file__) + "/Printer.qml")
        self.initializeEngine()
        
        if self._engine.rootObjects:
            self.exec_()

        self.getMachineSettings().saveValuesToFile(Resources.getStoragePath(Resources.SettingsLocation, 'ultimaker2.cfg'))

    def registerObjects(self, engine):
        engine.rootContext().setContextProperty('Printer', self)

    def onSelectionChanged(self):
        if Selection.getCount() > 0:
            if not self.getController().getActiveTool():
                self.getController().setActiveTool('TranslateTool')

            self.getController().getTool('CameraTool').setOrigin(Selection.getSelectedObject(0).getGlobalPosition())
        else:
            if self.getController().getActiveTool() and self.getController().getActiveTool().getName() == 'TranslateTool':
                self.getController().setActiveTool(None)

    @pyqtSlot(QUrl)
    def saveGCode(self, file):
        try:
            gcode = self.getController().getScene().gcode
        except AttributeError:
            return

        with open(file.toLocalFile(), 'w') as f:
            f.write(gcode)
