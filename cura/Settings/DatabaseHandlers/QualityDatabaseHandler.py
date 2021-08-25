from UM.Settings.DatabaseContainerMetadataController import DatabaseMetadataContainerController
from UM.Settings.InstanceContainer import InstanceContainer


class QualityDatabaseHandler(DatabaseMetadataContainerController):
    def __init__(self) -> None:
        super().__init__(
            insert_query = """  INSERT INTO qualities (id, name, quality_type, material, variant, global_quality, definition, version, setting_version) 
                                VALUES (?, ?, ? ,?, ?, ?, ?, ?, ?)""",
            update_query = """  UPDATE qualities
                                SET name = ?,
                                    quality_type = ?,
                                    material = ?,
                                    variant = ?,
                                    global_quality = ?,
                                    definition = ?,
                                    version = ?,
                                    setting_version = ?
                                WHERE id = ?
                            """,
            select_query = "SELECT * FROM qualities where id = ?",
            table_query = """CREATE TABLE qualities
                (
                    id text,
                    name text,
                    quality_type text,
                    material text,
                    variant text,
                    global_quality bool,
                    definition text,
                    version text,
                    setting_version text
                );
                CREATE UNIQUE INDEX idx_qualities_id on qualities (id);"""
        )

    def _convertMetadataToUpdateBatch(self, metadata):
        return self._convertMetadataToInsertBatch(metadata)[1:]

    def _convertRawDataToMetadata(self, data):
        return {"id": data[0], "name": data[1], "quality_type": data[2], "material": data[3], "variant": data[4],
                "global_quality": data[5], "definition": data[6], "container_type": InstanceContainer,
                "version": data[7], "setting_version": data[8], "type": "quality"}

    def _convertMetadataToInsertBatch(self, metadata):
        global_quality = False
        if "global_quality" in metadata:
            global_quality = metadata["global_quality"]
        material = ""
        if "material" in metadata:
            material = metadata["material"]
        variant = ""
        if "variant" in metadata:
            variant = metadata["variant"]

        return metadata["id"], metadata["name"], metadata["quality_type"], material, variant, global_quality, metadata["definition"], metadata["version"], metadata["setting_version"]


