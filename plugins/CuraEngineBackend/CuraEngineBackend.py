# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Backend.Backend import Backend, BackendState
from UM.Application import Application
from UM.Scene.SceneNode import SceneNode
from UM.Preferences import Preferences
from UM.Signal import Signal
from UM.Logger import Logger
from UM.Message import Message
from UM.PluginRegistry import PluginRegistry
from UM.Resources import Resources
from UM.Settings.Validator import ValidatorState #To find if a setting is in an error state. We can't slice then.
from UM.Platform import Platform

import cura.Settings

from cura.OneAtATimeIterator import OneAtATimeIterator
from cura.Settings.ExtruderManager import ExtruderManager
from . import ProcessSlicedLayersJob
from . import ProcessGCodeJob
from . import StartSliceJob

import os
import sys
from time import time

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
        # Find out where the engine is located, and how it is called.
        # This depends on how Cura is packaged and which OS we are running on.
        executable_name = "CuraEngine"
        if Platform.isWindows():
            executable_name += ".exe"
        default_engine_location = executable_name
        if os.path.exists(os.path.join(Application.getInstallPrefix(), "bin", executable_name)):
            default_engine_location = os.path.join(Application.getInstallPrefix(), "bin", executable_name)
        if hasattr(sys, "frozen"):
            default_engine_location = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), executable_name)
        if Platform.isLinux() and not default_engine_location:
            if not os.getenv("PATH"):
                raise OSError("There is something wrong with your Linux installation.")
            for pathdir in os.getenv("PATH").split(os.pathsep):
                execpath = os.path.join(pathdir, executable_name)
                if os.path.exists(execpath):
                    default_engine_location = execpath
                    break

        if not default_engine_location:
            raise EnvironmentError("Could not find CuraEngine")

        Logger.log("i", "Found CuraEngine at: %s" %(default_engine_location))

        default_engine_location = os.path.abspath(default_engine_location)
        Preferences.getInstance().addPreference("backend/location", default_engine_location)

        self._scene = Application.getInstance().getController().getScene()
        self._scene.sceneChanged.connect(self._onSceneChanged)

        # Workaround to disable layer view processing if layer view is not active.
        self._layer_view_active = False
        Application.getInstance().getController().activeViewChanged.connect(self._onActiveViewChanged)
        self._onActiveViewChanged()
        self._stored_layer_data = []
        self._stored_optimized_layer_data = []

        # Triggers for when to (re)start slicing:
        self._global_container_stack = None
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalStackChanged)
        self._onGlobalStackChanged()

        self._active_extruder_stack = None
        cura.Settings.ExtruderManager.getInstance().activeExtruderChanged.connect(self._onActiveExtruderChanged)
        self._onActiveExtruderChanged()

        # When you update a setting and other settings get changed through inheritance, many propertyChanged signals are fired.
        # This timer will group them up, and only slice for the last setting changed signal.
        # TODO: Properly group propertyChanged signals by whether they are triggered by the same user interaction.
        self._change_timer = QTimer()
        self._change_timer.setInterval(500)
        self._change_timer.setSingleShot(True)
        self._change_timer.timeout.connect(self.slice)

        # Listeners for receiving messages from the back-end.
        self._message_handlers["cura.proto.Layer"] = self._onLayerMessage
        self._message_handlers["cura.proto.LayerOptimized"] = self._onOptimizedLayerMessage
        self._message_handlers["cura.proto.Progress"] = self._onProgressMessage
        self._message_handlers["cura.proto.GCodeLayer"] = self._onGCodeLayerMessage
        self._message_handlers["cura.proto.GCodePrefix"] = self._onGCodePrefixMessage
        self._message_handlers["cura.proto.PrintTimeMaterialEstimates"] = self._onPrintTimeMaterialEstimates
        self._message_handlers["cura.proto.SlicingFinished"] = self._onSlicingFinishedMessage

        self._start_slice_job = None
        self._slicing = False  # Are we currently slicing?
        self._restart = False  # Back-end is currently restarting?
        self._enabled = True  # Should we be slicing? Slicing might be paused when, for instance, the user is dragging the mesh around.
        self._always_restart = True  # Always restart the engine when starting a new slice. Don't keep the process running. TODO: Fix engine statelessness.
        self._process_layers_job = None  # The currently active job to process layers, or None if it is not processing layers.

        self._backend_log_max_lines = 20000  # Maximum number of lines to buffer
        self._error_message = None  # Pop-up message that shows errors.

        self.backendQuit.connect(self._onBackendQuit)
        self.backendConnected.connect(self._onBackendConnected)

        # When a tool operation is in progress, don't slice. So we need to listen for tool operations.
        Application.getInstance().getController().toolOperationStarted.connect(self._onToolOperationStarted)
        Application.getInstance().getController().toolOperationStopped.connect(self._onToolOperationStopped)

        self._slice_start_time = None

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
        return [Preferences.getInstance().getValue("backend/location"), "connect", "127.0.0.1:{0}".format(self._port), "-j", json_path, ""]

    ##  Emitted when we get a message containing print duration and material amount.
    #   This also implies the slicing has finished.
    #   \param time The amount of time the print will take.
    #   \param material_amount The amount of material the print will use.
    printDurationMessage = Signal()

    ##  Emitted when the slicing process starts.
    slicingStarted = Signal()

    ##  Emitted when the slicing process is aborted forcefully.
    slicingCancelled = Signal()

    ##  Perform a slice of the scene.
    def slice(self):
        self._slice_start_time = time()
        if not self._enabled or not self._global_container_stack:  # We shouldn't be slicing.
            # try again in a short time
            self._change_timer.start()
            return

        self.printDurationMessage.emit(0, [0])

        self._stored_layer_data = []
        self._stored_optimized_layer_data = []

        if self._slicing:  # We were already slicing. Stop the old job.
            self._terminate()

        if self._process_layers_job:  # We were processing layers. Stop that, the layers are going to change soon.
            self._process_layers_job.abort()
            self._process_layers_job = None

        if self._error_message:
            self._error_message.hide()

        self.processingProgress.emit(0.0)
        self.backendStateChange.emit(BackendState.NotStarted)

        self._scene.gcode_list = []
        self._slicing = True
        self.slicingStarted.emit()

        slice_message = self._socket.createMessage("cura.proto.Slice")
        self._start_slice_job = StartSliceJob.StartSliceJob(slice_message)
        self._start_slice_job.start()
        self._start_slice_job.finished.connect(self._onStartSliceCompleted)

    ##  Terminate the engine process.
    def _terminate(self):
        self._slicing = False
        self._restart = True
        self._stored_layer_data = []
        self._stored_optimized_layer_data = []
        if self._start_slice_job is not None:
            self._start_slice_job.cancel()

        self.slicingCancelled.emit()
        self.processingProgress.emit(0)
        Logger.log("d", "Attempting to kill the engine process")
        self._createSocket()  # Ensure that we have a fresh socket.
        if Application.getInstance().getCommandLineOption("external-backend", False):
            return

        if self._process is not None:
            Logger.log("d", "Killing engine process")
            try:
                self._process.terminate()
                Logger.log("d", "Engine process is killed. Received return code %s", self._process.wait())
                self._process = None

            except Exception as e:  # terminating a process that is already terminating causes an exception, silently ignore this.
                Logger.log("d", "Exception occurred while trying to kill the engine %s", str(e))

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

        if job.isCancelled() or job.getError() or job.getResult() == StartSliceJob.StartJobResult.Error:
            return

        if job.getResult() == StartSliceJob.StartJobResult.SettingError:
            if Application.getInstance().getPlatformActivity:
                self._error_message = Message(catalog.i18nc("@info:status", "Unable to slice. Please check your setting values for errors."))
                self._error_message.show()
                self.backendStateChange.emit(BackendState.Error)
            else:
                self.backendStateChange.emit(BackendState.NotStarted)
            return

        if job.getResult() == StartSliceJob.StartJobResult.NothingToSlice:
            if Application.getInstance().getPlatformActivity:
                self._error_message = Message(catalog.i18nc("@info:status", "Unable to slice. No suitable models found."))
                self._error_message.show()
                self.backendStateChange.emit(BackendState.Error)
            else:
                self.backendStateChange.emit(BackendState.NotStarted)
            return

        # Preparation completed, send it to the backend.
        self._socket.sendMessage(job.getSliceMessage())
        Logger.log("d", "Sending slice message took %s seconds", time() - self._slice_start_time )

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
        if error.getErrorCode() == Arcus.ErrorCode.Debug:
            return

        self._terminate()

        if error.getErrorCode() not in [Arcus.ErrorCode.BindFailedError, Arcus.ErrorCode.ConnectionResetError, Arcus.ErrorCode.Debug]:
            Logger.log("e", "A socket error caused the connection to be reset")

    ##  A setting has changed, so check if we must reslice.
    #
    #   \param instance The setting instance that has changed.
    #   \param property The property of the setting instance that has changed.
    def _onSettingChanged(self, instance, property):
        if property == "value": # Only reslice if the value has changed.
            self._onChanged()

    ##  Called when a sliced layer data message is received from the engine.
    #
    #   \param message The protobuf message containing sliced layer data.
    def _onLayerMessage(self, message):
        self._stored_layer_data.append(message)

    ##  Called when an optimized sliced layer data message is received from the engine.
    #
    #   \param message The protobuf message containing sliced layer data.
    def _onOptimizedLayerMessage(self, message):
        self._stored_optimized_layer_data.append(message)

    ##  Called when a progress message is received from the engine.
    #
    #   \param message The protobuf message containing the slicing progress.
    def _onProgressMessage(self, message):
        self.processingProgress.emit(message.amount)
        self.backendStateChange.emit(BackendState.Processing)

    ##  Called when the engine sends a message that slicing is finished.
    #
    #   \param message The protobuf message signalling that slicing is finished.
    def _onSlicingFinishedMessage(self, message):
        self.backendStateChange.emit(BackendState.Done)
        self.processingProgress.emit(1.0)

        self._slicing = False
        Logger.log("d", "Slicing took %s seconds", time() - self._slice_start_time )
        if self._layer_view_active and (self._process_layers_job is None or not self._process_layers_job.isRunning()):
            self._process_layers_job = ProcessSlicedLayersJob.ProcessSlicedLayersJob(self._stored_optimized_layer_data)
            self._process_layers_job.start()
            self._stored_optimized_layer_data = []

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
    #   \param message The protobuff message containing the print time and
    #   material amount per extruder
    def _onPrintTimeMaterialEstimates(self, message):
        material_amounts = []
        for index in range(message.repeatedMessageCount("materialEstimates")):
            material_amounts.append(message.getRepeatedMessage("materialEstimates", index).material_amount)
        self.printDurationMessage.emit(message.time, material_amounts)

    ##  Creates a new socket connection.
    def _createSocket(self):
        super()._createSocket(os.path.abspath(os.path.join(PluginRegistry.getInstance().getPluginPath(self.getPluginId()), "Cura.proto")))

    ##  Manually triggers a reslice
    def forceSlice(self):
        self._change_timer.start()

    ##  Called when anything has changed to the stuff that needs to be sliced.
    #
    #   This indicates that we should probably re-slice soon.
    def _onChanged(self, *args, **kwargs):
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
        self._terminate()  # Do not continue slicing once a tool has started
        self._enabled = False  # Do not reslice when a tool is doing it's 'thing'

    ##  Called when the user stops using some tool.
    #
    #   This indicates that we can safely start slicing again.
    #
    #   \param tool The tool that the user was using.
    def _onToolOperationStopped(self, tool):
        self._enabled = True  # Tool stop, start listening for changes again.

    ##  Called when the user changes the active view mode.
    def _onActiveViewChanged(self):
        if Application.getInstance().getController().getActiveView():
            view = Application.getInstance().getController().getActiveView()
            if view.getPluginId() == "LayerView":  # If switching to layer view, we should process the layers if that hasn't been done yet.
                self._layer_view_active = True
                # There is data and we're not slicing at the moment
                # if we are slicing, there is no need to re-calculate the data as it will be invalid in a moment.
                if self._stored_optimized_layer_data and not self._slicing:
                    self._process_layers_job = ProcessSlicedLayersJob.ProcessSlicedLayersJob(self._stored_optimized_layer_data)
                    self._process_layers_job.start()
                    self._stored_optimized_layer_data = []
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

    ##  Called when the global container stack changes
    def _onGlobalStackChanged(self):
        if self._global_container_stack:
            self._global_container_stack.propertyChanged.disconnect(self._onSettingChanged)
            self._global_container_stack.containersChanged.disconnect(self._onChanged)
            extruders = list(ExtruderManager.getInstance().getMachineExtruders(self._global_container_stack.getId()))
            if extruders:
                for extruder in extruders:
                    extruder.propertyChanged.disconnect(self._onSettingChanged)

        self._global_container_stack = Application.getInstance().getGlobalContainerStack()

        if self._global_container_stack:
            self._global_container_stack.propertyChanged.connect(self._onSettingChanged)  # Note: Only starts slicing when the value changed.
            self._global_container_stack.containersChanged.connect(self._onChanged)
            extruders = list(ExtruderManager.getInstance().getMachineExtruders(self._global_container_stack.getId()))
            if extruders:
                for extruder in extruders:
                    extruder.propertyChanged.connect(self._onSettingChanged)
            self._onActiveExtruderChanged()
            self._onChanged()

    def _onActiveExtruderChanged(self):
        if self._global_container_stack:
            # Connect all extruders of the active machine. This might cause a few connects that have already happend,
            # but that shouldn't cause issues as only new / unique connections are added.
            extruders = list(ExtruderManager.getInstance().getMachineExtruders(self._global_container_stack.getId()))
            if extruders:
                for extruder in extruders:
                    extruder.propertyChanged.connect(self._onSettingChanged)
        if self._active_extruder_stack:
            self._active_extruder_stack.containersChanged.disconnect(self._onChanged)

        self._active_extruder_stack = cura.Settings.ExtruderManager.getInstance().getActiveExtruderStack()
        if self._active_extruder_stack:
            self._active_extruder_stack.containersChanged.connect(self._onChanged)

