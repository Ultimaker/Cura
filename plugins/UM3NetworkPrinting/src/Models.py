# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.


## Base model that maps kwargs to instance attributes.
class BaseModel:
    def __init__(self, **kwargs) -> None:
        self.__dict__.update(kwargs)
        self.validate()

    # Validates the model, raising an exception if the model is invalid.
    def validate(self) -> None:
        pass


##  Class representing a material that was fetched from the cluster API.
class ClusterMaterial(BaseModel):
    def __init__(self, guid: str, version: int, **kwargs) -> None:
        self.guid = guid  # type: str
        self.version = version  # type: int
        super().__init__(**kwargs)

    def validate(self) -> None:
        if not self.guid:
            raise ValueError("guid is required on ClusterMaterial")
        if not self.version:
            raise ValueError("version is required on ClusterMaterial")


##  Class representing a local material that was fetched from the container registry.
class LocalMaterial(BaseModel):
    def __init__(self, GUID: str, id: str, version: int, **kwargs) -> None:
        self.GUID = GUID  # type: str
        self.id = id  # type: str
        self.version = version  # type: int
        super().__init__(**kwargs)

    #
    def validate(self) -> None:
        super().validate()
        if not self.GUID:
            raise ValueError("guid is required on LocalMaterial")
        if not self.version:
            raise ValueError("version is required on LocalMaterial")
        if not self.id:
            raise ValueError("id is required on LocalMaterial")
