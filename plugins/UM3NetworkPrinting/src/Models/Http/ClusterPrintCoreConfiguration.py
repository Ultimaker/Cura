# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Union, Dict, Optional, Any

from cura.PrinterOutput.Models.ExtruderConfigurationModel import ExtruderConfigurationModel
from cura.PrinterOutput.Models.ExtruderOutputModel import ExtruderOutputModel

from .ClusterPrinterConfigurationMaterial import ClusterPrinterConfigurationMaterial
from ..BaseModel import BaseModel


class ClusterPrintCoreConfiguration(BaseModel):
    """Class representing a cloud cluster printer configuration
    
    Also used for representing slots in a Material Station (as from Cura's perspective these are the same).
    """

    def __init__(self, extruder_index: int, material: Union[None, Dict[str, Any],
                 ClusterPrinterConfigurationMaterial] = None, print_core_id: Optional[str] = None, **kwargs) -> None:
        """Creates a new cloud cluster printer configuration object
        
        :param extruder_index: The position of the extruder on the machine as list index. Numbered from left to right.
        :param material: The material of a configuration object in a cluster printer. May be in a dict or an object.
        :param nozzle_diameter: The diameter of the print core at this position in millimeters, e.g. '0.4'.
        :param print_core_id: The type of print core inserted at this position, e.g. 'AA 0.4'.
        """

        self.extruder_index = extruder_index
        self.material = self.parseModel(ClusterPrinterConfigurationMaterial, material) if material else None
        self.print_core_id = print_core_id
        super().__init__(**kwargs)

    def updateOutputModel(self, model: ExtruderOutputModel) -> None:
        """Updates the given output model.
        
        :param model: The output model to update.
        """

        if self.print_core_id is not None:
            model.updateHotendID(self.print_core_id)

        if self.material:
            active_material = model.activeMaterial
            if active_material is None or active_material.guid != self.material.guid:
                material = self.material.createOutputModel()
                model.updateActiveMaterial(material)
        else:
            model.updateActiveMaterial(None)

    def createConfigurationModel(self) -> ExtruderConfigurationModel:
        """Creates a configuration model"""

        model = ExtruderConfigurationModel(position = self.extruder_index)
        self.updateConfigurationModel(model)
        return model

    def updateConfigurationModel(self, model: ExtruderConfigurationModel) -> ExtruderConfigurationModel:
        """Creates a configuration model"""

        model.setHotendID(self.print_core_id)
        if self.material:
            model.setMaterial(self.material.createOutputModel())
        return model
