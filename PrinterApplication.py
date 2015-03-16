from UM.Qt.QtApplication import QtApplication
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Camera import Camera
from UM.Scene.Platform import Platform
from UM.Math.Vector import Vector
from UM.Math.Matrix import Matrix
from UM.Resources import Resources
from UM.Scene.ToolHandle import ToolHandle
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Mesh.WriteMeshJob import WriteMeshJob

from UM.Scene.BoxRenderer import BoxRenderer
from UM.Scene.Selection import Selection

from PlatformPhysics import PlatformPhysics
from BuildVolume import BuildVolume
from CameraAnimation import CameraAnimation

from PyQt5.QtCore import pyqtSlot, QUrl, Qt, pyqtSignal, pyqtProperty
from PyQt5.QtGui import QColor

import os.path
import numpy
numpy.seterr(all='ignore')

class PrinterApplication(QtApplication):
    def __init__(self):
        super().__init__(name = 'cura')
        self.setRequiredPlugins([
            'CuraEngineBackend',
            'MeshView',
            'LayerView',
            'STLReader',
            'SelectionTool',
            'CameraTool',
            'GCodeWriter',
            'LocalFileStorage'
        ])
        self._physics = None
        self._volume = None
        self.activeMachineChanged.connect(self._onActiveMachineChanged)
    
    def _loadPlugins(self):
        self._plugin_registry.loadPlugins({ "type": "logger"})
        self._plugin_registry.loadPlugins({ "type": "storage_device" })
        self._plugin_registry.loadPlugins({ "type": "view" })
        self._plugin_registry.loadPlugins({ "type": "mesh_reader" })
        self._plugin_registry.loadPlugins({ "type": "mesh_writer" })
        self._plugin_registry.loadPlugins({ "type": "tool" })

        self._plugin_registry.loadPlugin('CuraEngineBackend')
    
    def run(self):
        self.showSplashMessage('Setting up scene...')

        controller = self.getController()

        controller.setActiveView("MeshView")
        controller.setCameraTool("CameraTool")
        controller.setSelectionTool("SelectionTool")

        t = controller.getTool('TranslateTool')
        if t:
            t.setEnabledAxis([ToolHandle.XAxis, ToolHandle.ZAxis])

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

        self._camera_animation = CameraAnimation()
        self._camera_animation.setCameraTool(self.getController().getTool('CameraTool'))

        controller.getScene().setActiveCamera('3d')

        self.showSplashMessage('Loading interface...')

        self.setMainQml(os.path.dirname(__file__) + "/Printer.qml")
        self.initializeEngine()

        self.getStorageDevice('LocalFileStorage').removableDrivesChanged.connect(self._removableDrivesChanged)

        #TODO: Add support for active machine preference
        if self.getMachines():
            self.setActiveMachine(self.getMachines()[0])
        else:
            self.requestAddPrinter.emit()

        if self._engine.rootObjects:
            self.closeSplash()

            self.exec_()

    def registerObjects(self, engine):
        engine.rootContext().setContextProperty('Printer', self)

    def onSelectionChanged(self):
        if Selection.hasSelection():
            if not self.getController().getActiveTool():
                self.getController().setActiveTool('TranslateTool')

            self._camera_animation.setStart(self.getController().getTool('CameraTool').getOrigin())
            self._camera_animation.setTarget(Selection.getSelectedObject(0).getGlobalPosition())
            self._camera_animation.start()
        else:
            if self.getController().getActiveTool():
                self.getController().setActiveTool(None)

    requestAddPrinter = pyqtSignal()

    def _onActiveMachineChanged(self):
        machine = self.getActiveMachine()
        if machine:
            self._volume.setWidth(machine.getSettingValueByKey('machine_width'))
            self._volume.setHeight(machine.getSettingValueByKey('machine_height'))
            self._volume.setDepth(machine.getSettingValueByKey('machine_depth'))
            self._volume.rebuild()

    removableDrivesChanged = pyqtSignal()

    @pyqtProperty("QStringList", notify = removableDrivesChanged)
    def removableDrives(self):
        return list(self.getStorageDevice('LocalFileStorage').getRemovableDrives().keys())

    @pyqtSlot()
    def saveToSD(self):
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if type(node) is not SceneNode or not node.getMeshData():
                continue

            drives = self.getStorageDevice('LocalFileStorage').getRemovableDrives()
            path = next(iter(drives.values()))
            filename = os.path.join(path, node.getName()[0:node.getName().rfind('.')] + '.gcode')

            job = WriteMeshJob(filename, node.getMeshData())
            job.start()
            return

    def _removableDrivesChanged(self):
        print(self.getStorageDevice('LocalFileStorage').getRemovableDrives())
        self.removableDrivesChanged.emit()
