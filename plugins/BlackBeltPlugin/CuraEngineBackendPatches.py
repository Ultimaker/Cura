from UM.Application import Application
from UM.Logger import Logger
from UM.Backend.Backend import BackendState
from UM.Qt.Duration import DurationFormat

from . import ProcessSlicedLayersJob
from . import StartSliceJob

from time import time

class CuraEngineBackendPatches():
    def __init__(self, backend):
        self._backend = backend

        self._backend._change_timer.timeout.disconnect(self._backend.slice)
        self._backend.slice = self.slice
        self._backend._change_timer.timeout.connect(self.slice)

        self._backend._onSlicingFinishedMessage = self._onSlicingFinishedMessage
        self._backend._message_handlers["cura.proto.SlicingFinished"] = self._onSlicingFinishedMessage

    ##  Perform a slice of the scene.
    def slice(self):
        self._backend._slice_start_time = time()
        if not self._backend._need_slicing:
            self._backend.processingProgress.emit(1.0)
            self._backend.backendStateChange.emit(BackendState.Done)
            Logger.log("w", "Slice unnecessary, nothing has changed that needs reslicing.")
            return

        Application.getInstance().getPrintInformation().setToZeroPrintInformation()

        self._backend._stored_layer_data = []
        self._backend._stored_optimized_layer_data = []

        if self._backend._process is None:
            self._backend._createSocket()
        self._backend.stopSlicing()
        self._backend._engine_is_fresh = False  # Yes we're going to use the engine

        self._backend.processingProgress.emit(0.0)
        self._backend.backendStateChange.emit(BackendState.NotStarted)

        self._backend._scene.gcode_list = []
        self._backend._slicing = True
        self._backend.slicingStarted.emit()

        slice_message = self._backend._socket.createMessage("cura.proto.Slice")
        self._backend._start_slice_job = StartSliceJob.StartSliceJob(slice_message)
        self._backend._start_slice_job.start()
        self._backend._start_slice_job.finished.connect(self._backend._onStartSliceCompleted)

    ##  Called when the engine sends a message that slicing is finished.
    #
    #   \param message The protobuf message signalling that slicing is finished.
    def _onSlicingFinishedMessage(self, message):
        print("???????????????????????")
        self._backend.backendStateChange.emit(BackendState.Done)
        self._backend.processingProgress.emit(1.0)

        for line in self._backend._scene.gcode_list:
            replaced = line.replace("{print_time}", str(Application.getInstance().getPrintInformation().currentPrintTime.getDisplayString(DurationFormat.Format.ISO8601)))
            replaced = replaced.replace("{filament_amount}", str(Application.getInstance().getPrintInformation().materialLengths))
            replaced = replaced.replace("{filament_weight}", str(Application.getInstance().getPrintInformation().materialWeights))
            replaced = replaced.replace("{filament_cost}", str(Application.getInstance().getPrintInformation().materialCosts))
            replaced = replaced.replace("{jobname}", str(Application.getInstance().getPrintInformation().jobName))

            self._backend._scene.gcode_list[self._backend._scene.gcode_list.index(line)] = replaced

        self._backend._slicing = False
        self._backend._need_slicing = False
        Logger.log("d", "Slicing took %s seconds", time() - self._backend._slice_start_time )
        if self._backend._layer_view_active and (self._backend._process_layers_job is None or not self._backend._process_layers_job.isRunning()):
            self._backend._process_layers_job = ProcessSlicedLayersJob.ProcessSlicedLayersJob(self._backend._stored_optimized_layer_data)
            self._backend._process_layers_job.finished.connect(self._backend._onProcessLayersFinished)
            self._backend._process_layers_job.start()
            self._backend._stored_optimized_layer_data = []