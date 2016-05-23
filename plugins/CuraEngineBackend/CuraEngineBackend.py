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
from UM.Resources import Resources

from cura.OneAtATimeIterator import OneAtATimeIterator
from . import ProcessSlicedLayersJob
from . import ProcessGCodeJob
from . import StartSliceJob

import os
import sys

from PyQt5.QtCore import QTimer

import Arcus

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


class CuraEngineBackend(Backend):
    ##  Starts the back-end plug-in.
    #
    #   This registers all the signal listeners and prepares for communication
    #   with the back-end in general.
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
        self._stored_layer_data = []

        #When any setting property changed, call the _onSettingChanged function.
        #This function will then see if we need to start slicing.
        Application.getInstance().getGlobalContainerStack().propertyChanged.connect(self._onSettingChanged)

        #When you update a setting and other settings get changed through inheritance, many propertyChanged signals are fired.
        #This timer will group them up, and only slice for the last setting changed signal.
        #TODO: Properly group propertyChanged signals by whether they are triggered by the same user interaction.
        self._change_timer = QTimer()
        self._change_timer.setInterval(500)
        self._change_timer.setSingleShot(True)
        self._change_timer.timeout.connect(self.slice)

        #Listeners for receiving messages from the back-end.
        self._message_handlers["cura.proto.Layer"] = self._onLayerMessage
        self._message_handlers["cura.proto.Progress"] = self._onProgressMessage
        self._message_handlers["cura.proto.GCodeLayer"] = self._onGCodeLayerMessage
        self._message_handlers["cura.proto.GCodePrefix"] = self._onGCodePrefixMessage
        self._message_handlers["cura.proto.ObjectPrintTime"] = self._onObjectPrintTimeMessage
        self._message_handlers["cura.proto.SlicingFinished"] = self._onSlicingFinishedMessage

        self._slicing = False #Are we currently slicing?
        self._restart = False #Back-end is currently restarting?
        self._enabled = True #Should we be slicing? Slicing might be paused when, for instance, the user is dragging the mesh around.
        self._always_restart = True #Always restart the engine when starting a new slice. Don't keep the process running. TODO: Fix engine statelessness.
        self._process_layers_job = None #The currently active job to process layers, or None if it is not processing layers.

        self._message = None #Pop-up message that shows the slicing progress bar (or an error message).

        self.backendQuit.connect(self._onBackendQuit)
        self.backendConnected.connect(self._onBackendConnected)

        #When a tool operation is in progress, don't slice. So we need to listen for tool operations.
        Application.getInstance().getController().toolOperationStarted.connect(self._onToolOperationStarted)
        Application.getInstance().getController().toolOperationStopped.connect(self._onToolOperationStopped)

    ##  Called when closing the application.
    #
    #   This function should terminate the engine process.
    def close(self):
        # Terminate CuraEngine if it is still running at this point
        self._terminate()
        super().close()

    ##  Get the command that is used to call the engine.
    #   This is useful for debugging and used to actually start the engine.
    #   \return list of commands and args / parameters.
    def getEngineCommand(self):
        active_machine = Application.getInstance().getMachineManager().getActiveMachineInstance()
        json_path = ""
        if not active_machine:
            json_path = Resources.getPath(Resources.MachineDefinitions, "fdmprinter.json")
        else:
            json_path = active_machine.getMachineDefinition().getPath()

        return [Preferences.getInstance().getValue("backend/location"), "connect", "127.0.0.1:{0}".format(self._port), "-j", json_path, "-vv"]

    ##  Emitted when we get a message containing print duration and material amount. This also implies the slicing has finished.
    #   \param time The amount of time the print will take.
    #   \param material_amount The amount of material the print will use.
    printDurationMessage = Signal()

    ##  Emitted when the slicing process starts.
    slicingStarted = Signal()

    ##  Emitted when the slicing process is aborted forcefully.
    slicingCancelled = Signal()

    ##  Perform a slice of the scene.
    def slice(self):
        if not self._enabled: #We shouldn't be slicing.
            return

        if self._slicing:
            self._terminate()

        if self._process_layers_job:
            self._process_layers_job.abort()
            self._process_layers_job = None

        #TODO: Re-add don't slice with error stuff.
        #if self._profile.hasErrorValue():
        #    Logger.log("w", "Profile has error values. Aborting slicing")
        #    if self._message:
        #        self._message.hide()
        #        self._message = None
        #    self._message = Message(catalog.i18nc("@info:status", "Unable to slice. Please check your setting values for errors."))
        #    self._message.show()
        #    return #No slicing if we have error values since those are by definition illegal values.

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
        self._stored_layer_data = []
        self.slicingCancelled.emit()
        self.processingProgress.emit(0)
        Logger.log("d", "Attempting to kill the engine process")
        if self._process is not None:
            Logger.log("d", "Killing engine process")
            try:
                self._process.terminate()
                Logger.log("d", "Engine process is killed. Received return code %s", self._process.wait())
                self._process = None
                #self._createSocket() # Re create the socket
            except Exception as e: # terminating a process that is already terminating causes an exception, silently ignore this.
                Logger.log("d", "Exception occured while trying to kill the engine %s", str(e))
        if self._message:
            self._message.hide()
            self._message = None


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
        if Application.getInstance().isShuttingDown():
            return

        super()._onSocketError(error)
        self._terminate()

        if error.getErrorCode() not in [Arcus.ErrorCode.BindFailedError, Arcus.ErrorCode.ConnectionResetError, Arcus.ErrorCode.Debug]:
            Logger.log("e", "A socket error caused the connection to be reset")

    def _onActiveProfileChanged(self):
        if self._profile:
            self._profile.settingValueChanged.disconnect(self._onSettingChanged)

        self._profile = Application.getInstance().getMachineManager().getWorkingProfile()
        if self._profile:
            self._profile.settingValueChanged.connect(self._onSettingChanged)
            self._onChanged()

    ##  A setting has changed, so check if we must reslice.
    #
    #   \param instance The setting instance that has changed.
    #   \param property The property of the setting instance that has changed.
    def _onSettingChanged(self, instance, property):
        if property == "value": #Only reslice if the value has changed.
            self._onChanged()

    def _onLayerMessage(self, message):
        self._stored_layer_data.append(message)


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

        if self._layer_view_active and (self._process_layers_job is None or not self._process_layers_job.isRunning()):
            self._process_layers_job = ProcessSlicedLayersJob.ProcessSlicedLayersJob(self._stored_layer_data)
            self._process_layers_job.start()
            self._stored_layer_data = []

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
                    self._process_layers_job = ProcessSlicedLayersJob.ProcessSlicedLayersJob(self._stored_layer_data)
                    self._process_layers_job.start()
                    self._stored_layer_data = []
            else:
                self._layer_view_active = False

    def _onInstanceChanged(self):
        self._terminate()

    def _onBackendQuit(self):
        if not self._restart and self._process:
            Logger.log("d", "Backend quit with return code %s. Resetting process and socket.", self._process.wait())
            self._process = None
            self._createSocket()
