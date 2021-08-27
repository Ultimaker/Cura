from UM.Settings.DatabaseContainerMetadataController import DatabaseMetadataContainerController
from UM.Settings.InstanceContainer import InstanceContainer


class IntentDatabaseHandler(DatabaseMetadataContainerController):
    def __init__(self) -> None:
        super().__init__(
            insert_query = """  INSERT INTO intents (id, name, quality_type, intent_category, variant, definition, material, version, setting_version)
                                VALUES (?, ?, ? ,?, ?, ?, ?, ?, ?)""",
            update_query="""UPDATE intents
                            SET name = ?,
                                quality_type = ?,
                                intent_category = ?,
                                variant = ?,
                                definition = ?,
                                material = ?,
                                version = ?,
                                setting_version = ?
                            WHERE id = ?
                        """,
            select_query = "SELECT * FROM intents WHERE id = ?",
            delete_query = "DELETE FROM intents WHERE id = ?",
            table_query="""CREATE TABLE intents
               (
                   id text,
                   name text,
                   quality_type text,
                   intent_category text,
                   variant text,
                   definition text,
                   material text,
                   version text,
                   setting_version text
               );
               CREATE UNIQUE INDEX idx_intents_id on intents (id);"""
        )

    def _convertMetadataToUpdateBatch(self, metadata):
        return self._convertMetadataToInsertBatch(metadata)[1:]

    def _convertRawDataToMetadata(self, data):
        return {"id": data[0], "name": data[1], "quality_type": data[2], "intent_category": data[3], "variant": data[4], "definition": data[5], "container_type": InstanceContainer, "material": data[6], "version": data[7], "setting_version": data[8], "type": "intent"}

    def _convertMetadataToInsertBatch(self, metadata):
        return metadata["id"], metadata["name"], metadata["quality_type"], metadata["intent_category"], metadata[
            "variant"], metadata["definition"], metadata["material"], metadata["version"], metadata["setting_version"]



