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
from UM.Settings.Validator import ValidatorState #To find if a setting is in an error state. We can't slice then.

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

        #Triggers for when to (re)start slicing:
        if Application.getInstance().getGlobalContainerStack():
            Application.getInstance().getGlobalContainerStack().propertyChanged.connect(self._onSettingChanged) #Note: Only starts slicing when the value changed.

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

        self._start_slice_job = None
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
        json_path = Resources.getPath(Resources.DefinitionContainers, "fdmprinter.def.json")
        return [Preferences.getInstance().getValue("backend/location"), "connect", "127.0.0.1:{0}".format(self._port), "-j", json_path, "-vv"]

    def close(self):
        self._terminate()   # Forcefully shutdown the backend.

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
        self._stored_layer_data = []

        if not self._enabled: #We shouldn't be slicing.
            return

        if self._slicing: #We were already slicing. Stop the old job.
            self._terminate()

        if self._process_layers_job: #We were processing layers. Stop that, the layers are going to change soon.
            self._process_layers_job.abort()
            self._process_layers_job = None

        #Don't slice if there is a setting with an error value.
        stack = Application.getInstance().getGlobalContainerStack()
        for key in stack.getAllKeys():
            validation_state = stack.getProperty(key, "validationState")
            #Only setting instances have a validation state, so settings which
            #are not overwritten by any instance will have none. The property
            #then, and only then, evaluates to None. We make the assumption that
            #the definition defines the setting with a default value that is
            #valid. Therefore we can allow both ValidatorState.Valid and None as
            #allowable validation states.
            #TODO: This assumption is wrong! If the definition defines an inheritance function that through inheritance evaluates to a disallowed value, a setting is still invalid even though it's default!
            #TODO: Therefore we must also validate setting definitions.
            if validation_state != None and validation_state != ValidatorState.Valid:
                Logger.log("w", "Setting %s is not valid, but %s. Aborting slicing.", key, validation_state)
                if self._message: #Hide any old message before creating a new one.
                    self._message.hide()
                    self._message = None
                self._message = Message(catalog.i18nc("@info:status", "Unable to slice. Please check your setting values for errors."))
                self._message.show()
                return

        self.processingProgress.emit(0.0)
        self.backendStateChange.emit(BackendState.NOT_STARTED)
        if self._message:
            self._message.setProgress(-1)
        else:
            self._message = Message(catalog.i18nc("@info:status", "Slicing..."), 0, False, -1)
            self._message.show()

        self._scene.gcode_list = []
        self._slicing = True
        self.slicingStarted.emit()

        slice_message = self._socket.createMessage("cura.proto.Slice")
        settings_message = self._socket.createMessage("cura.proto.SettingList");
        self._start_slice_job = StartSliceJob.StartSliceJob(slice_message, settings_message)
        self._start_slice_job.start()
        self._start_slice_job.finished.connect(self._onStartSliceCompleted)

    ##  Terminate the engine process.
    def _terminate(self):
        self._slicing = False
        self._restart = True
        self._stored_layer_data = []
        if self._start_slice_job is not None:
            self._start_slice_job.cancel()

        self.slicingCancelled.emit()
        self.processingProgress.emit(0)
        Logger.log("d", "Attempting to kill the engine process")
        if self._process is not None:
            Logger.log("d", "Killing engine process")
            try:
                self._process.terminate()
                Logger.log("d", "Engine process is killed. Received return code %s", self._process.wait())
                self._process = None
            except Exception as e: # terminating a process that is already terminating causes an exception, silently ignore this.
                Logger.log("d", "Exception occurred while trying to kill the engine %s", str(e))

        if self._message:
            self._message.hide()
            self._message = None

    ##  Event handler to call when the job to initiate the slicing process is
    #   completed.
    #
    #   When the start slice job is successfully completed, it will be happily
    #   slicing. This function handles any errors that may occur during the
    #   bootstrapping of a slice job.
    #
    #   \param job The start slice job that was just finished.
    def _onStartSliceCompleted(self, job):
        # Note that cancelled slice jobs can still call this method.
        if self._start_slice_job is job:
            self._start_slice_job = None
        if job.isCancelled() or job.getError() or job.getResult() != True:
            if self._message:
                self._message.hide()
                self._message = None
            return
        else:
            # Preparation completed, send it to the backend.
            self._socket.sendMessage(job.getSettingsMessage())
            self._socket.sendMessage(job.getSliceMessage())

    ##  Listener for when the scene has changed.
    #
    #   This should start a slice if the scene is now ready to slice.
    #
    #   \param source The scene node that was changed.
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

    ##  Called when an error occurs in the socket connection towards the engine.
    #
    #   \param error The exception that occurred.
    def _onSocketError(self, error):
        if Application.getInstance().isShuttingDown():
            return

        super()._onSocketError(error)
        self._terminate()

        if error.getErrorCode() not in [Arcus.ErrorCode.BindFailedError, Arcus.ErrorCode.ConnectionResetError, Arcus.ErrorCode.Debug]:
            Logger.log("e", "A socket error caused the connection to be reset")

    ##  A setting has changed, so check if we must reslice.
    #
    #   \param instance The setting instance that has changed.
    #   \param property The property of the setting instance that has changed.
    def _onSettingChanged(self, instance, property):
        if property == "value": #Only reslice if the value has changed.
            self._onChanged()

    ##  Called when a sliced layer data message is received from the engine.
    #
    #   \param message The protobuf message containing sliced layer data.
    def _onLayerMessage(self, message):
        self._stored_layer_data.append(message)

    ##  Called when a progress message is received from the engine.
    #
    #   \param message The protobuf message containing the slicing progress.
    def _onProgressMessage(self, message):
        if self._message:
            self._message.setProgress(round(message.amount * 100))

        self.processingProgress.emit(message.amount)
        self.backendStateChange.emit(BackendState.PROCESSING)

    ##  Called when the engine sends a message that slicing is finished.
    #
    #   \param message The protobuf message signalling that slicing is finished.
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

    ##  Called when a g-code message is received from the engine.
    #
    #   \param message The protobuf message containing g-code, encoded as UTF-8.
    def _onGCodeLayerMessage(self, message):
        self._scene.gcode_list.append(message.data.decode("utf-8", "replace"))

    ##  Called when a g-code prefix message is received from the engine.
    #
    #   \param message The protobuf message containing the g-code prefix,
    #   encoded as UTF-8.
    def _onGCodePrefixMessage(self, message):
        self._scene.gcode_list.insert(0, message.data.decode("utf-8", "replace"))

    ##  Called when a print time message is received from the engine.
    #
    #   \param message The protobuf message containing the print time and
    #   material amount.
    def _onObjectPrintTimeMessage(self, message):
        self.printDurationMessage.emit(message.time, message.material_amount)

    ##  Creates a new socket connection.
    def _createSocket(self):
        super()._createSocket(os.path.abspath(os.path.join(PluginRegistry.getInstance().getPluginPath(self.getPluginId()), "Cura.proto")))

    ##  Manually triggers a reslice
    def forceSlice(self):
        self._change_timer.start()

    ##  Called when anything has changed to the stuff that needs to be sliced.
    #
    #   This indicates that we should probably re-slice soon.
    def _onChanged(self):
        self._change_timer.start()

    ##  Called when the back-end connects to the front-end.
    def _onBackendConnected(self):
        if self._restart:
            self._onChanged()
            self._restart = False

    ##  Called when the user starts using some tool.
    #
    #   When the user starts using a tool, we should pause slicing to prevent
    #   continuously slicing while the user is dragging some tool handle.
    #
    #   \param tool The tool that the user is using.
    def _onToolOperationStarted(self, tool):
        self._terminate() # Do not continue slicing once a tool has started
        self._enabled = False # Do not reslice when a tool is doing it's 'thing'

    ##  Called when the user stops using some tool.
    #
    #   This indicates that we can safely start slicing again.
    #
    #   \param tool The tool that the user was using.
    def _onToolOperationStopped(self, tool):
        self._enabled = True # Tool stop, start listening for changes again.

    ##  Called when the user changes the active view mode.
    def _onActiveViewChanged(self):
        if Application.getInstance().getController().getActiveView():
            view = Application.getInstance().getController().getActiveView()
            if view.getPluginId() == "LayerView": #If switching to layer view, we should process the layers if that hasn't been done yet.
                self._layer_view_active = True
                # There is data and we're not slicing at the moment
                # if we are slicing, there is no need to re-calculate the data as it will be invalid in a moment.
                if self._stored_layer_data and not self._slicing:
                    self._process_layers_job = ProcessSlicedLayersJob.ProcessSlicedLayersJob(self._stored_layer_data)
                    self._process_layers_job.start()
                    self._stored_layer_data = []
            else:
                self._layer_view_active = False

    ##  Called when the back-end self-terminates.
    #
    #   We should reset our state and start listening for new connections.
    def _onBackendQuit(self):
        if not self._restart and self._process:
            Logger.log("d", "Backend quit with return code %s. Resetting process and socket.", self._process.wait())
            self._process = None
            self._createSocket()
