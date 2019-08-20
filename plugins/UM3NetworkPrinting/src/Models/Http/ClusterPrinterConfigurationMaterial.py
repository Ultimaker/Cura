# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional

from UM.Settings.ContainerRegistry import ContainerRegistry
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

    ##  Creates a material output model based on this cloud printer material.
    #
    #   A material is chosen that matches the current GUID. If multiple such
    #   materials are available, read-only materials are preferred and the
    #   material with the earliest alphabetical name will be selected.
    #   \return A material output model that matches the current GUID.
    def createOutputModel(self) -> MaterialOutputModel:
        container_registry = ContainerRegistry.getInstance()
        same_guid = container_registry.findInstanceContainersMetadata(GUID = self.guid)
        if same_guid:
            read_only = sorted(filter(lambda metadata: container_registry.isReadOnly(metadata["id"]), same_guid), key = lambda metadata: metadata["name"])
            if read_only:
                material_metadata = read_only[0]
            else:
                material_metadata = min(same_guid, key = lambda metadata: metadata["name"])
        else:
            material_metadata = {
                "color_code": self.color,
                "brand": self.brand,
                "material": self.material,
                "name": "Empty" if self.material == "empty" else "Unknown"
            }

        return MaterialOutputModel(guid = self.guid, type = material_metadata["material"], brand = material_metadata["brand"], color = material_metadata["color_code"], name = material_metadata["name"])
