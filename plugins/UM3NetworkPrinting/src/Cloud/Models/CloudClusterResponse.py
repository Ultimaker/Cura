# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional

from .BaseCloudModel import BaseCloudModel


##  Class representing a cloud connected cluster.
#  Spec: https://api-staging.ultimaker.com/connect/v1/spec
class CloudClusterResponse(BaseCloudModel):
    ## Creates a new cluster response object.
    #  \param cluster_id: The secret unique ID, e.g. 'kBEeZWEifXbrXviO8mRYLx45P8k5lHVGs43XKvRniPg='.
    #  \param host_guid: The unique identifier of the print cluster host, e.g. 'e90ae0ac-1257-4403-91ee-a44c9b7e8050'.
    #  \param host_name: The name of the printer as configured during the Wi-Fi setup. Used as identifier for end users.
    #  \param is_online: Whether this cluster is currently connected to the cloud.
    #  \param status: The status of the cluster authentication (active or inactive).
    #  \param host_version: The firmware version of the cluster host. This is where the Stardust client is running on.
    def __init__(self, cluster_id: str, host_guid: str, host_name: str, is_online: bool, status: str,
                 host_version: Optional[str] = None, **kwargs) -> None:
        self.cluster_id = cluster_id
        self.host_guid = host_guid
        self.host_name = host_name
        self.status = status
        self.is_online = is_online
        self.host_version = host_version
        super().__init__(**kwargs)

    # Validates the model, raising an exception if the model is invalid.
    def validate(self) -> None:
        super().validate()
        if not self.cluster_id:
            raise ValueError("cluster_id is required on CloudCluster")
