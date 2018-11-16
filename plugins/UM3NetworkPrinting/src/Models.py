# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional


class BaseModel:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__ if type(self) == type(other) else False


##  Represents an item in the cluster API response for installed materials.
class ClusterMaterial(BaseModel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.version = int(self.version)
        self.density = float(self.density)

    guid: None  # type: Optional[str]

    material: None  # type: Optional[str]

    brand: None  # type: Optional[str]

    version = None  # type: Optional[int]

    color: None  # type: Optional[str]

    density: None  # type: Optional[float]


class LocalMaterialProperties(BaseModel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.density = float(self.density)
        self.diameter = float(self.diameter)
        self.weight = float(self.weight)

    density: None  # type: Optional[float]

    diameter: None  # type: Optional[float]

    weight: None  # type: Optional[int]


class LocalMaterial(BaseModel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.properties = LocalMaterialProperties(**self.properties)
        self.approximate_diameter = float(self.approximate_diameter)
        self.version = int(self.version)

    GUID: None  # type: Optional[str]

    id: None  # type: Optional[str]

    type: None  # type: Optional[str]

    status: None  # type: Optional[str]

    base_file: None  # type: Optional[str]

    setting_version: None  # type: Optional[str]

    version = None  # type: Optional[int]

    name: None  # type: Optional[str]

    brand: None  # type: Optional[str]

    material: None  # type: Optional[str]

    color_name: None  # type: Optional[str]

    description: None  # type: Optional[str]

    adhesion_info: None  # type: Optional[str]

    approximate_diameter: None  # type: Optional[float]

    properties: None  # type: LocalMaterialProperties

    definition: None  # type: Optional[str]

    compatible: None  # type: Optional[bool]
