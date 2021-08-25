from UM.Settings.DatabaseContainerMetadataController import DatabaseMetadataContainerController
from UM.Settings.InstanceContainer import InstanceContainer


class VariantDatabaseHandler(DatabaseMetadataContainerController):
    def __init__(self) -> None:
        super().__init__(
            insert_query = """INSERT INTO variants (id, name, hardware_type, definition, version, setting_version) 
                             VALUES (?, ?, ?, ?, ?, ?)""",
            update_query = """  UPDATE variants
                                SET name = ?,
                                    hardware_type = ?,
                                    definition = ?,
                                    version = ?,
                                    setting_version = ?
                                WHERE id = ?
                           """,
            select_query= "SELECT * FROM variants where id = ?",
            table_query = """CREATE TABLE variants
                (
                    id text,
                    name text,
                    hardware_type text,
                    definition text,
                    version text,
                    setting_version text
                );
                CREATE UNIQUE INDEX idx_variants_id on variants (id);"""
        )

    def _convertMetadataToUpdateBatch(self, metadata):
        return self._convertMetadataToInsertBatch(metadata)[1:]

    def _convertRawDataToMetadata(self, data):
        return {"id": data[0], "name": data[1], "hardware_type": data[2], "definition": data[3], "container_type": InstanceContainer, "version": data[4], "setting_version": data[5], "type": "variant"}

    def _convertMetadataToInsertBatch(self, metadata):
        return metadata["id"], metadata["name"], metadata["hardware_type"], metadata["definition"], metadata["version"], \
               metadata["setting_version"]
