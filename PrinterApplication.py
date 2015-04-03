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
from UM.Mesh.ReadMeshJob import ReadMeshJob

from UM.Scene.BoxRenderer import BoxRenderer
from UM.Scene.Selection import Selection

from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Operations.RemoveSceneNodeOperation import RemoveSceneNodeOperation
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.SetTransformOperation import SetTransformOperation

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
        self._platform = None
        self._output_source = 'local_file'
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
        self._platform = Platform(root)

        self._volume = BuildVolume(root)

        self.getRenderer().setLightPosition(Vector(0, 150, 0))
        self.getRenderer().setBackgroundColor(QColor(246, 246, 246))

        camera = Camera('3d', root)
        camera.translate(Vector(-150, 150, 300))
        camera.setPerspective(True)
        camera.lookAt(Vector(0, 0, 0), Vector(0, 1, 0))

        self._camera_animation = CameraAnimation()
        self._camera_animation.setCameraTool(self.getController().getTool('CameraTool'))

        controller.getScene().setActiveCamera('3d')

        self.showSplashMessage('Loading interface...')

        self.setMainQml(os.path.dirname(__file__), "qml/Printer.qml")
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

    @pyqtSlot('quint64')
    def deleteObject(self, object_id):
        object = self.getController().getScene().findObject(object_id)

        if object:
            op = RemoveSceneNodeOperation(object)
            op.push()

    @pyqtSlot('quint64', int)
    def multiplyObject(self, object_id, count):
        node = self.getController().getScene().findObject(object_id)

        if node:
            op = GroupedOperation()
            for i in range(count):
                new_node = SceneNode()
                new_node.setMeshData(node.getMeshData())
                new_node.setScale(node.getScale())
                new_node.translate(Vector((i + 1) * node.getBoundingBox().width, 0, 0))
                new_node.setSelectable(True)
                op.addOperation(AddSceneNodeOperation(new_node, node.getParent()))
            op.push()

    @pyqtSlot('quint64')
    def centerObject(self, object_id):
        node = self.getController().getScene().findObject(object_id)

        if node:
            transform = node.getLocalTransformation()
            transform.setTranslation(Vector(0, 0, 0))
            op = SetTransformOperation(node, transform)
            op.push()

    @pyqtSlot()
    def deleteAll(self):
        nodes = []
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if type(node) is not SceneNode or not node.getMeshData():
                continue
            nodes.append(node)

        if nodes:
            op = GroupedOperation()

            for node in nodes:
                op.addOperation(RemoveSceneNodeOperation(node))

            op.push()

    @pyqtSlot()
    def resetAllTranslation(self):
        nodes = []
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if type(node) is not SceneNode or not node.getMeshData():
                continue
            nodes.append(node)

        if nodes:
            op = GroupedOperation()

            for node in nodes:
                transform = node.getLocalTransformation()
                transform.setTranslation(Vector(0, 0, 0))
                op.addOperation(SetTransformOperation(node, transform))

            op.push()

    @pyqtSlot()
    def resetAll(self):
        nodes = []
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if type(node) is not SceneNode or not node.getMeshData():
                continue
            nodes.append(node)

        if nodes:
            op = GroupedOperation()

            for node in nodes:
                transform = Matrix()
                op.addOperation(SetTransformOperation(node, transform))

            op.push()

    @pyqtSlot()
    def reloadAll(self):
        nodes = []
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if type(node) is not SceneNode or not node.getMeshData():
                continue

            nodes.append(node)

        if nodes:
            file_name = node.getMeshData().getFileName()

            job = ReadMeshJob(file_name)
            job.finished.connect(lambda j: node.setMeshData(j.getResult()))
            job.start()

    def _onActiveMachineChanged(self):
        machine = self.getActiveMachine()
        if machine:
            self._volume.setWidth(machine.getSettingValueByKey('machine_width'))
            self._volume.setHeight(machine.getSettingValueByKey('machine_height'))
            self._volume.setDepth(machine.getSettingValueByKey('machine_depth'))

            disallowed_areas = machine.getSettingValueByKey('machine_disallowed_areas')
            areas = []
            if disallowed_areas:

                for area in disallowed_areas:
                    polygon = []
                    polygon.append(Vector(area[0][0], 0.1, area[0][1]))
                    polygon.append(Vector(area[1][0], 0.1, area[1][1]))
                    polygon.append(Vector(area[2][0], 0.1, area[2][1]))
                    polygon.append(Vector(area[3][0], 0.1, area[3][1]))
                    areas.append(polygon)
            self._volume.setDisallowedAreas(areas)

            self._volume.rebuild()

            offset = machine.getSettingValueByKey('machine_platform_offset')
            if offset:
                self._platform.setPosition(Vector(offset[0], offset[1], offset[2]))
            else:
                self._platform.setPosition(Vector(0.0, 0.0, 0.0))

    removableDrivesChanged = pyqtSignal()

    outputDeviceChanged = pyqtSignal()
    @pyqtProperty(str, notify = outputDeviceChanged)
    def outputDevice(self):
        return self._output_source

    @pyqtProperty(str, notify = outputDeviceChanged)
    def outputDeviceIcon(self):
        if self._output_source == 'local_file':
            return 'save'
        elif self._output_source == 'sdcard':
            return 'save_sd'
        elif self._output_source == 'usb':
            return 'print_usb'

    @pyqtSlot()
    def writeToOutputDevice(self):
        pass

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
