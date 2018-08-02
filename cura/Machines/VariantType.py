# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from enum import Enum


class VariantType(Enum):
    BUILD_PLATE = "buildplate"
    NOZZLE = "nozzle"


ALL_VARIANT_TYPES = (VariantType.BUILD_PLATE, VariantType.NOZZLE)


__all__ = ["VariantType", "ALL_VARIANT_TYPES"]
