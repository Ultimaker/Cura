# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional, List

import uuid

from .CloudClusterResponse import CloudClusterResponse
from .ClusterPrinterStatus import ClusterPrinterStatus


class CloudClusterWithConfigResponse(CloudClusterResponse):
    """Class representing a cloud connected cluster."""

    def __init__(self, **kwargs) -> None:
        self.configuration = self.parseModel(ClusterPrinterStatus, kwargs.get("host_printer"))

        # Some printers will return a null UUID in the host_printer.uuid field. For those we can fall back using
        # the host_guid field of the cluster data
        valid_uuid = False
        try:
            parsed_uuid = uuid.UUID(self.configuration.uuid)
            valid_uuid = parsed_uuid.int != 0
        except:
            pass

        if not valid_uuid:
            try:
                self.configuration.uuid = kwargs.get("host_guid")
            except:
                pass

        super().__init__(**kwargs)
