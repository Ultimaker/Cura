# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from cura.PrinterOutput.ExtruderConfigurationModel import ExtruderConfigurationModel
from cura.PrinterOutput.ExtruderOutputModel import ExtruderOutputModel
from .CloudClusterPrinterConfigurationMaterial import CloudClusterPrinterConfigurationMaterial
from .BaseCloudModel import BaseCloudModel


##  Class representing a cloud cluster printer configuration
class CloudClusterPrinterConfiguration(BaseCloudModel):
    def __init__(self, **kwargs) -> None:
        self.extruder_index = None  # type: int
        self.material = None  # type: CloudClusterPrinterConfigurationMaterial
        self.nozzle_diameter = None  # type: str
        self.print_core_id = None  # type: str
        super().__init__(**kwargs)

        if isinstance(self.material, dict):
            self.material = CloudClusterPrinterConfigurationMaterial(**self.material)

    ## Updates the given output model.
    #  \param model - The output model to update.
    def updateOutputModel(self, model: ExtruderOutputModel) -> None:
        model.updateHotendID(self.print_core_id)

        if model.activeMaterial is None or model.activeMaterial.guid != self.material.guid:
            material = self.material.createOutputModel()
            model.updateActiveMaterial(material)

    ## Creates a configuration model
    def createConfigurationModel(self) -> ExtruderConfigurationModel:
        model = ExtruderConfigurationModel(position = self.extruder_index)
        self.updateConfigurationModel(model)
        return model

    ## Creates a configuration model
    def updateConfigurationModel(self, model: ExtruderConfigurationModel) -> ExtruderConfigurationModel:
        model.setHotendID(self.print_core_id)
        if self.material:
            model.setMaterial(self.material.createOutputModel())
        return model
