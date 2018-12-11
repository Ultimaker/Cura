# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import List, Optional, Union, Dict

from cura.PrinterOutput.ConfigurationModel import ConfigurationModel
from plugins.UM3NetworkPrinting.src.Cloud.CloudOutputController import CloudOutputController
from .CloudClusterPrinterConfiguration import CloudClusterPrinterConfiguration
from .CloudClusterPrintJobConstraint import CloudClusterPrintJobConstraints
from .BaseCloudModel import BaseCloudModel


##  Class representing a print job
from plugins.UM3NetworkPrinting.src.UM3PrintJobOutputModel import UM3PrintJobOutputModel


## Model for the status of a single print job in a cluster.
#  Spec: https://api-staging.ultimaker.com/connect/v1/spec
class CloudClusterPrintJobStatus(BaseCloudModel):
    ## Creates a new cloud print job status model.
    #  \param assigned_to: The name of the printer this job is assigned to while being queued.
    #  \param configuration: The required print core configurations of this print job.
    #  \param constraints: Print job constraints object.
    #  \param created_at: The timestamp when the job was created in Cura Connect.
    #  \param force: Allow this job to be printed despite of mismatching configurations.
    #  \param last_seen: The number of seconds since this job was checked.
    #  \param machine_variant: The machine type that this job should be printed on.Coincides with the machine_type field
    #       of the printer object.
    #  \param name: The name of the print job. Usually the name of the .gcode file.
    #  \param network_error_count: The number of errors encountered when requesting data for this print job.
    #  \param owner: The name of the user who added the print job to Cura Connect.
    #  \param printer_uuid: UUID of the printer that the job is currently printing on or assigned to.
    #  \param started: Whether the job has started printing or not.
    #  \param status: The status of the print job.
    #  \param time_elapsed: The remaining printing time in seconds.
    #  \param time_total: The total printing time in seconds.
    #  \param uuid: UUID of this print job. Should be used for identification purposes.
    def __init__(self, created_at: str, force: bool, machine_variant: str, name: str, started: bool, status: str,
                 time_total: int, uuid: str,
                 configuration: List[Union[Dict[str, any], CloudClusterPrinterConfiguration]],
                 constraints: List[Union[Dict[str, any], CloudClusterPrintJobConstraints]],
                 last_seen: Optional[float] = None, network_error_count: Optional[int] = None,
                 owner: Optional[str] = None, printer_uuid: Optional[str] = None, time_elapsed: Optional[int] = None,
                 assigned_to: Optional[str] = None, **kwargs) -> None:
        self.assigned_to = assigned_to  # type: str
        self.configuration = self.parseModels(CloudClusterPrinterConfiguration, configuration)
        self.constraints = self.parseModels(CloudClusterPrintJobConstraints, constraints)
        self.created_at = created_at
        self.force = force
        self.last_seen = last_seen
        self.machine_variant = machine_variant
        self.name = name
        self.network_error_count = network_error_count
        self.owner = owner
        self.printer_uuid = printer_uuid
        self.started = started
        self.status = status
        self.time_elapsed = time_elapsed
        self.time_total = time_total
        self.uuid = uuid
        super().__init__(**kwargs)

    ## Creates an UM3 print job output model based on this cloud cluster print job.
    #  \param printer: The output model of the printer
    def createOutputModel(self, controller: CloudOutputController) -> UM3PrintJobOutputModel:
        model = UM3PrintJobOutputModel(controller, self.uuid, self.name)
        self.updateOutputModel(model)

        return model

    ## Creates a new configuration model
    def _createConfigurationModel(self) -> ConfigurationModel:
        extruders = [extruder.createConfigurationModel() for extruder in self.configuration or ()]
        configuration = ConfigurationModel()
        configuration.setExtruderConfigurations(extruders)
        return configuration

    ## Updates an UM3 print job output model based on this cloud cluster print job.
    #  \param model: The model to update.
    def updateOutputModel(self, model: UM3PrintJobOutputModel) -> None:
        # TODO: Add `compatible_machine_families` to the cloud, than add model.setCompatibleMachineFamilies()
        # TODO: Add `impediments_to_printing` to the cloud, see ClusterUM3OutputDevice._updatePrintJob
        # TODO: Use model.updateConfigurationChanges, see ClusterUM3OutputDevice#_createConfigurationChanges
        model.updateConfiguration(self._createConfigurationModel())
        model.updateTimeTotal(self.time_total)
        model.updateTimeElapsed(self.time_elapsed)
        model.updateOwner(self.owner)
        model.updateState(self.status)
