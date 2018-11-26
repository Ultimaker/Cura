# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from collections import namedtuple

Cluster = namedtuple("Cluster", [
    "cluster_id",            # Type: str
    "host_guid",             # Type: str
    "host_name",             # Type: str
    "host_version",          # Type: str
    "status",                # Type: str
])