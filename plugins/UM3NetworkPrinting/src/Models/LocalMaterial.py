# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from .BaseModel import BaseModel


class LocalMaterial(BaseModel):

    def __init__(self, GUID: str, id: str, version: int, **kwargs) -> None:
        self.GUID = GUID  # type: str
        self.id = id  # type: str
        self.version = version  # type: int
        super().__init__(**kwargs)

    def validate(self) -> None:
        super().validate()
        if not self.GUID:
            raise ValueError("guid is required on LocalMaterial")
        if not self.version:
            raise ValueError("version is required on LocalMaterial")
        if not self.id:
            raise ValueError("id is required on LocalMaterial")
