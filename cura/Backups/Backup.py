# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import io
import os
import re
import shutil
from zipfile import ZipFile, ZIP_DEFLATED, BadZipfile
from typing import Dict, Optional, TYPE_CHECKING

from UM import i18nCatalog
from UM.Logger import Logger
from UM.Message import Message
from UM.Platform import Platform
from UM.Resources import Resources

if TYPE_CHECKING:
    from cura.CuraApplication import CuraApplication


##  The back-up class holds all data about a back-up.
#
#   It is also responsible for reading and writing the zip file to the user data
#   folder.
class Backup:
    # These files should be ignored when making a backup.
    IGNORED_FILES = [r"cura\.log", r"plugins\.json", r"cache", r"__pycache__", r"\.qmlc", r"\.pyc"]

    # Re-use translation catalog.
    catalog = i18nCatalog("cura")

    def __init__(self, application: "CuraApplication", zip_file: bytes = None, meta_data: Dict[str, str] = None) -> None:
        self._application = application
        self.zip_file = zip_file  # type: Optional[bytes]
        self.meta_data = meta_data  # type: Optional[Dict[str, str]]

    ##  Create a back-up from the current user config folder.
    def makeFromCurrent(self) -> None:
        cura_release = self._application.getVersion()
        version_data_dir = Resources.getDataStoragePath()

        Logger.log("d", "Creating backup for Cura %s, using folder %s", cura_release, version_data_dir)

        # Ensure all current settings are saved.
        self._application.saveSettings()

        # We copy the preferences file to the user data directory in Linux as it's in a different location there.
        # When restoring a backup on Linux, we move it back.
        if Platform.isLinux(): #TODO: This should check for the config directory not being the same as the data directory, rather than hard-coding that to Linux systems.
            preferences_file_name = self._application.getApplicationName()
            preferences_file = Resources.getPath(Resources.Preferences, "{}.cfg".format(preferences_file_name))
            backup_preferences_file = os.path.join(version_data_dir, "{}.cfg".format(preferences_file_name))
            if os.path.exists(preferences_file) and (not os.path.exists(backup_preferences_file) or not os.path.samefile(preferences_file, backup_preferences_file)):
                Logger.log("d", "Copying preferences file from %s to %s", preferences_file, backup_preferences_file)
                shutil.copyfile(preferences_file, backup_preferences_file)

        # Create an empty buffer and write the archive to it.
        buffer = io.BytesIO()
        archive = self._makeArchive(buffer, version_data_dir)
        if archive is None:
            return
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

    ##  Make a full archive from the given root path with the given name.
    #   \param root_path The root directory to archive recursively.
    #   \return The archive as bytes.
    def _makeArchive(self, buffer: "io.BytesIO", root_path: str) -> Optional[ZipFile]:
        ignore_string = re.compile("|".join(self.IGNORED_FILES))
        try:
            archive = ZipFile(buffer, "w", ZIP_DEFLATED)
            for root, folders, files in os.walk(root_path):
                for item_name in folders + files:
                    absolute_path = os.path.join(root, item_name)
                    if ignore_string.search(absolute_path):
                        continue
                    archive.write(absolute_path, absolute_path[len(root_path) + len(os.sep):])
            archive.close()
            return archive
        except (IOError, OSError, BadZipfile) as error:
            Logger.log("e", "Could not create archive from user data directory: %s", error)
            self._showMessage(
                self.catalog.i18nc("@info:backup_failed",
                                   "Could not create archive from user data directory: {}".format(error)))
            return None

    ##  Show a UI message.
    def _showMessage(self, message: str) -> None:
        Message(message, title=self.catalog.i18nc("@info:title", "Backup"), lifetime=30).show()

    ##  Restore this back-up.
    #   \return Whether we had success or not.
    def restore(self) -> bool:
        if not self.zip_file or not self.meta_data or not self.meta_data.get("cura_release", None):
            # We can restore without the minimum required information.
            Logger.log("w", "Tried to restore a Cura backup without having proper data or meta data.")
            self._showMessage(
                self.catalog.i18nc("@info:backup_failed",
                                   "Tried to restore a Cura backup without having proper data or meta data."))
            return False

        current_version = self._application.getVersion()
        version_to_restore = self.meta_data.get("cura_release", "master")

        if current_version < version_to_restore:
            # Cannot restore version newer than current because settings might have changed.
            Logger.log("d", "Tried to restore a Cura backup of version {version_to_restore} with cura version {current_version}".format(version_to_restore = version_to_restore, current_version = current_version))
            self._showMessage(
                self.catalog.i18nc("@info:backup_failed",
                                   "Tried to restore a Cura backup that is higher than the current version."))
            return False

        version_data_dir = Resources.getDataStoragePath()
        archive = ZipFile(io.BytesIO(self.zip_file), "r")
        extracted = self._extractArchive(archive, version_data_dir)

        # Under Linux, preferences are stored elsewhere, so we copy the file to there.
        if Platform.isLinux():
            preferences_file_name = self._application.getApplicationName()
            preferences_file = Resources.getPath(Resources.Preferences, "{}.cfg".format(preferences_file_name))
            backup_preferences_file = os.path.join(version_data_dir, "{}.cfg".format(preferences_file_name))
            Logger.log("d", "Moving preferences file from %s to %s", backup_preferences_file, preferences_file)
            shutil.move(backup_preferences_file, preferences_file)

        return extracted

    ##  Extract the whole archive to the given target path.
    #   \param archive The archive as ZipFile.
    #   \param target_path The target path.
    #   \return Whether we had success or not.
    @staticmethod
    def _extractArchive(archive: "ZipFile", target_path: str) -> bool:

        # Implement security recommendations: Sanity check on zip files will make it harder to spoof.
        from cura.CuraApplication import CuraApplication
        config_filename = CuraApplication.getInstance().getApplicationName() + ".cfg"  # Should be there if valid.
        if config_filename not in [file.filename for file in archive.filelist]:
            Logger.logException("e", "Unable to extract the backup due to corruption of compressed file(s).")
            return False

        Logger.log("d", "Removing current data in location: %s", target_path)
        Resources.factoryReset()
        Logger.log("d", "Extracting backup to location: %s", target_path)
        try:
            archive.extractall(target_path)
        except PermissionError:
            Logger.logException("e", "Unable to extract the backup due to permission errors")
            return False
        return True
