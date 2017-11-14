# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

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
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Qt.Duration import DurationFormat
from PyQt5.QtCore import QObject, pyqtSlot

from cura.Settings.ExtruderManager import ExtruderManager
from . import ProcessSlicedLayersJob
from . import StartSliceJob

import os
import sys
from time import time

from PyQt5.QtCore import QTimer

import Arcus

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

class CuraEngineBackend(QObject, Backend):
    ##  Starts the back-end plug-in.
    #
    #   This registers all the signal listeners and prepares for communication
    #   with the back-end in general.
    #   CuraEngineBackend is exposed to qml as well.
    def __init__(self, parent = None):
        super().__init__(parent = parent)
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

        # Workaround to disable layer view processing if layer view is not active.
        self._layer_view_active = False
        Application.getInstance().getController().activeViewChanged.connect(self._onActiveViewChanged)
        self._onActiveViewChanged()
        self._stored_layer_data = []
        self._stored_optimized_layer_data = []

        self._scene = Application.getInstance().getController().getScene()
        self._scene.sceneChanged.connect(self._onSceneChanged)

        # Triggers for auto-slicing. Auto-slicing is triggered as follows:
        #  - auto-slicing is started with a timer
        #  - whenever there is a value change, we start the timer
        #  - sometimes an error check can get scheduled for a value change, in that case, we ONLY want to start the
        #    auto-slicing timer when that error check is finished
        #  If there is an error check, it will set the "_is_error_check_scheduled" flag, stop the auto-slicing timer,
        #  and only wait for the error check to be finished to start the auto-slicing timer again.
        #
        self._global_container_stack = None
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalStackChanged)
        self._onGlobalStackChanged()

        Application.getInstance().stacksValidationFinished.connect(self._onStackErrorCheckFinished)

        # A flag indicating if an error check was scheduled
        # If so, we will stop the auto-slice timer and start upon the error check
        self._is_error_check_scheduled = False

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
        self._tool_active = False  # If a tool is active, some tasks do not have to do anything
        self._always_restart = True  # Always restart the engine when starting a new slice. Don't keep the process running. TODO: Fix engine statelessness.
        self._process_layers_job = None  # The currently active job to process layers, or None if it is not processing layers.
        self._need_slicing = False
        self._engine_is_fresh = True  # Is the newly started engine used before or not?

        self._backend_log_max_lines = 20000  # Maximum number of lines to buffer
        self._error_message = None  # Pop-up message that shows errors.
        self._last_num_objects = 0  # Count number of objects to see if there is something changed
        self._postponed_scene_change_sources = []  # scene change is postponed (by a tool)

        self.backendQuit.connect(self._onBackendQuit)
        self.backendConnected.connect(self._onBackendConnected)

        # When a tool operation is in progress, don't slice. So we need to listen for tool operations.
        Application.getInstance().getController().toolOperationStarted.connect(self._onToolOperationStarted)
        Application.getInstance().getController().toolOperationStopped.connect(self._onToolOperationStopped)

        self._slice_start_time = None

        Preferences.getInstance().addPreference("general/auto_slice", True)

        self._use_timer = False
        # When you update a setting and other settings get changed through inheritance, many propertyChanged signals are fired.
        # This timer will group them up, and only slice for the last setting changed signal.
        # TODO: Properly group propertyChanged signals by whether they are triggered by the same user interaction.
        self._change_timer = QTimer()
        self._change_timer.setSingleShot(True)
        self._change_timer.setInterval(500)
        self.determineAutoSlicing()
        Preferences.getInstance().preferenceChanged.connect(self._onPreferencesChanged)

    ##  Terminate the engine process.
    #
    #   This function should terminate the engine process.
    #   Called when closing the application.
    def close(self):
        # Terminate CuraEngine if it is still running at this point
        self._terminate()

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

    @pyqtSlot()
    def stopSlicing(self):
        self.backendStateChange.emit(BackendState.NotStarted)
        if self._slicing:  # We were already slicing. Stop the old job.
            self._terminate()
            self._createSocket()

        if self._process_layers_job:  # We were processing layers. Stop that, the layers are going to change soon.
            self._process_layers_job.abort()
            self._process_layers_job = None

        if self._error_message:
            self._error_message.hide()

    ##  Manually triggers a reslice
    @pyqtSlot()
    def forceSlice(self):
        if self._use_timer:
            self._change_timer.start()
        else:
            self.slice()

    ##  Perform a slice of the scene.
    def slice(self):
        self._slice_start_time = time()
        if not self._need_slicing:
            self.processingProgress.emit(1.0)
            self.backendStateChange.emit(BackendState.Done)
            Logger.log("w", "Slice unnecessary, nothing has changed that needs reslicing.")
            return
        if Application.getInstance().getPrintInformation():
            Application.getInstance().getPrintInformation().setToZeroPrintInformation()

        self._stored_layer_data = []
        self._stored_optimized_layer_data = []

        if self._process is None:
            self._createSocket()
        self.stopSlicing()
        self._engine_is_fresh = False  # Yes we're going to use the engine

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
    #   Start the engine process by calling _createSocket()
    def _terminate(self):
        self._slicing = False
        self._stored_layer_data = []
        self._stored_optimized_layer_data = []
        if self._start_slice_job is not None:
            self._start_slice_job.cancel()

        self.slicingCancelled.emit()
        self.processingProgress.emit(0)
        Logger.log("d", "Attempting to kill the engine process")

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
        if self._error_message:
            self._error_message.hide()

        # Note that cancelled slice jobs can still call this method.
        if self._start_slice_job is job:
            self._start_slice_job = None

        if job.isCancelled() or job.getError() or job.getResult() == StartSliceJob.StartJobResult.Error:
            return

        if job.getResult() == StartSliceJob.StartJobResult.MaterialIncompatible:
            if Application.getInstance().platformActivity:
                self._error_message = Message(catalog.i18nc("@info:status",
                                            "Unable to slice with the current material as it is incompatible with the selected machine or configuration."), title = catalog.i18nc("@info:title", "Unable to slice"))
                self._error_message.show()
                self.backendStateChange.emit(BackendState.Error)
            else:
                self.backendStateChange.emit(BackendState.NotStarted)
            return

        if job.getResult() == StartSliceJob.StartJobResult.SettingError:
            if Application.getInstance().platformActivity:
                extruders = list(ExtruderManager.getInstance().getMachineExtruders(self._global_container_stack.getId()))
                error_keys = []
                for extruder in extruders:
                    error_keys.extend(extruder.getErrorKeys())
                if not extruders:
                    error_keys = self._global_container_stack.getErrorKeys()
                error_labels = set()
                for key in error_keys:
                    for stack in [self._global_container_stack] + extruders: #Search all container stacks for the definition of this setting. Some are only in an extruder stack.
                        definitions = stack.getBottom().findDefinitions(key = key)
                        if definitions:
                            break #Found it! No need to continue search.
                    else: #No stack has a definition for this setting.
                        Logger.log("w", "When checking settings for errors, unable to find definition for key: {key}".format(key = key))
                        continue
                    error_labels.add(definitions[0].label)

                error_labels = ", ".join(error_labels)
                self._error_message = Message(catalog.i18nc("@info:status", "Unable to slice with the current settings. The following settings have errors: {0}").format(error_labels),
                                              title = catalog.i18nc("@info:title", "Unable to slice"))
                self._error_message.show()
                self.backendStateChange.emit(BackendState.Error)
            else:
                self.backendStateChange.emit(BackendState.NotStarted)
            return

        if job.getResult() == StartSliceJob.StartJobResult.BuildPlateError:
            if Application.getInstance().platformActivity:
                self._error_message = Message(catalog.i18nc("@info:status", "Unable to slice because the prime tower or prime position(s) are invalid."),
                                              title = catalog.i18nc("@info:title", "Unable to slice"))
                self._error_message.show()
                self.backendStateChange.emit(BackendState.Error)
            else:
                self.backendStateChange.emit(BackendState.NotStarted)

        if job.getResult() == StartSliceJob.StartJobResult.NothingToSlice:
            if Application.getInstance().platformActivity:
                self._error_message = Message(catalog.i18nc("@info:status", "Nothing to slice because none of the models fit the build volume. Please scale or rotate models to fit."),
                                              title = catalog.i18nc("@info:title", "Unable to slice"))
                self._error_message.show()
                self.backendStateChange.emit(BackendState.Error)
            else:
                self.backendStateChange.emit(BackendState.NotStarted)
            return
        # Preparation completed, send it to the backend.
        self._socket.sendMessage(job.getSliceMessage())

        # Notify the user that it's now up to the backend to do it's job
        self.backendStateChange.emit(BackendState.Processing)

        Logger.log("d", "Sending slice message took %s seconds", time() - self._slice_start_time )

    ##  Determine enable or disable auto slicing. Return True for enable timer and False otherwise.
    #   It disables when
    #   - preference auto slice is off
    #   - decorator isBlockSlicing is found (used in g-code reader)
    def determineAutoSlicing(self):
        enable_timer = True

        if not Preferences.getInstance().getValue("general/auto_slice"):
            enable_timer = False
        for node in DepthFirstIterator(self._scene.getRoot()):
            if node.callDecoration("isBlockSlicing"):
                enable_timer = False
                self.backendStateChange.emit(BackendState.Disabled)
            gcode_list = node.callDecoration("getGCodeList")
            if gcode_list is not None:
                self._scene.gcode_list = gcode_list

        if self._use_timer == enable_timer:
            return self._use_timer
        if enable_timer:
            self.backendStateChange.emit(BackendState.NotStarted)
            self.enableTimer()
            return True
        else:
            self.disableTimer()
            return False

    ##  Listener for when the scene has changed.
    #
    #   This should start a slice if the scene is now ready to slice.
    #
    #   \param source The scene node that was changed.
    def _onSceneChanged(self, source):
        if type(source) is not SceneNode:
            return

        root_scene_nodes_changed = False
        if source == self._scene.getRoot():
            num_objects = 0
            for node in DepthFirstIterator(self._scene.getRoot()):
                # Only count sliceable objects
                if node.callDecoration("isSliceable"):
                    num_objects += 1
            if num_objects != self._last_num_objects:
                self._last_num_objects = num_objects
                root_scene_nodes_changed = True
            else:
                return

        if not source.callDecoration("isGroup") and not root_scene_nodes_changed:
            if source.getMeshData() is None:
                return
            if source.getMeshData().getVertices() is None:
                return

        if self._tool_active:
            # do it later, each source only has to be done once
            if source not in self._postponed_scene_change_sources:
                self._postponed_scene_change_sources.append(source)
            return

        self.needsSlicing()
        self.stopSlicing()
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
        self._createSocket()

        if error.getErrorCode() not in [Arcus.ErrorCode.BindFailedError, Arcus.ErrorCode.ConnectionResetError, Arcus.ErrorCode.Debug]:
            Logger.log("w", "A socket error caused the connection to be reset")

    ##  Remove old layer data (if any)
    def _clearLayerData(self):
        for node in DepthFirstIterator(self._scene.getRoot()):
            if node.callDecoration("getLayerData"):
                node.getParent().removeChild(node)
                break

    ##  Convenient function: set need_slicing, emit state and clear layer data
    def needsSlicing(self):
        self.stopSlicing()
        self._need_slicing = True
        self.processingProgress.emit(0.0)
        self.backendStateChange.emit(BackendState.NotStarted)
        if not self._use_timer:
            # With manually having to slice, we want to clear the old invalid layer data.
            self._clearLayerData()

    ##  A setting has changed, so check if we must reslice.
    # \param instance The setting instance that has changed.
    # \param property The property of the setting instance that has changed.
    def _onSettingChanged(self, instance, property):
        if property == "value":  # Only reslice if the value has changed.
            self.needsSlicing()
            self._onChanged()

        elif property == "validationState":
            if self._use_timer:
                self._is_error_check_scheduled = True
                self._change_timer.stop()

    def _onStackErrorCheckFinished(self):
        self._is_error_check_scheduled = False
        if not self._slicing and self._need_slicing:
            self.needsSlicing()
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

        for line in self._scene.gcode_list:
            replaced = line.replace("{print_time}", str(Application.getInstance().getPrintInformation().currentPrintTime.getDisplayString(DurationFormat.Format.ISO8601)))
            replaced = replaced.replace("{filament_amount}", str(Application.getInstance().getPrintInformation().materialLengths))
            replaced = replaced.replace("{filament_weight}", str(Application.getInstance().getPrintInformation().materialWeights))
            replaced = replaced.replace("{filament_cost}", str(Application.getInstance().getPrintInformation().materialCosts))
            replaced = replaced.replace("{jobname}", str(Application.getInstance().getPrintInformation().jobName))

            self._scene.gcode_list[self._scene.gcode_list.index(line)] = replaced

        self._slicing = False
        self._need_slicing = False
        Logger.log("d", "Slicing took %s seconds", time() - self._slice_start_time )
        if self._layer_view_active and (self._process_layers_job is None or not self._process_layers_job.isRunning()):
            self._process_layers_job = ProcessSlicedLayersJob.ProcessSlicedLayersJob(self._stored_optimized_layer_data)
            self._process_layers_job.finished.connect(self._onProcessLayersFinished)
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

    ##  Creates a new socket connection.
    def _createSocket(self):
        super()._createSocket(os.path.abspath(os.path.join(PluginRegistry.getInstance().getPluginPath(self.getPluginId()), "Cura.proto")))
        self._engine_is_fresh = True

    ##  Called when anything has changed to the stuff that needs to be sliced.
    #
    #   This indicates that we should probably re-slice soon.
    def _onChanged(self, *args, **kwargs):
        self.needsSlicing()
        if self._use_timer:
            # if the error check is scheduled, wait for the error check finish signal to trigger auto-slice,
            # otherwise business as usual
            if self._is_error_check_scheduled:
                self._change_timer.stop()
            else:
                self._change_timer.start()

    ##  Called when a print time message is received from the engine.
    #
    #   \param message The protobuf message containing the print time per feature and
    #   material amount per extruder
    def _onPrintTimeMaterialEstimates(self, message):
        material_amounts = []
        for index in range(message.repeatedMessageCount("materialEstimates")):
            material_amounts.append(message.getRepeatedMessage("materialEstimates", index).material_amount)

        times = self._parseMessagePrintTimes(message)
        self.printDurationMessage.emit(times, material_amounts)

    ##  Called for parsing message to retrieve estimated time per feature
    #
    #   \param message The protobuf message containing the print time per feature
    def _parseMessagePrintTimes(self, message):
        result = {
            "inset_0": message.time_inset_0,
            "inset_x": message.time_inset_x,
            "skin": message.time_skin,
            "infill": message.time_infill,
            "support_infill": message.time_support_infill,
            "support_interface": message.time_support_interface,
            "support": message.time_support,
            "skirt": message.time_skirt,
            "travel": message.time_travel,
            "retract": message.time_retract,
            "none": message.time_none
        }
        return result

    ##  Called when the back-end connects to the front-end.
    def _onBackendConnected(self):
        if self._restart:
            self._restart = False
            self._onChanged()

    ##  Called when the user starts using some tool.
    #
    #   When the user starts using a tool, we should pause slicing to prevent
    #   continuously slicing while the user is dragging some tool handle.
    #
    #   \param tool The tool that the user is using.
    def _onToolOperationStarted(self, tool):
        self._tool_active = True  # Do not react on scene change
        self.disableTimer()
        # Restart engine as soon as possible, we know we want to slice afterwards
        if not self._engine_is_fresh:
            self._terminate()
            self._createSocket()

    ##  Called when the user stops using some tool.
    #
    #   This indicates that we can safely start slicing again.
    #
    #   \param tool The tool that the user was using.
    def _onToolOperationStopped(self, tool):
        self._tool_active = False  # React on scene change again
        self.determineAutoSlicing()  # Switch timer on if appropriate
        # Process all the postponed scene changes
        while self._postponed_scene_change_sources:
            source = self._postponed_scene_change_sources.pop(0)
            self._onSceneChanged(source)

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
                    self._process_layers_job.finished.connect(self._onProcessLayersFinished)
                    self._process_layers_job.start()
                    self._stored_optimized_layer_data = []
            else:
                self._layer_view_active = False

    ##  Called when the back-end self-terminates.
    #
    #   We should reset our state and start listening for new connections.
    def _onBackendQuit(self):
        if not self._restart:
            if self._process:
                Logger.log("d", "Backend quit with return code %s. Resetting process and socket.", self._process.wait())
                self._process = None

    ##  Called when the global container stack changes
    def _onGlobalStackChanged(self):
        if self._global_container_stack:
            self._global_container_stack.propertyChanged.disconnect(self._onSettingChanged)
            self._global_container_stack.containersChanged.disconnect(self._onChanged)
            extruders = list(ExtruderManager.getInstance().getMachineExtruders(self._global_container_stack.getId()))

            for extruder in extruders:
                extruder.propertyChanged.disconnect(self._onSettingChanged)
                extruder.containersChanged.disconnect(self._onChanged)

        self._global_container_stack = Application.getInstance().getGlobalContainerStack()

        if self._global_container_stack:
            self._global_container_stack.propertyChanged.connect(self._onSettingChanged)  # Note: Only starts slicing when the value changed.
            self._global_container_stack.containersChanged.connect(self._onChanged)
            extruders = list(ExtruderManager.getInstance().getMachineExtruders(self._global_container_stack.getId()))
            for extruder in extruders:
                extruder.propertyChanged.connect(self._onSettingChanged)
                extruder.containersChanged.connect(self._onChanged)
            self._onChanged()

    def _onProcessLayersFinished(self, job):
        self._process_layers_job = None

    ##  Connect slice function to timer.
    def enableTimer(self):
        if not self._use_timer:
            self._change_timer.timeout.connect(self.slice)
            self._use_timer = True

    ##  Disconnect slice function from timer.
    #   This means that slicing will not be triggered automatically
    def disableTimer(self):
        if self._use_timer:
            self._use_timer = False
            self._change_timer.timeout.disconnect(self.slice)

    def _onPreferencesChanged(self, preference):
        if preference != "general/auto_slice":
            return
        auto_slice = self.determineAutoSlicing()
        if auto_slice:
            self._change_timer.start()

    ##   Tickle the backend so in case of auto slicing, it starts the timer.
    def tickle(self):
        if self._use_timer:
            self._change_timer.start()
