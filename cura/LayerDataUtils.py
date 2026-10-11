# Copyright (c) 2026 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Iterable

import numpy


def has_printed_layer(layer, non_printing_types: Iterable[int]) -> bool:
    """Return whether a layer contains a printable path with positive height."""
    if layer is None or layer.height <= 0:
        return False

    non_printing_types = set(non_printing_types)
    return any(
        any(line_type not in non_printing_types for line_type in numpy.asarray(polygon.types).ravel())
        for polygon in layer.polygons
    )
