# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Union, Dict, Optional

from cura.PrinterOutput.ExtruderConfigurationModel import ExtruderConfigurationModel
from cura.PrinterOutput.ExtruderOutputModel import ExtruderOutputModel
from .CloudClusterPrinterConfigurationMaterial import CloudClusterPrinterConfigurationMaterial
from .BaseCloudModel import BaseCloudModel


##  Class representing a cloud cluster printer configuration
#  Spec: https://api-staging.ultimaker.com/connect/v1/spec
class CloudClusterPrinterConfiguration(BaseCloudModel):
    ## Creates a new cloud cluster printer configuration object
    #  \param extruder_index: The position of the extruder on the machine as list index. Numbered from left to right.
    #  \param material: The material of a configuration object in a cluster printer. May be in a dict or an object.
    #  \param nozzle_diameter: The diameter of the print core at this position in millimeters, e.g. '0.4'.
    #  \param print_core_id: The type of print core inserted at this position, e.g. 'AA 0.4'.
    def __init__(self, extruder_index: int,
                 material: Union[None, Dict[str, any], CloudClusterPrinterConfigurationMaterial],
                 nozzle_diameter: Optional[str] = None, print_core_id: Optional[str] = None, **kwargs) -> None:
        self.extruder_index = extruder_index
        self.material = self.parseModel(CloudClusterPrinterConfigurationMaterial, material)
        self.nozzle_diameter = nozzle_diameter
        self.print_core_id = print_core_id
        super().__init__(**kwargs)

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
