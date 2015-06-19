# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Qt.QtApplication import QtApplication
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Camera import Camera
from UM.Scene.Platform import Platform
from UM.Math.Vector import Vector
from UM.Math.Matrix import Matrix
from UM.Math.Quaternion import Quaternion
from UM.Resources import Resources
from UM.Scene.ToolHandle import ToolHandle
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Mesh.WriteMeshJob import WriteMeshJob
from UM.Mesh.ReadMeshJob import ReadMeshJob
from UM.Logger import Logger
from UM.Preferences import Preferences
from UM.Message import Message
from UM.PluginRegistry import PluginRegistry
from UM.JobQueue import JobQueue

from UM.Scene.BoxRenderer import BoxRenderer
from UM.Scene.Selection import Selection

from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Operations.RemoveSceneNodeOperation import RemoveSceneNodeOperation
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.SetTransformOperation import SetTransformOperation

from UM.i18n import i18nCatalog

from . import PlatformPhysics
from . import BuildVolume
from . import CameraAnimation
from . import PrintInformation
from . import CuraActions

from PyQt5.QtCore import pyqtSlot, QUrl, Qt, pyqtSignal, pyqtProperty
from PyQt5.QtGui import QColor

import platform
import sys
import os.path
import numpy
numpy.seterr(all="ignore")

