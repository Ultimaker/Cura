# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from collections import namedtuple

ClusterMaterial = namedtuple('ClusterMaterial', [
    'guid',
    'material',
    'brand',
    'version',
    'color',
    'density'
])

LocalMaterial = namedtuple('LocalMaterial', [
    'GUID',
    'id',
    'type',
    'status',
    'base_file',
    'setting_version',
    'version',
    'name',
    'brand',
    'material',
    'color_name',
    'color_code',
    'description',
    'adhesion_info',
    'approximate_diameter',
    'properties',
    'definition',
    'compatible'
])
