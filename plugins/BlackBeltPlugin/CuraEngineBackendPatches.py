from UM.Logger import Logger
from UM.Backend.Backend import BackendState

from . import ProcessSlicedLayersJob
from . import StartSliceJob

from time import time

class CuraEngineBackendPatches():
    def __init__(self, backend):
        self._backend = backend

        try:
            self._backend._change_timer.timeout.disconnect(self._backend.slice)
            self._backend._change_timer.timeout.connect(self.slice)
        except:
            pass
        self._backend.slice = self.slice

        self._backend._startProcessSlicedLayersJob = self._startProcessSlicedLayersJob

    ##  Perform a slice of the scene.
    #   This is a verbatim copy of CuranEngineBackend.slice(), with the only difference being the local imports
    def slice(self) -> None:
        Logger.log("d", "Starting to slice...")
        self._backend._slice_start_time = time()
        if not self._backend._build_plates_to_be_sliced:
            self._backend.processingProgress.emit(1.0)
            Logger.log("w", "Slice unnecessary, nothing has changed that needs reslicing.")
            return

        if self._backend._process_layers_job:
            Logger.log("d", "Process layers job still busy, trying later.")
            return

        if not hasattr(self._backend._scene, "gcode_dict"):
            self._backend._scene.gcode_dict = {} #type: ignore #Because we are creating the missing attribute here.

        # see if we really have to slice
        active_build_plate = self._backend._application.getMultiBuildPlateModel().activeBuildPlate
        build_plate_to_be_sliced = self._backend._build_plates_to_be_sliced.pop(0)
        Logger.log("d", "Going to slice build plate [%s]!" % build_plate_to_be_sliced)
        num_objects = self._backend._numObjectsPerBuildPlate()

        self._backend._stored_layer_data = []
        self._backend._stored_optimized_layer_data[build_plate_to_be_sliced] = []

        if build_plate_to_be_sliced not in num_objects or num_objects[build_plate_to_be_sliced] == 0:
            self._backend._scene.gcode_dict[build_plate_to_be_sliced] = [] #type: ignore #Because we created this attribute above.
            Logger.log("d", "Build plate %s has no objects to be sliced, skipping", build_plate_to_be_sliced)
            if self._backend._build_plates_to_be_sliced:
                self._backend.slice()
            return

        if self._backend._application.getPrintInformation() and build_plate_to_be_sliced == active_build_plate:
            self._backend._application.getPrintInformation().setToZeroPrintInformation(build_plate_to_be_sliced)

        if self._backend._process is None: # type: ignore
            self._backend._createSocket()
        self._backend.stopSlicing()
        self._backend._engine_is_fresh = False  # Yes we're going to use the engine

        self._backend.processingProgress.emit(0.0)
        self._backend.backendStateChange.emit(BackendState.NotStarted)

        self._backend._scene.gcode_dict[build_plate_to_be_sliced] = [] #type: ignore #[] indexed by build plate number
        self._backend._slicing = True
        self._backend.slicingStarted.emit()

        self._backend.determineAutoSlicing()  # Switch timer on or off if appropriate

        slice_message = self._backend._socket.createMessage("cura.proto.Slice")
        ## PATCH: local import
        self._backend._start_slice_job = StartSliceJob.StartSliceJob(slice_message)
        self._backend._start_slice_job_build_plate = build_plate_to_be_sliced
        self._backend._start_slice_job.setBuildPlate(self._backend._start_slice_job_build_plate)
        self._backend._start_slice_job.start()
        self._backend._start_slice_job.finished.connect(self._backend._onStartSliceCompleted)

    #   This is a verbatim copy of CuranEngineBackend._startProcessSlicedLayersJob(), with the only difference being the local imports
    def _startProcessSlicedLayersJob(self, build_plate_number) -> None:
        ## PATCH: local import
        self._backend._process_layers_job = ProcessSlicedLayersJob.ProcessSlicedLayersJob(self._backend._stored_optimized_layer_data[build_plate_number])
        self._backend._process_layers_job.setBuildPlate(build_plate_number)
        self._backend._process_layers_job.finished.connect(self._backend._onProcessLayersFinished)
        self._backend._process_layers_job.start()
