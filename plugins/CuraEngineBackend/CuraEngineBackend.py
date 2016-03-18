# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Backend.Backend import Backend
from UM.Application import Application
from UM.Scene.SceneNode import SceneNode
from UM.Preferences import Preferences
from UM.Signal import Signal
from UM.Logger import Logger
from UM.Qt.Bindings.BackendProxy import BackendState #To determine the state of the slicing job.
from UM.Message import Message
from UM.PluginRegistry import PluginRegistry

from . import ProcessSlicedObjectListJob
from . import ProcessGCodeJob
from . import StartSliceJob

import os
import sys

from PyQt5.QtCore import QTimer

import Arcus

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

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

        Application.getInstance().getMachineManager().activeMachineInstanceChanged.connect(self._onChanged)

        self._profile = None
        Application.getInstance().getMachineManager().activeProfileChanged.connect(self._onActiveProfileChanged)
        self._onActiveProfileChanged()

        self._change_timer = QTimer()
        self._change_timer.setInterval(500)
        self._change_timer.setSingleShot(True)
        self._change_timer.timeout.connect(self.slice)

        self._message_handlers["cura.proto.SlicedObjectList"] = self._onSlicedObjectListMessage
        self._message_handlers["cura.proto.Progress"] = self._onProgressMessage
        self._message_handlers["cura.proto.GCodeLayer"] = self._onGCodeLayerMessage
        self._message_handlers["cura.proto.GCodePrefix"] = self._onGCodePrefixMessage
        self._message_handlers["cura.proto.ObjectPrintTime"] = self._onObjectPrintTimeMessage
        self._message_handlers["cura.proto.SlicingFinished"] = self._onSlicingFinishedMessage

        self._slicing = False
        self._restart = False
        self._enabled = True
        self._always_restart = True
        self._process_layers_job = None #The currently active job to process layers, or None if it is not processing layers.

        self._message = None

        self.backendQuit.connect(self._onBackendQuit)

        self.backendConnected.connect(self._onBackendConnected)
        Application.getInstance().getController().toolOperationStarted.connect(self._onToolOperationStarted)
        Application.getInstance().getController().toolOperationStopped.connect(self._onToolOperationStopped)

        Application.getInstance().getMachineManager().activeMachineInstanceChanged.connect(self._onInstanceChanged)

    ##  Get the command that is used to call the engine.
    #   This is usefull for debugging and used to actually start the engine
    #   \return list of commands and args / parameters.
    def getEngineCommand(self):
        active_machine = Application.getInstance().getMachineManager().getActiveMachineInstance()
        if not active_machine:
            return None

        return [Preferences.getInstance().getValue("backend/location"), "connect", "127.0.0.1:{0}".format(self._port), "-j", active_machine.getMachineDefinition().getPath(), "-vv"]

    ##  Emitted when we get a message containing print duration and material amount. This also implies the slicing has finished.
    #   \param time The amount of time the print will take.
    #   \param material_amount The amount of material the print will use.
    printDurationMessage = Signal()

    ##  Emitted when the slicing process starts.
    slicingStarted = Signal()

    ##  Emitted whne the slicing process is aborted forcefully.
    slicingCancelled = Signal()

    ##  Perform a slice of the scene.
    def slice(self):
        if not self._enabled:
            return

        if self._slicing:
            self._terminate()

            if self._message:
                self._message.hide()
                self._message = None

            self.slicingCancelled.emit()
            return

        if self._process_layers_job:
            self._process_layers_job.abort()
            self._process_layers_job = None

        if self._profile.hasErrorValue():
            Logger.log("w", "Profile has error values. Aborting slicing")
            if self._message:
                self._message.hide()
                self._message = None
            self._message = Message(catalog.i18nc("@info:status", "Unable to slice. Please check your setting values for errors."))
            self._message.show()
            return #No slicing if we have error values since those are by definition illegal values.

        self.processingProgress.emit(0.0)
        self.backendStateChange.emit(BackendState.NOT_STARTED)
        if self._message:
            self._message.setProgress(-1)
        #else:
        #    self._message = Message(catalog.i18nc("@info:status", "Slicing..."), 0, False, -1)
        #    self._message.show()

        self._scene.gcode_list = []
        self._slicing = True
        self.slicingStarted.emit()

        job = StartSliceJob.StartSliceJob(self._profile, self._socket)
        job.start()
        job.finished.connect(self._onStartSliceCompleted)

    def _terminate(self):
        self._slicing = False
        self._restart = True
        self.slicingCancelled.emit()
        if self._process is not None:
            Logger.log("d", "Killing engine process")
            try:
                self._process.terminate()
                self._process = None
            except: # terminating a process that is already terminating causes an exception, silently ignore this.
                pass
            Logger.log("d", "Engine process is killed")

    def _onStartSliceCompleted(self, job):
        if job.getError() or job.getResult() != True:
            if self._message:
                self._message.hide()
                self._message = None
            return

    def _onSceneChanged(self, source):
        if type(source) is not SceneNode:
            return

        if source is self._scene.getRoot():
            return

        if source.getMeshData() is None:
            return

        if source.getMeshData().getVertices() is None:
            return

        self._onChanged()

    def _onSocketError(self, error):
        super()._onSocketError(error)

        self._slicing = False
        self.processingProgress.emit(0)

        if error.getErrorCode() not in [Arcus.ErrorCode.BindFailedError, Arcus.ErrorCode.ConnectionResetError, Arcus.ErrorCode.Debug]:
            Logger.log("e", "A socket error caused the connection to be reset")

    def _onActiveProfileChanged(self):
        if self._profile:
            self._profile.settingValueChanged.disconnect(self._onSettingChanged)

        self._profile = Application.getInstance().getMachineManager().getWorkingProfile()
        if self._profile:
            self._profile.settingValueChanged.connect(self._onSettingChanged)
            self._onChanged()

    def _onSettingChanged(self, setting):
        self._onChanged()

    def _onSlicedObjectListMessage(self, message):
        if self._layer_view_active:
            self._process_layers_job = ProcessSlicedObjectListJob.ProcessSlicedObjectListJob(message)
            self._process_layers_job.start()
        else :
            self._stored_layer_data = message

    def _onProgressMessage(self, message):
        if self._message:
            self._message.setProgress(round(message.amount * 100))

        self.processingProgress.emit(message.amount)
        self.backendStateChange.emit(BackendState.PROCESSING)

    def _onSlicingFinishedMessage(self, message):
        self.backendStateChange.emit(BackendState.DONE)
        self.processingProgress.emit(1.0)

        self._slicing = False

        if self._message:
            self._message.setProgress(100)
            self._message.hide()
            self._message = None

    def _onGCodeLayerMessage(self, message):
        self._scene.gcode_list.append(message.data.decode("utf-8", "replace"))

    def _onGCodePrefixMessage(self, message):
        self._scene.gcode_list.insert(0, message.data.decode("utf-8", "replace"))

    def _onObjectPrintTimeMessage(self, message):
        self.printDurationMessage.emit(message.time, message.material_amount)

    def _createSocket(self):
        super()._createSocket(os.path.abspath(os.path.join(PluginRegistry.getInstance().getPluginPath(self.getPluginId()), "Cura.proto")))

    ##  Manually triggers a reslice
    def forceSlice(self):
        self._change_timer.start()

    def _onChanged(self):
        if not self._profile:
            return

        self._change_timer.start()

    def _onBackendConnected(self):
        if self._restart:
            self._onChanged()
            self._restart = False

    def _onToolOperationStarted(self, tool):
        self._terminate() # Do not continue slicing once a tool has started
        self._enabled = False # Do not reslice when a tool is doing it's 'thing'

    def _onToolOperationStopped(self, tool):
        self._enabled = True # Tool stop, start listening for changes again.

    def _onActiveViewChanged(self):
        if Application.getInstance().getController().getActiveView():
            view = Application.getInstance().getController().getActiveView()
            if view.getPluginId() == "LayerView":
                self._layer_view_active = True
                # There is data and we're not slicing at the moment
                # if we are slicing, there is no need to re-calculate the data as it will be invalid in a moment.
                if self._stored_layer_data and not self._slicing:
                    self._process_layers_job = ProcessSlicedObjectListJob.ProcessSlicedObjectListJob(self._stored_layer_data)
                    self._process_layers_job.start()
                    self._stored_layer_data = None
            else:
                self._layer_view_active = False

    def _onInstanceChanged(self):
        self._terminate()
        self.slicingCancelled.emit()

    def _onBackendQuit(self):
        if not self._restart and self._process:
            self._process = None
            self._createSocket()
