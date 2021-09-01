from typing import Generator

from UM.Settings.SQLQueryFactory import SQLQueryFactory, metadata_type
from UM.Settings.DatabaseContainerMetadataController import DatabaseMetadataContainerController
from UM.Settings.InstanceContainer import InstanceContainer


class QualityDatabaseHandler(DatabaseMetadataContainerController):
    """The Database handler for Quality containers"""

    def __init__(self):
        super().__init__(SQLQueryFactory(table = "qualities",
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
        self.container_type = InstanceContainer

    def groomMetadata(self, metadata: metadata_type) -> metadata_type:
        if "global_quality" not in metadata:
            metadata["global_quality"] = "False"
        return super().groomMetadata(metadata)
