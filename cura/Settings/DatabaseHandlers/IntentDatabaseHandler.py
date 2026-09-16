# Copyright (c) 2023 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Settings.SQLQueryFactory import SQLQueryFactory
from UM.Settings.DatabaseContainerMetadataController import DatabaseMetadataContainerController
from UM.Settings.InstanceContainer import InstanceContainer


class IntentDatabaseHandler(DatabaseMetadataContainerController):
    """The Database handler for Intent containers"""

    def __init__(self) -> None:
        super().__init__(SQLQueryFactory(table="intent",
                                         fields={
                                             "id": "text",
                                             "name": "text",
                                             "quality_type": "text",
                                             "intent_category": "text",
                                             "variant": "text",
                                             "definition": "text",
                                             "material": "text",
                                             "version": "text",
                                             "setting_version": "text",
                                             "icon": "text",
                                             "description": "text",
                                         }))
        self._container_type = InstanceContainer
