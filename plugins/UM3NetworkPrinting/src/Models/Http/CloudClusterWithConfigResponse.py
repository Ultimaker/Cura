# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional, List

from .CloudClusterResponse import CloudClusterResponse
from .ClusterPrinterStatus import ClusterPrinterStatus


class CloudClusterWithConfigResponse(CloudClusterResponse):
    """Class representing a cloud connected cluster."""

    def __init__(self, **kwargs) -> None:
        self.configuration = self.parseModel(ClusterPrinterStatus, kwargs.get("host_printer"))
        super().__init__(**kwargs)
