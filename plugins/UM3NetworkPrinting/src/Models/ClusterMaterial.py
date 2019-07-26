##  Class representing a material that was fetched from the cluster API.
from plugins.UM3NetworkPrinting.src.Models.BaseModel import BaseModel


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
