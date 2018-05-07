# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import os
from datetime import datetime
from typing import Optional
from zipfile import ZipFile, ZIP_DEFLATED, BadZipfile

from UM.Logger import Logger
from UM.Resources import Resources
from cura.CuraApplication import CuraApplication


class Backup:
    """
    The backup class holds all data about a backup.
    It is also responsible for reading and writing the zip file to the user data folder.
    """

    def __init__(self, zip_file: "ZipFile" = None, meta_data: dict = None):
        self.zip_file = zip_file  # type: Optional[ZipFile]
        self.meta_data = meta_data  # type: Optional[dict

    def makeFromCurrent(self) -> (bool, Optional[str]):
        """
        Create a backup from the current user config folder.
        """
        cura_release = CuraApplication.getInstance().getVersion()
        version_data_dir = Resources.getDataStoragePath()
        timestamp = datetime.now().isoformat()

        Logger.log("d", "Creating backup for Cura %s, using folder %s", cura_release, version_data_dir)

        # We're using an easy to parse filename for when we're restoring edge cases:
        # TIMESTAMP.backup.VERSION.cura.zip
        archive = self._makeArchive("{}.backup.{}.cura.zip".format(timestamp, cura_release), version_data_dir)

        self.zip_file = archive
        self.meta_data = {
            "cura_release": cura_release
        }
        # TODO: fill meta data with machine/material/etc counts.

    @staticmethod
    def _makeArchive(root_path: str, archive_name: str) -> Optional[ZipFile]:
        """
        Make a full archive from the given root path with the given name.
        :param root_path: The root directory to archive recursively.
        :param archive_name: The name of the archive to create.
        :return: The archive as ZipFile.
        """
        parent_folder = os.path.dirname(root_path)
        contents = os.walk(root_path)
        try:
            archive = ZipFile(archive_name, "w", ZIP_DEFLATED)
            for root, folders, files in contents:
                for folder_name in folders:
                    # Add all folders, even empty ones.
                    absolute_path = os.path.join(root, folder_name)
                    relative_path = absolute_path.replace(parent_folder + '\\', '')
                    archive.write(absolute_path, relative_path)
                for file_name in files:
                    # Add all files.
                    absolute_path = os.path.join(root, file_name)
                    relative_path = absolute_path.replace(parent_folder + '\\', '')
                    archive.write(absolute_path, relative_path)
            archive.close()
            return archive
        except (IOError, OSError, BadZipfile) as error:
            Logger.log("e", "Could not create archive from user data directory: %s", error)
            return None

    def restore(self) -> None:
        """
        Restore this backup.
        """
        if not self.zip_file or not self.meta_data or not self.meta_data.get("cura_release", None):
            # We can restore without the minimum required information.
            Logger.log("w", "Tried to restore a Cura backup without having proper data or meta data.")
            return

        # global_data_dir = os.path.dirname(version_data_dir)
        # TODO: restore logic.
