# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import List

from cura.PrinterOutput.ConfigurationModel import ConfigurationModel
from cura.PrinterOutput.PrinterOutputController import PrinterOutputController
from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel
from .CloudClusterPrinterConfiguration import CloudClusterPrinterConfiguration
from .BaseCloudModel import BaseCloudModel


##  Class representing a cluster printer
class CloudClusterPrinter(BaseCloudModel):
    def __init__(self, **kwargs) -> None:
        self.configuration = []  # type: List[CloudClusterPrinterConfiguration]
        self.enabled = None  # type: str
        self.firmware_version = None  # type: str
        self.friendly_name = None  # type: str
        self.ip_address = None  # type: str
        self.machine_variant = None  # type: str
        self.status = None  # type: str
        self.unique_name = None  # type: str
        self.uuid = None  # type: str
        super().__init__(**kwargs)

        self.configuration = [CloudClusterPrinterConfiguration(**c)
                              if isinstance(c, dict) else c for c in self.configuration]

    ## Creates a new output model.
    #  \param controller - The controller of the model.
    def createOutputModel(self, controller: PrinterOutputController) -> PrinterOutputModel:
        model = PrinterOutputModel(controller, len(self.configuration), firmware_version = self.firmware_version)
        self.updateOutputModel(model)
        return model

    ## Updates the given output model.
    #  \param model - The output model to update.
    def updateOutputModel(self, model: PrinterOutputModel) -> None:
        model.updateKey(self.uuid)
        model.updateName(self.friendly_name)
        model.updateType(self.machine_variant)
        model.updateState(self.status if self.enabled else "disabled")

        for configuration, extruder_output, extruder_config in \
                zip(self.configuration, model.extruders, model.printerConfiguration.extruderConfigurations):
            configuration.updateOutputModel(extruder_output)
            configuration.updateConfigurationModel(extruder_config)

        pass
