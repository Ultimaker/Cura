# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import NamedTuple

ClusterMaterial = NamedTuple("ClusterMaterial", [
    ("guid", str),
    ("material", str),
    ("brand", str),
    ("version", int),
    ("color", str),
    ("density", str),
])

LocalMaterial = NamedTuple("LocalMaterial", [
    ("GUID", str),
    ("id", str),
    ("type", str),
    ("status", str),
    ("base_file", str),
    ("setting_version", int),
    ("version", int),
    ("name", str),
    ("brand", str),
    ("material", str),
    ("color_name", str),
    ("color_code", str),
    ("description", str),
    ("adhesion_info", str),
    ("approximate_diameter", str),
    ("properties", str),
    ("definition", str),
    ("compatible", str),
])
