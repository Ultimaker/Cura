# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from ...Models import BaseModel


##  Class representing a cloud connected cluster.
class CloudCluster(BaseModel):
    def __init__(self, **kwargs):
        self.cluster_id = None  # type: str
        self.host_guid = None  # type: str
        self.host_name = None  # type: str
        self.host_version = None  # type: str
        self.status = None  # type: str
        self.is_online = None  # type: bool
        super().__init__(**kwargs)

    # Validates the model, raising an exception if the model is invalid.
    def validate(self) -> None:
        super().validate()
        if not self.cluster_id:
            raise ValueError("cluster_id is required on CloudCluster")
