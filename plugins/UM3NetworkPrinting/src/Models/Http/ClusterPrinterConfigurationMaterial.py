# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional

from cura.CuraApplication import CuraApplication
from cura.PrinterOutput.Models.MaterialOutputModel import MaterialOutputModel

from ..BaseModel import BaseModel


## Class representing a cloud cluster printer configuration
class ClusterPrinterConfigurationMaterial(BaseModel):

    ## Creates a new material configuration model.
    #  \param brand: The brand of material in this print core, e.g. 'Ultimaker'.
    #  \param color: The color of material in this print core, e.g. 'Blue'.
    #  \param guid: he GUID of the material in this print core, e.g. '506c9f0d-e3aa-4bd4-b2d2-23e2425b1aa9'.
    #  \param material: The type of material in this print core, e.g. 'PLA'.
    def __init__(self, brand: Optional[str] = None, color: Optional[str] = None, guid: Optional[str] = None,
                 material: Optional[str] = None, **kwargs) -> None:
        self.guid = guid
        self.brand = brand
        self.color = color
        self.material = material
        super().__init__(**kwargs)

    ## Creates a material output model based on this cloud printer material.
    def createOutputModel(self) -> MaterialOutputModel:
        material_manager = CuraApplication.getInstance().getMaterialManager()
        material_group_list = material_manager.getMaterialGroupListByGUID(self.guid) or []

        # Sort the material groups by "is_read_only = True" first, and then the name alphabetically.
        read_only_material_group_list = list(filter(lambda x: x.is_read_only, material_group_list))
        non_read_only_material_group_list = list(filter(lambda x: not x.is_read_only, material_group_list))
        material_group = None
        if read_only_material_group_list:
            read_only_material_group_list = sorted(read_only_material_group_list, key = lambda x: x.name)
            material_group = read_only_material_group_list[0]
        elif non_read_only_material_group_list:
            non_read_only_material_group_list = sorted(non_read_only_material_group_list, key = lambda x: x.name)
            material_group = non_read_only_material_group_list[0]

        if material_group:
            container = material_group.root_material_node.getContainer()
            color = container.getMetaDataEntry("color_code")
            brand = container.getMetaDataEntry("brand")
            material_type = container.getMetaDataEntry("material")
            name = container.getName()
        else:
            color = self.color
            brand = self.brand
            material_type = self.material
            name = "Empty" if self.material == "empty" else "Unknown"

        return MaterialOutputModel(guid=self.guid, type=material_type, brand=brand, color=color, name=name)
