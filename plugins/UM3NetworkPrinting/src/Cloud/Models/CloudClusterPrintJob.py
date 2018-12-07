# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import List

from cura.PrinterOutput.ConfigurationModel import ConfigurationModel
from plugins.UM3NetworkPrinting.src.Cloud.CloudOutputController import CloudOutputController
from .CloudClusterPrinterConfiguration import CloudClusterPrinterConfiguration
from .CloudClusterPrintJobConstraint import CloudClusterPrintJobConstraint
from ...Models import BaseModel


##  Class representing a print job
from plugins.UM3NetworkPrinting.src.UM3PrintJobOutputModel import UM3PrintJobOutputModel


class CloudClusterPrintJob(BaseModel):
    def __init__(self, **kwargs) -> None:
        self.assigned_to = None  # type: str
        self.configuration = []  # type: List[CloudClusterPrinterConfiguration]
        self.constraints = []  # type: List[CloudClusterPrintJobConstraint]
        self.created_at = None  # type: str
        self.force = None  # type: str
        self.last_seen = None  # type: str
        self.machine_variant = None  # type: str
        self.name = None  # type: str
        self.network_error_count = None  # type: int
        self.owner = None  # type: str
        self.printer_uuid = None  # type: str
        self.started = None  # type: str
        self.status = None  # type: str
        self.time_elapsed = None  # type: str
        self.time_total = None  # type: str
        self.uuid = None  # type: str
        super().__init__(**kwargs)
        self.configuration = [CloudClusterPrinterConfiguration(**c) if isinstance(c, dict) else c
                              for c in self.configuration]
        self.constraints = [CloudClusterPrintJobConstraint(**p) if isinstance(p, dict) else p
                            for p in self.constraints]

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
