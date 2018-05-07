# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.


class Backup:
    """
    The backup class holds all data about a backup.
    It is also responsible for reading and writing the zip file to the user data folder.
    """

    def __init__(self):
        self.generated = False  # type: bool
        self.backup_id = None  # type: str
        self.target_cura_version = None  # type: str
        self.zip_file = None
        self.meta_data = None  # type: dict

    def getZipFile(self):
        pass

    def getMetaData(self):
        pass

    def create(self):
        self.generated = True
        pass

    def restore(self):
        pass
