# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Backend.Backend import Backend
from UM.Application import Application
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Preferences import Preferences
from UM.Math.Vector import Vector
from UM.Signal import Signal
from UM.Logger import Logger
from UM.Resources import Resources

from cura.OneAtATimeIterator import OneAtATimeIterator
from . import Cura_pb2
from . import ProcessSlicedObjectListJob
from . import ProcessGCodeJob

import os
import sys
import numpy

from PyQt5.QtCore import QTimer

class CuraEngineBackend(Backend):
    def __init__(self):
        super().__init__()

        # Find out where the engine is located, and how it is called. This depends on how Cura is packaged and which OS we are running on.
        default_engine_location = os.path.join(Application.getInstallPrefix(), "bin", "CuraEngine")
        if hasattr(sys, "frozen"):
            default_engine_location = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "CuraEngine")
        if sys.platform == "win32":
            default_engine_location += ".exe"
        default_engine_location = os.path.abspath(default_engine_location)
        Preferences.getInstance().addPreference("backend/location", default_engine_location)

        self._scene = Application.getInstance().getController().getScene()
        self._scene.sceneChanged.connect(self._onSceneChanged)

        # Workaround to disable layer view processing if layer view is not active.
        self._layer_view_active = False
        Application.getInstance().getController().activeViewChanged.connect(self._onActiveViewChanged)
        self._onActiveViewChanged()
        self._stored_layer_data = None

        self._settings = None
        Application.getInstance().activeMachineChanged.connect(self._onActiveMachineChanged)
        self._onActiveMachineChanged()

        self._change_timer = QTimer()
        self._change_timer.setInterval(500)
        self._change_timer.setSingleShot(True)
        self._change_timer.timeout.connect(self.slice)

        self._message_handlers[Cura_pb2.SlicedObjectList] = self._onSlicedObjectListMessage
        self._message_handlers[Cura_pb2.Progress] = self._onProgressMessage
        self._message_handlers[Cura_pb2.GCodeLayer] = self._onGCodeLayerMessage
        self._message_handlers[Cura_pb2.GCodePrefix] = self._onGCodePrefixMessage
        self._message_handlers[Cura_pb2.ObjectPrintTime] = self._onObjectPrintTimeMessage

        self._slicing = False
        self._restart = False

        self._save_gcode = True
        self._save_polygons = True
        self._report_progress = True

        self._enabled = True

        self.backendConnected.connect(self._onBackendConnected)

    def getEngineCommand(self):
        return [Preferences.getInstance().getValue("backend/location"), "-j", Resources.getPath(Resources.SettingsLocation, "fdmprinter.json"), "-vv", "--connect", "127.0.0.1:{0}".format(self._port)]

    ##  Emitted when we get a message containing print duration and material amount. This also implies the slicing has finished.
    #   \param time The amount of time the print will take.
    #   \param material_amount The amount of material the print will use.
    printDurationMessage = Signal()

    ##  Emitted when the slicing process starts.
    slicingStarted = Signal()

    ##  Emitted whne the slicing process is aborted forcefully.
    slicingCancelled = Signal()

    ##  Perform a slice of the scene with the given set of settings.
    #
    #   \param kwargs Keyword arguments.
    #                 Valid values are:
    #                 - settings: The settings to use for the slice. The default is the active machine.
    #                 - save_gcode: True if the generated gcode should be saved, False if not. True by default.
    #                 - save_polygons: True if the generated polygon data should be saved, False if not. True by default.
    #                 - force_restart: True if the slicing process should be forcefully restarted if it is already slicing.
    #                                  If False, this method will do nothing when already slicing. True by default.
    #                 - report_progress: True if the slicing progress should be reported, False if not. Default is True.
    def slice(self, **kwargs):
        if not self._enabled:
            return

        if self._slicing:
            if not kwargs.get("force_restart", True):
                return

            self._slicing = False
            self._restart = True
            if self._process is not None:
                Logger.log("d", "Killing engine process")
                try:
                    self._process.terminate()
                except: # terminating a process that is already terminating causes an exception, silently ignore this.
                    pass
            self.slicingCancelled.emit()
            return

        objects = []
        for node in DepthFirstIterator(self._scene.getRoot()):
            if type(node) is SceneNode and node.getMeshData() and node.getMeshData().getVertices() is not None:
                if not getattr(node, "_outside_buildarea", False):
                    objects.append(node)

        if not objects:
            return #No point in slicing an empty build plate

        if kwargs.get("settings", self._settings).hasErrorValue():
            return #No slicing if we have error values since those are by definition illegal values.

        self._slicing = True
        self.slicingStarted.emit()

        self._report_progress = kwargs.get("report_progress", True)
        if self._report_progress:
            self.processingProgress.emit(0.0)

        self._sendSettings(kwargs.get("settings", self._settings))

        self._scene.acquireLock()

        # Set the gcode as an empty list. This will be filled with strings by GCodeLayer messages.
        # This is done so the gcode can be fragmented in memory and does not need a continues memory space.
        # (AKA. This prevents MemoryErrors)
        self._save_gcode = kwargs.get("save_gcode", True)
        if self._save_gcode:
            setattr(self._scene, "gcode_list", [])

        self._save_polygons = kwargs.get("save_polygons", True)

        msg = Cura_pb2.ObjectList()

        #TODO: All at once/one at a time mode
        #print("Iterator time! ", OneAtATimeIterator(self._scene.getRoot()))
        #for item in OneAtATimeIterator(self._scene.getRoot()):
        #    print(item)
        
        center = Vector()
        for object in objects:
            center += object.getPosition()

            mesh_data = object.getMeshData().getTransformed(object.getWorldTransformation())

            obj = msg.objects.add()
            obj.id = id(object)
            
            verts = numpy.array(mesh_data.getVertices())
            verts[:,[1,2]] = verts[:,[2,1]]
            verts[:,1] *= -1
            obj.vertices = verts.tostring()

            #if meshData.hasNormals():
                #obj.normals = meshData.getNormalsAsByteArray()

            #if meshData.hasIndices():
                #obj.indices = meshData.getIndicesAsByteArray()

        self._scene.releaseLock()

        self._socket.sendMessage(msg)

    def _onSceneChanged(self, source):
        if (type(source) is not SceneNode) or (source is self._scene.getRoot()) or (source.getMeshData() is None):
            return

        if(source.getMeshData().getVertices() is None):
            return

        self._onChanged()

    def _onActiveMachineChanged(self):
        if self._settings:
            self._settings.settingChanged.disconnect(self._onSettingChanged)

        self._settings = Application.getInstance().getActiveMachine()
        if self._settings:
            self._settings.settingChanged.connect(self._onSettingChanged)
            self._onChanged()

    def _onSettingChanged(self, setting):
        self._onChanged()

    def _onSlicedObjectListMessage(self, message):
        if self._save_polygons:
            if self._layer_view_active:
                job = ProcessSlicedObjectListJob.ProcessSlicedObjectListJob(message)
                job.start()
            else :
                self._stored_layer_data = message

    def _onProgressMessage(self, message):
        if message.amount >= 0.99:
            self._slicing = False

        if self._report_progress:
            self.processingProgress.emit(message.amount)

    def _onGCodeLayerMessage(self, message):
        if self._save_gcode:
            job = ProcessGCodeJob.ProcessGCodeLayerJob(message)
            job.start()

    def _onGCodePrefixMessage(self, message):
        if self._save_gcode:
            self._scene.gcode_list.insert(0, message.data.decode("utf-8", "replace"))

    def _onObjectPrintTimeMessage(self, message):
        self.printDurationMessage.emit(message.time, message.material_amount)
        self.processingProgress.emit(1.0)

    def _createSocket(self):
        super()._createSocket()
        
        self._socket.registerMessageType(1, Cura_pb2.ObjectList)
        self._socket.registerMessageType(2, Cura_pb2.SlicedObjectList)
        self._socket.registerMessageType(3, Cura_pb2.Progress)
        self._socket.registerMessageType(4, Cura_pb2.GCodeLayer)
        self._socket.registerMessageType(5, Cura_pb2.ObjectPrintTime)
        self._socket.registerMessageType(6, Cura_pb2.SettingList)
        self._socket.registerMessageType(7, Cura_pb2.GCodePrefix)

    def _onChanged(self):
        if not self._settings:
            return

        self._change_timer.start()

    def _sendSettings(self, settings):
        msg = Cura_pb2.SettingList()
        for setting in settings.getAllSettings(include_machine=True):
            s = msg.settings.add()
            s.name = setting.getKey()
            s.value = str(setting.getValue()).encode("utf-8")

        self._socket.sendMessage(msg)

    def _onBackendConnected(self):
        if self._restart:
            self._onChanged()
            self._restart = False

    def _onToolOperationStarted(self, tool):
        self._enabled = False

    def _onToolOperationStopped(self, tool):
        self._enabled = True
        self._onChanged()

    def _onActiveViewChanged(self):
        if Application.getInstance().getController().getActiveView():
            view = Application.getInstance().getController().getActiveView()
            if view.getPluginId() == "LayerView":
                self._layer_view_active = True
                if self._stored_layer_data:
                    job = ProcessSlicedObjectListJob.ProcessSlicedObjectListJob(self._stored_layer_data)
                    job.start()
            else:
                self._layer_view_active = False
