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
    IGNORED_FILES = {"cura.log", "cache"}

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

        # Create an empty buffer and write the archive to it.
        buffer = io.BytesIO()
        archive = self._makeArchive(buffer, version_data_dir)
        files = archive.namelist()
        
        # Count the metadata items. We do this in a rather naive way at the moment.
        machine_count = len([s for s in files if "machine_instances/" in s]) - 1
        material_count = len([s for s in files if "materials/" in s]) - 1
        profile_count = len([s for s in files if "quality_changes/" in s]) - 1
        plugin_count = len([s for s in files if "plugin.json" in s])
        
        # Store the archive and metadata so the BackupManager can fetch them when needed.
        self.zip_file = buffer.getvalue()
        self.meta_data = {
            "cura_release": cura_release,
            "machine_count": str(machine_count),
            "material_count": str(material_count),
            "profile_count": str(profile_count),
            "plugin_count": str(plugin_count)
        }

    def _makeArchive(self, buffer: "io.BytesIO", root_path: str) -> Optional[ZipFile]:
        """
        Make a full archive from the given root path with the given name.
        :param root_path: The root directory to archive recursively.
        :return: The archive as bytes.
        """
        contents = os.walk(root_path)
        try:
            archive = ZipFile(buffer, "w", ZIP_DEFLATED)
            for root, folders, files in contents:
                for folder_name in folders:
                    if folder_name in self.IGNORED_FILES:
                        continue
                    absolute_path = os.path.join(root, folder_name)
                    relative_path = absolute_path[len(root_path) + len(os.sep):]
                    archive.write(absolute_path, relative_path)
                for file_name in files:
                    if file_name in self.IGNORED_FILES:
                        continue
                    absolute_path = os.path.join(root, file_name)
                    relative_path = absolute_path[len(root_path) + len(os.sep):]
                    archive.write(absolute_path, relative_path)
            archive.close()
            return archive
        except (IOError, OSError, BadZipfile) as error:
            Logger.log("e", "Could not create archive from user data directory: %s", error)
            # TODO: show message.
            return None

    def restore(self) -> bool:
        """
        Restore this backups
        :return: A boolean whether we had success or not.
        """
        if not self.zip_file or not self.meta_data or not self.meta_data.get("cura_release", None):
            # We can restore without the minimum required information.
            Logger.log("w", "Tried to restore a Cura backup without having proper data or meta data.")
            # TODO: show message.
            return False

        # TODO: handle restoring older data version.
        # global_data_dir = os.path.dirname(version_data_dir)

        version_data_dir = Resources.getDataStoragePath()
        archive = ZipFile(io.BytesIO(self.zip_file), "r")
        extracted = self._extractArchive(archive, version_data_dir)
        return extracted

    @staticmethod
    def _extractArchive(archive: "ZipFile", target_path: str) -> bool:
        """
        Extract the whole archive to the given target path.
        :param archive: The archive as ZipFile.
        :param target_path: The target path.
        :return: A boolean whether we had success or not.
        """
        Logger.log("d", "Removing current data in location: %s", target_path)
        shutil.rmtree(target_path)
        Logger.log("d", "Extracting backup to location: %s", target_path)
        archive.extractall(target_path)
        return True
