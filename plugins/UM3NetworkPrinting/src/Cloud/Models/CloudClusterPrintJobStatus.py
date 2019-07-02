# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import List, Optional, Union, Dict, Any

from cura.PrinterOutput.Models.PrinterConfigurationModel import PrinterConfigurationModel
from ...UM3PrintJobOutputModel import UM3PrintJobOutputModel
from ...ConfigurationChangeModel import ConfigurationChangeModel
from ..CloudOutputController import CloudOutputController
from .BaseCloudModel import BaseCloudModel
from .CloudClusterBuildPlate import CloudClusterBuildPlate
from .CloudClusterPrintJobConfigurationChange import CloudClusterPrintJobConfigurationChange
from .CloudClusterPrintJobImpediment import CloudClusterPrintJobImpediment
from .CloudClusterPrintCoreConfiguration import CloudClusterPrintCoreConfiguration
from .CloudClusterPrintJobConstraint import CloudClusterPrintJobConstraints


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
    #  \param deleted_at: The time when this print job was deleted.
    #  \param printed_on_uuid: UUID of the printer used to print this job.
    #  \param configuration_changes_required: List of configuration changes the printer this job is associated with
    #       needs to make in order to be able to print this job
    #  \param build_plate: The build plate (type) this job needs to be printed on.
    #  \param compatible_machine_families: Family names of machines suitable for this print job
    #  \param impediments_to_printing: A list of reasons that prevent this job from being printed on the associated
    #       printer
    def __init__(self, created_at: str, force: bool, machine_variant: str, name: str, started: bool, status: str,
                 time_total: int, uuid: str,
                 configuration: List[Union[Dict[str, Any], CloudClusterPrintCoreConfiguration]],
                 constraints: List[Union[Dict[str, Any], CloudClusterPrintJobConstraints]],
                 last_seen: Optional[float] = None, network_error_count: Optional[int] = None,
                 owner: Optional[str] = None, printer_uuid: Optional[str] = None, time_elapsed: Optional[int] = None,
                 assigned_to: Optional[str] = None, deleted_at: Optional[str] = None,
                 printed_on_uuid: Optional[str] = None,
                 configuration_changes_required: List[
                     Union[Dict[str, Any], CloudClusterPrintJobConfigurationChange]] = None,
                 build_plate: Union[Dict[str, Any], CloudClusterBuildPlate] = None,
                 compatible_machine_families: List[str] = None,
                 impediments_to_printing: List[Union[Dict[str, Any], CloudClusterPrintJobImpediment]] = None,
                 **kwargs) -> None:
        self.assigned_to = assigned_to
        self.configuration = self.parseModels(CloudClusterPrintCoreConfiguration, configuration)
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
        self.deleted_at = deleted_at
        self.printed_on_uuid = printed_on_uuid

        self.configuration_changes_required = self.parseModels(CloudClusterPrintJobConfigurationChange,
                                                               configuration_changes_required) \
            if configuration_changes_required else []
        self.build_plate = self.parseModel(CloudClusterBuildPlate, build_plate) if build_plate else None
        self.compatible_machine_families = compatible_machine_families if compatible_machine_families else []
        self.impediments_to_printing = self.parseModels(CloudClusterPrintJobImpediment, impediments_to_printing) \
            if impediments_to_printing else []

        super().__init__(**kwargs)

    ## Creates an UM3 print job output model based on this cloud cluster print job.
    #  \param printer: The output model of the printer
    def createOutputModel(self, controller: CloudOutputController) -> UM3PrintJobOutputModel:
        model = UM3PrintJobOutputModel(controller, self.uuid, self.name)
        self.updateOutputModel(model)
        return model

    ## Creates a new configuration model
    def _createConfigurationModel(self) -> PrinterConfigurationModel:
        extruders = [extruder.createConfigurationModel() for extruder in self.configuration or ()]
        configuration = PrinterConfigurationModel()
        configuration.setExtruderConfigurations(extruders)
        return configuration

    ## Updates an UM3 print job output model based on this cloud cluster print job.
    #  \param model: The model to update.
    def updateOutputModel(self, model: UM3PrintJobOutputModel) -> None:
        model.updateConfiguration(self._createConfigurationModel())
        model.updateTimeTotal(self.time_total)
        model.updateTimeElapsed(self.time_elapsed)
        model.updateOwner(self.owner)
        model.updateState(self.status)
        model.setCompatibleMachineFamilies(self.compatible_machine_families)
        model.updateTimeTotal(self.time_total)
        model.updateTimeElapsed(self.time_elapsed)
        model.updateOwner(self.owner)

        status_set_by_impediment = False
        for impediment in self.impediments_to_printing:
            # TODO: impediment.severity is defined as int, this will not work, is there a translation?
            if impediment.severity == "UNFIXABLE":
                status_set_by_impediment = True
                model.updateState("error")
                break

        if not status_set_by_impediment:
            model.updateState(self.status)

        model.updateConfigurationChanges(
            [ConfigurationChangeModel(
                type_of_change = change.type_of_change,
                index = change.index if change.index else 0,
                target_name = change.target_name if change.target_name else "",
                origin_name = change.origin_name if change.origin_name else "")
                for change in self.configuration_changes_required])
