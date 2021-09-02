from UM.Settings.SQLQueryFactory import SQLQueryFactory
from UM.Settings.DatabaseContainerMetadataController import DatabaseMetadataContainerController


class IntentDatabaseHandler(DatabaseMetadataContainerController):
    """The Database handler for Intent containers"""

    def __init__(self) -> None:
        super().__init__(SQLQueryFactory(table = "intents",
                                         fields = {
                                             "name": "text",
                                             "quality_type": "text",
                                             "intent_category": "text",
                                             "variant": "text",
                                             "definition": "text",
                                             "material": "text",
                                             "version": "text",
                                             "setting_version": "text"
                                         }))
