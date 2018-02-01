# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.



class XmlMaterialValidator():

    @classmethod
    def validateMaterialMetaDate(cls, validation_metadata):

        if validation_metadata.get("GUID") is None:
            return "Missing GUID"

        if validation_metadata.get("brand") is None:
            return "Missing Brand"

        if validation_metadata.get("material") is None:
            return "Missing Material"

        if validation_metadata.get("version") is None:
            return "Missing Version"

        if validation_metadata.get("description") is None:
            return "Missing Description"

        if validation_metadata.get("adhesion_info") is None:
            return "Missing Adhesion Info"

        return None


