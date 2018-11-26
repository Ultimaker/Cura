# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.


## Base model that maps kwargs to instance attributes.
class BaseModel:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.validate()

    def validate(self):
        pass


##  Class representing a material that was fetched from the cluster API.
class ClusterMaterial(BaseModel):
    def __init__(self, **kwargs):
        self.guid = None  # type: str
        self.material = None  # type: str
        self.brand = None  # type: str
        self.version = None  # type: int
        self.color = None  # type: str
        self.density = None  # type: str
        super().__init__(**kwargs)

    def validate(self):
        if not self.guid:
            raise ValueError("guid is required on ClusterMaterial")


##  Class representing a local material that was fetched from the container registry.
class LocalMaterial(BaseModel):
    def __init__(self, **kwargs):
        self.GUID = None  # type: str
        self.id = None  # type: str
        self.type = None  # type: str
        self.status = None  # type: str
        self.base_file = None  # type: str
        self.setting_version = None  # type: int
        self.version = None  # type: int
        self.brand = None  # type: str
        self.material = None  # type: str
        self.color_name = None  # type: str
        self.color_code = None  # type: str
        self.description = None  # type: str
        self.adhesion_info = None  # type: str
        self.approximate_diameter = None  # type: str
        self.definition = None  # type: str
        self.compatible = None  # type: bool
        super().__init__(**kwargs)

    def validate(self):
        if not self.GUID:
            raise ValueError("guid is required on LocalMaterial")
        if not self.id:
            raise ValueError("id is required on LocalMaterial")
