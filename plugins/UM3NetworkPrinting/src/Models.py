# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from collections import namedtuple

ClusterMaterial = namedtuple('ClusterMaterial', [
    'guid',      # Type: str
    'material',              # Type: str
    'brand',                 # Type: str
    'version',               # Type: int
    'color',                 # Type: str
    'density'                # Type: str
])

LocalMaterial = namedtuple('LocalMaterial', [
    'GUID',                  # Type: str
    'id',                    # Type: str
    'type',                  # Type: str
    'status',                # Type: str
    'base_file',             # Type: str
    'setting_version',       # Type: int
    'version',               # Type: int
    'name',                  # Type: str
    'brand',                 # Type: str
    'material',              # Type: str
    'color_name',            # Type: str
    'color_code',            # Type: str
    'description',           # Type: str
    'adhesion_info',         # Type: str
    'approximate_diameter',  # Type: str
    'properties',            # Type: str
    'definition',            # Type: str
    'compatible'             # Type: str
])
