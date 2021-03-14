# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict


class XmlMaterialValidator:
    """Makes sure that the required metadata is present for a material."""

    @classmethod
    def validateMaterialMetaData(cls, validation_metadata: Dict[str, Any]):
        """Makes sure that the required metadata is present for a material."""


        if validation_metadata.get("GUID") is None:
            return "Missing GUID"

        if validation_metadata.get("brand") is None:
            return "Missing Brand"

        if validation_metadata.get("material") is None:
            return "Missing Material"

        if validation_metadata.get("version") is None:
            return "Missing Version"

        return None


