# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Settings.SQLQueryFactory import SQLQueryFactory, metadata_type
from UM.Settings.DatabaseContainerMetadataController import DatabaseMetadataContainerController
from UM.Settings.InstanceContainer import InstanceContainer


class QualityDatabaseHandler(DatabaseMetadataContainerController):
    """The Database handler for Quality containers"""

    def __init__(self):
        super().__init__(SQLQueryFactory(table = "quality",
                                         fields = {
                                             "id": "text",
                                             "name": "text",
                                             "quality_type": "text",
                                             "material": "text",
                                             "variant": "text",
                                             "global_quality": "bool",
                                             "definition": "text",
                                             "version": "text",
                                             "setting_version": "text"
                                         }))
        self._container_type = InstanceContainer

    def groomMetadata(self, metadata: metadata_type) -> metadata_type:
        """
        Ensures that the metadata is in the order of the field keys and has the right size.
        if the metadata doesn't contains a key which is stored in the DB it will add it as
        an empty string. Key, value pairs that are not stored in the DB are dropped.
        If the `global_quality` isn't set it well default to 'False'

        :param metadata: The container metadata
        """
        if "global_quality" not in metadata:
            metadata["global_quality"] = "False"
        return super().groomMetadata(metadata)