class CuraApplication(QtApplication):
    def __init__(self):
        Resources.addResourcePath(os.path.join(QtApplication.getInstallPrefix(), "share", "cura"))
        if not hasattr(sys, "frozen"):
            Resources.addResourcePath(os.path.join(os.path.abspath(os.path.dirname(__file__)), ".."))

        super().__init__(name = "cura", version = "15.05.95")

        self.setRequiredPlugins([
            "CuraEngineBackend",
            "MeshView",
            "LayerView",
            "STLReader",
            "SelectionTool",
            "CameraTool",
            "GCodeWriter",
            "LocalFileStorage"
        ])
        self._physics = None
        self._volume = None
        self._platform = None
        self._output_devices = {}
        self._print_information = None
        self._i18n_catalog = None
        self._previous_active_tool = None

        self.activeMachineChanged.connect(self._onActiveMachineChanged)

        Preferences.getInstance().addPreference("cura/active_machine", "")
        Preferences.getInstance().addPreference("cura/active_mode", "simple")
        Preferences.getInstance().addPreference("cura/recent_files", "")
        Preferences.getInstance().addPreference("cura/categories_expanded", "")

        JobQueue.getInstance().jobFinished.connect(self._onJobFinished)

        self._recent_files = []
        files = Preferences.getInstance().getValue("cura/recent_files").split(";")
        for f in files:
            if not os.path.isfile(f):
                continue

            self._recent_files.append(f)
    
    ##  Handle loading of all plugin types (and the backend explicitly)
    #   \sa PluginRegistery
    def _loadPlugins(self):
        self._plugin_registry.addPluginLocation(os.path.join(QtApplication.getInstallPrefix(), "lib", "cura"))
        if not hasattr(sys, "frozen"):
            self._plugin_registry.addPluginLocation(os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "plugins"))

        self._plugin_registry.loadPlugins({ "type": "logger"})
        self._plugin_registry.loadPlugins({ "type": "storage_device" })
        self._plugin_registry.loadPlugins({ "type": "view" })
        self._plugin_registry.loadPlugins({ "type": "mesh_reader" })
        self._plugin_registry.loadPlugins({ "type": "mesh_writer" })
        self._plugin_registry.loadPlugins({ "type": "tool" })
        self._plugin_registry.loadPlugins({ "type": "extension" })

        self._plugin_registry.loadPlugin("CuraEngineBackend")

    def addCommandLineOptions(self, parser):
        parser.add_argument("file", nargs="*", help="Files to load after starting the application.")

    def run(self):
        self._i18n_catalog = i18nCatalog("cura");

        self.addOutputDevice("local_file", {
            "id": "local_file",
            "function": self._writeToLocalFile,
            "description": self._i18n_catalog.i18nc("Save button tooltip", "Save to Disk"),
            "icon": "save",
            "priority": 0
        })

        self.showSplashMessage(self._i18n_catalog.i18nc("Splash screen message", "Setting up scene..."))

        controller = self.getController()

        controller.setActiveView("MeshView")
        controller.setCameraTool("CameraTool")
        controller.setSelectionTool("SelectionTool")

        t = controller.getTool("TranslateTool")
        if t:
            t.setEnabledAxis([ToolHandle.XAxis, ToolHandle.ZAxis])

        Selection.selectionChanged.connect(self.onSelectionChanged)

        root = controller.getScene().getRoot()
        self._platform = Platform(root)

        self._volume = BuildVolume.BuildVolume(root)

        self.getRenderer().setLightPosition(Vector(0, 150, 0))
        self.getRenderer().setBackgroundColor(QColor(245, 245, 245))

        self._physics = PlatformPhysics.PlatformPhysics(controller, self._volume)

        camera = Camera("3d", root)
        camera.setPosition(Vector(-150, 150, 300))
        camera.setPerspective(True)
        camera.lookAt(Vector(0, 0, 0))

        self._camera_animation = CameraAnimation.CameraAnimation()
        self._camera_animation.setCameraTool(self.getController().getTool("CameraTool"))

        controller.getScene().setActiveCamera("3d")

        self.showSplashMessage(self._i18n_catalog.i18nc("Splash screen message", "Loading interface..."))

        self.setMainQml(Resources.getPath(Resources.QmlFilesLocation, "Cura.qml"))
        self.initializeEngine()

        self.getStorageDevice("LocalFileStorage").removableDrivesChanged.connect(self._removableDrivesChanged)

        if self.getMachines():
            active_machine_pref = Preferences.getInstance().getValue("cura/active_machine")
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

            for file in self.getCommandLineOption("file", []):
                job = ReadMeshJob(os.path.abspath(file))
                job.finished.connect(self._onFileLoaded)
                job.start()

            self.exec_()

    def registerObjects(self, engine):
        engine.rootContext().setContextProperty("Printer", self)
        self._print_information = PrintInformation.PrintInformation()
        engine.rootContext().setContextProperty("PrintInformation", self._print_information)
        self._cura_actions = CuraActions.CuraActions(self)
        engine.rootContext().setContextProperty("CuraActions", self._cura_actions)

    def onSelectionChanged(self):
        if Selection.hasSelection():
            if not self.getController().getActiveTool():
                if self._previous_active_tool:
                    self.getController().setActiveTool(self._previous_active_tool)
                    self._previous_active_tool = None
                else:
                    self.getController().setActiveTool("TranslateTool")

            self._camera_animation.setStart(self.getController().getTool("CameraTool").getOrigin())
            self._camera_animation.setTarget(Selection.getSelectedObject(0).getWorldPosition())
            self._camera_animation.start()
        else:
            if self.getController().getActiveTool():
                self._previous_active_tool = self.getController().getActiveTool().getPluginId()
                self.getController().setActiveTool(None)
            else:
                self._previous_active_tool = None

    requestAddPrinter = pyqtSignal()

    ##  Remove an object from the scene
    @pyqtSlot("quint64")
    def deleteObject(self, object_id):
        object = self.getController().getScene().findObject(object_id)

        if object:
            op = RemoveSceneNodeOperation(object)
            op.push()
    
    ##  Create a number of copies of existing object.
    @pyqtSlot("quint64", int)
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
    
    ##  Center object on platform.
    @pyqtSlot("quint64")
    def centerObject(self, object_id):
        node = self.getController().getScene().findObject(object_id)

        if node:
            op = SetTransformOperation(node, Vector())
            op.push()
    
    ##  Delete all mesh data on the scene.
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
    
    ## Reset all translation on nodes with mesh data. 
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
                op.addOperation(SetTransformOperation(node, Vector()))

            op.push()
    
    ## Reset all transformations on nodes with mesh data. 
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
                op.addOperation(SetTransformOperation(node, Vector(), Quaternion(), Vector(1, 1, 1)))

            op.push()
            
    ##  Reload all mesh data on the screen from file.
    @pyqtSlot()
    def reloadAll(self):
        nodes = []
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if type(node) is not SceneNode or not node.getMeshData():
                continue

            nodes.append(node)

        if not nodes:
            return

        for node in nodes:
            if not node.getMeshData():
                continue

            file_name = node.getMeshData().getFileName()
            if file_name:
                job = ReadMeshJob(file_name)
                job.finished.connect(lambda j: node.setMeshData(j.getResult()))
                job.start()
    
    ##  Get logging data of the backend engine
    #   \returns \type{string} Logging data
    @pyqtSlot(result=str)
    def getEngineLog(self):
        log = ""

        for entry in self.getBackend().getLog():
            log += entry.decode()

        return log

    recentFilesChanged = pyqtSignal()
    @pyqtProperty("QStringList", notify = recentFilesChanged)
    def recentFiles(self):
        return self._recent_files

    @pyqtSlot("QStringList")
    def setExpandedCategories(self, categories):
        categories = list(set(categories))
        categories.sort()
        joined = ";".join(categories)
        if joined != Preferences.getInstance().getValue("cura/categories_expanded"):
            Preferences.getInstance().setValue("cura/categories_expanded", joined)
            self.expandedCategoriesChanged.emit()

    expandedCategoriesChanged = pyqtSignal()
    @pyqtProperty("QStringList", notify = expandedCategoriesChanged)
    def expandedCategories(self):
        return Preferences.getInstance().getValue("cura/categories_expanded").split(";")

    outputDevicesChanged = pyqtSignal()
    
    @pyqtProperty("QVariantMap", notify = outputDevicesChanged)
    def outputDevices(self):
        return self._output_devices

    @pyqtProperty("QStringList", notify = outputDevicesChanged)
    def outputDeviceNames(self):
        return self._output_devices.keys()

    @pyqtSlot(str, result = "QVariant")
    def getSettingValue(self, key):
        if not self.getActiveMachine():
            return None

        return self.getActiveMachine().getSettingValueByKey(key)
    
    ##  Change setting by key value pair
    @pyqtSlot(str, "QVariant")
    def setSettingValue(self, key, value):
        if not self.getActiveMachine():
            return

        self.getActiveMachine().setSettingValueByKey(key, value)

    ##  Add an output device that can be written to.
    #
    #   \param id \type{string} The identifier used to identify the device.
    #   \param device \type{StorageDevice} A dictionary of device information.
    #                 It should contains the following:
    #                 - function: A function to be called when trying to write to the device. Will be passed the device id as first parameter.
    #                 - description: A translated string containing a description of what happens when writing to the device.
    #                 - icon: The icon to use to represent the device.
    #                 - priority: The priority of the device. The device with the highest priority will be used as the default device.
    def addOutputDevice(self, id, device):
        self._output_devices[id] = device
        self.outputDevicesChanged.emit()
    
    ##  Remove output device
    #   \param id \type{string} The identifier used to identify the device.
    #   \sa PrinterApplication::addOutputDevice()
    def removeOutputDevice(self, id):
        if id in self._output_devices:
            del self._output_devices[id]
            self.outputDevicesChanged.emit()

    @pyqtSlot(str)
    def writeToOutputDevice(self, device):
        self._output_devices[device]["function"](device)

    writeToLocalFileRequested = pyqtSignal()
    
    def _writeToLocalFile(self, device):
        self.writeToLocalFileRequested.emit()

    def _writeToSD(self, device):
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if type(node) is not SceneNode or not node.getMeshData():
                continue

            try:
                path = self.getStorageDevice("LocalFileStorage").getRemovableDrives()[device]
            except KeyError:
                Logger.log("e", "Tried to write to unknown SD card %s", device)
                return
    
            filename = os.path.join(path, node.getName()[0:node.getName().rfind(".")] + ".gcode")

            job = WriteMeshJob(filename, node.getMeshData())
            job._sdcard = device
            job.start()
            job.finished.connect(self._onWriteToSDFinished)
            return

    def _removableDrivesChanged(self):
        drives = self.getStorageDevice("LocalFileStorage").getRemovableDrives()
        for drive in drives:
            if drive not in self._output_devices:
                self.addOutputDevice(drive, {
                    "id": drive,
                    "function": self._writeToSD,
                    "description": self._i18n_catalog.i18nc("Save button tooltip. {0} is sd card name", "Save to SD Card {0}").format(drive),
                    "icon": "save_sd",
                    "priority": 1
                })

        drives_to_remove = []
        for device in self._output_devices:
            if device not in drives:
                if self._output_devices[device]["function"] == self._writeToSD:
                    drives_to_remove.append(device)

        for drive in drives_to_remove:
            self.removeOutputDevice(drive)

    def _onActiveMachineChanged(self):
        machine = self.getActiveMachine()
        if machine:
            Preferences.getInstance().setValue("cura/active_machine", machine.getName())

            self._volume.setWidth(machine.getSettingValueByKey("machine_width"))
            self._volume.setHeight(machine.getSettingValueByKey("machine_height"))
            self._volume.setDepth(machine.getSettingValueByKey("machine_depth"))

            disallowed_areas = machine.getSettingValueByKey("machine_disallowed_areas")
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

            if self.getController().getTool("ScaleTool"):
                self.getController().getTool("ScaleTool").setMaximumBounds(self._volume.getBoundingBox())

            offset = machine.getSettingValueByKey("machine_platform_offset")
            if offset:
                self._platform.setPosition(Vector(offset[0], offset[1], offset[2]))
            else:
                self._platform.setPosition(Vector(0.0, 0.0, 0.0))

    def _onWriteToSDFinished(self, job):
        message = Message(self._i18n_catalog.i18nc("Saved to SD message, {0} is sdcard, {1} is filename", "Saved to SD Card {0} as {1}").format(job._sdcard, job.getFileName()))
        message.addAction(
            "eject",
            self._i18n_catalog.i18nc("Message action", "Eject"),
            "eject",
            self._i18n_catalog.i18nc("Message action tooltip, {0} is sdcard", "Eject SD Card {0}").format(job._sdcard)
        )
        message._sdcard = job._sdcard
        message.actionTriggered.connect(self._onMessageActionTriggered)
        message.show()

    def _onMessageActionTriggered(self, message, action):
        if action == "eject":
            self.getStorageDevice("LocalFileStorage").ejectRemovableDrive(message._sdcard)

    def _onFileLoaded(self, job):
        mesh = job.getResult()
        if mesh != None:
            node = SceneNode()

            node.setSelectable(True)
            node.setMeshData(mesh)
            node.setName(os.path.basename(job.getFileName()))

            op = AddSceneNodeOperation(node, self.getController().getScene().getRoot())
            op.push()

    def _onJobFinished(self, job):
        if type(job) is not ReadMeshJob:
            return

        f = job.getFileName()
        if f in self._recent_files:
            self._recent_files.remove(f)

        self._recent_files.insert(0, f)
        if len(self._recent_files) > 10:
            del self._recent_files[10]

        Preferences.getInstance().setValue("cura/recent_files", ";".join(self._recent_files))
        self.recentFilesChanged.emit()
