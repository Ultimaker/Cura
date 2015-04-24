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
from UM.Logger import Logger
from UM.Preferences import Preferences

from UM.Scene.BoxRenderer import BoxRenderer
from UM.Scene.Selection import Selection

from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Operations.RemoveSceneNodeOperation import RemoveSceneNodeOperation
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.SetTransformOperation import SetTransformOperation

from PlatformPhysics import PlatformPhysics
from BuildVolume import BuildVolume
from CameraAnimation import CameraAnimation
from PrintInformation import PrintInformation

from PyQt5.QtCore import pyqtSlot, QUrl, Qt, pyqtSignal, pyqtProperty
from PyQt5.QtGui import QColor

import os.path
import numpy
numpy.seterr(all='ignore')

class PrinterApplication(QtApplication):
    def __init__(self):
        super().__init__(name = 'cura', version = "14.2.1")
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
        self._output_devices = {
            'local_file': {
                'id': 'local_file',
                'function': self._writeToLocalFile,
                'description': 'Save to Disk',
                'icon': 'save',
                'priority': 0
            }
        }
        self._print_information = None

        self.activeMachineChanged.connect(self._onActiveMachineChanged)

        Preferences.getInstance().addPreference('cura/active_machine', '')
        Preferences.getInstance().addPreference('cura/active_mode', 'simple')
    
    def _loadPlugins(self):
        self._plugin_registry.loadPlugins({ "type": "logger"})
        self._plugin_registry.loadPlugins({ "type": "storage_device" })
        self._plugin_registry.loadPlugins({ "type": "view" })
        self._plugin_registry.loadPlugins({ "type": "mesh_reader" })
        self._plugin_registry.loadPlugins({ "type": "mesh_writer" })
        self._plugin_registry.loadPlugins({ "type": "tool" })
        self._plugin_registry.loadPlugins({ "type": "extension" })

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

        root = controller.getScene().getRoot()
        self._platform = Platform(root)

        self._volume = BuildVolume(root)

        self.getRenderer().setLightPosition(Vector(0, 150, 0))
        self.getRenderer().setBackgroundColor(QColor(245, 245, 245))

        self._physics = PlatformPhysics(controller, self._volume)

        camera = Camera('3d', root)
        camera.setPosition(Vector(-150, 150, 300))
        camera.setPerspective(True)
        camera.lookAt(Vector(0, 0, 0))

        self._camera_animation = CameraAnimation()
        self._camera_animation.setCameraTool(self.getController().getTool('CameraTool'))

        controller.getScene().setActiveCamera('3d')

        self.showSplashMessage('Loading interface...')

        self.setMainQml(os.path.dirname(__file__), "qml/Printer.qml")
        self.initializeEngine()

        self.getStorageDevice('LocalFileStorage').removableDrivesChanged.connect(self._removableDrivesChanged)

        if self.getMachines():
            active_machine_pref = Preferences.getInstance().getValue('cura/active_machine')
            if active_machine_pref:
                for machine in self.getMachines():
                    if machine.getName() == active_machine_pref:
                        self.setActiveMachine(machine)

            if not self.getActiveMachine():
                self.setActiveMachine(self.getMachines()[0])
        else:
            self.requestAddPrinter.emit()

        self._removableDrivesChanged()
        if self._engine.rootObjects:
            self.closeSplash()

            self.exec_()

    def registerObjects(self, engine):
        engine.rootContext().setContextProperty('Printer', self)
        self._print_information = PrintInformation()
        engine.rootContext().setContextProperty('PrintInformation', self._print_information)

    def onSelectionChanged(self):
        if Selection.hasSelection():
            if not self.getController().getActiveTool():
                self.getController().setActiveTool('TranslateTool')

            self._camera_animation.setStart(self.getController().getTool('CameraTool').getOrigin())
            self._camera_animation.setTarget(Selection.getSelectedObject(0).getWorldPosition())
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

    @pyqtSlot(result=str)
    def getEngineLog(self):
        log = ""

        for entry in self.getBackend().getLog():
            log += entry.decode()

        return log

    outputDevicesChanged = pyqtSignal()
    
    @pyqtProperty('QVariantMap', notify = outputDevicesChanged)
    def outputDevices(self):
        return self._output_devices

    @pyqtProperty('QStringList', notify = outputDevicesChanged)
    def outputDeviceNames(self):
        return self._output_devices.keys()

    @pyqtSlot(str, result = 'QVariant')
    def getSettingValue(self, key):
        if not self.getActiveMachine():
            return None

        return self.getActiveMachine().getSettingValueByKey(key)

    @pyqtSlot(str, 'QVariant')
    def setSettingValue(self, key, value):
        if not self.getActiveMachine():
            return

        self.getActiveMachine().setSettingValueByKey(key, value)

    ##  Add an output device that can be written to.
    #
    #   \param id The identifier used to identify the device.
    #   \param device A dictionary of device information.
    #                 It should contains the following:
    #                 - function: A function to be called when trying to write to the device. Will be passed the device id as first parameter.
    #                 - description: A translated string containing a description of what happens when writing to the device.
    #                 - icon: The icon to use to represent the device.
    #                 - priority: The priority of the device. The device with the highest priority will be used as the default device.
    def addOutputDevice(self, id, device):
        self._output_devices[id] = device
        self.outputDevicesChanged.emit()

    def removeOutputDevice(self, id):
        if id in self._output_devices:
            del self._output_devices[id]
            self.outputDevicesChanged.emit()

    @pyqtSlot(str)
    def writeToOutputDevice(self, device):
        self._output_devices[device]['function'](device)

    writeToLocalFileRequested = pyqtSignal()
    
    def _writeToLocalFile(self, device):
        self.writeToLocalFileRequested.emit()

    def _writeToSD(self, device):
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if type(node) is not SceneNode or not node.getMeshData():
                continue

            try:
                path = self.getStorageDevice('LocalFileStorage').getRemovableDrives()[device]
            except KeyError:
                Logger.log('e', 'Tried to write to unknown SD card %s', device)
                return

            filename = os.path.join(path, node.getName()[0:node.getName().rfind('.')] + '.gcode')

            job = WriteMeshJob(filename, node.getMeshData())
            job.start()
            return

    def _removableDrivesChanged(self):
        drives = self.getStorageDevice('LocalFileStorage').getRemovableDrives()
        for drive in drives:
            if drive not in self._output_devices:
                self.addOutputDevice(drive, {
                    'id': drive,
                    'function': self._writeToSD,
                    'description': 'Save to SD Card {0}'.format(drive),
                    'icon': 'save_sd',
                    'priority': 1
                })

        for device in self._output_devices:
            if device not in drives:
                if self._output_devices[device]['function'] == self._writeToSD:
                    self.removeOutputDevice(device)

    def _onActiveMachineChanged(self):
        machine = self.getActiveMachine()
        if machine:
            Preferences.getInstance().setValue('cura/active_machine', machine.getName())

            self._volume.setWidth(machine.getSettingValueByKey('machine_width'))
            self._volume.setHeight(machine.getSettingValueByKey('machine_height'))
            self._volume.setDepth(machine.getSettingValueByKey('machine_depth'))

            disallowed_areas = machine.getSettingValueByKey('machine_disallowed_areas')
            areas = []
            if disallowed_areas:

                for area in disallowed_areas:
                    polygon = []
                    polygon.append(Vector(area[0][0], 0.2, area[0][1]))
                    polygon.append(Vector(area[1][0], 0.2, area[1][1]))
                    polygon.append(Vector(area[2][0], 0.2, area[2][1]))
                    polygon.append(Vector(area[3][0], 0.2, area[3][1]))
                    areas.append(polygon)
            self._volume.setDisallowedAreas(areas)

            self._volume.rebuild()

            offset = machine.getSettingValueByKey('machine_platform_offset')
            if offset:
                self._platform.setPosition(Vector(offset[0], offset[1], offset[2]))
            else:
                self._platform.setPosition(Vector(0.0, 0.0, 0.0))
