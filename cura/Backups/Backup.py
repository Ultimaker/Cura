# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import io
import os
import shutil

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

    # These files should be ignored when making a backup.
    IGNORED_FILES = {"cura.log"}

    def __init__(self, zip_file: bytes = None, meta_data: dict = None):
        self.zip_file = zip_file  # type: Optional[bytes]
        self.meta_data = meta_data  # type: Optional[dict]

    def makeFromCurrent(self) -> (bool, Optional[str]):
        """
        Create a backup from the current user config folder.
        """
        cura_release = CuraApplication.getInstance().getVersion()
        version_data_dir = Resources.getDataStoragePath()

        Logger.log("d", "Creating backup for Cura %s, using folder %s", cura_release, version_data_dir)

        # Ensure all current settings are saved.
        CuraApplication.getInstance().saveSettings()

        # We're using an easy to parse filename for when we're restoring edge cases:
        # TIMESTAMP.backup.VERSION.cura.zip
        archive = self._makeArchive(version_data_dir)

        self.zip_file = archive
        self.meta_data = {
            "cura_release": cura_release,
            "machine_count": 0,
            "material_count": 0,
            "profile_count": 0,
            "plugin_count": 0
        }
        # TODO: fill meta data with real machine/material/etc counts.

    def _makeArchive(self, root_path: str) -> Optional[bytes]:
        """
        Make a full archive from the given root path with the given name.
        :param root_path: The root directory to archive recursively.
        :return: The archive as bytes.
        """
        contents = os.walk(root_path)
        try:
            buffer = io.BytesIO()
            archive = ZipFile(buffer, "w", ZIP_DEFLATED)
            for root, folders, files in contents:
                for folder_name in folders:
                    # Add all folders, even empty ones.
                    absolute_path = os.path.join(root, folder_name)
                    relative_path = absolute_path[len(root_path) + len(os.sep):]
                    archive.write(absolute_path, relative_path)
                for file_name in files:
                    # Add all files except the ignored ones.
                    if file_name in self.IGNORED_FILES:
                        continue
                    absolute_path = os.path.join(root, file_name)
                    relative_path = absolute_path[len(root_path) + len(os.sep):]
                    archive.write(absolute_path, relative_path)
            archive.close()
            return buffer.getvalue()
        except (IOError, OSError, BadZipfile) as error:
            Logger.log("e", "Could not create archive from user data directory: %s", error)
            return None

    def restore(self) -> bool:
        """
        Restore this backup.
        """
        if not self.zip_file or not self.meta_data or not self.meta_data.get("cura_release", None):
            # We can restore without the minimum required information.
            Logger.log("w", "Tried to restore a Cura backup without having proper data or meta data.")
            return False

        # global_data_dir = os.path.dirname(version_data_dir)
        # TODO: handle restoring older data version.

        version_data_dir = Resources.getDataStoragePath()
        archive = ZipFile(io.BytesIO(self.zip_file), "r")
        extracted = self._extractArchive(archive, version_data_dir)
        if not extracted:
            return False
        return True

    @staticmethod
    def _extractArchive(archive: "ZipFile", target_path: str) -> bool:
        Logger.log("d", "Removing current data in location: %s", target_path)
        shutil.rmtree(target_path)

        Logger.log("d", "Extracting backup to location: %s", target_path)
        archive.extractall(target_path)

        return True
