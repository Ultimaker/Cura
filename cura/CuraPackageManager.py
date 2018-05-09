# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional, Dict, Any
import json
import os
import shutil
import zipfile
import tempfile

from PyQt5.QtCore import pyqtSlot, QObject, pyqtSignal

from UM.Application import Application
from UM.Logger import Logger
from UM.Resources import Resources
from UM.Version import Version

class CuraPackageManager(QObject):
    Version = 1

    # The prefix that's added to all files for an installed package to avoid naming conflicts with user created files.
    PREFIX_PLACE_HOLDER = "-CP;"

    def __init__(self, parent = None):
        super().__init__(parent)

        self._application = Application.getInstance()
        self._container_registry = self._application.getContainerRegistry()
        self._plugin_registry = self._application.getPluginRegistry()

        # JSON file that keeps track of all installed packages.
        self._bundled_package_management_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "resources",
            "packages.json"
        )
        self._user_package_management_file_path = os.path.join(
            os.path.abspath(Resources.getDataStoragePath()),
            "packages.json"
        )

        self._bundled_package_dict = {}     # A dict of all bundled packages
        self._installed_package_dict = {}   # A dict of all installed packages
        self._to_remove_package_set = set() # A set of packages that need to be removed at the next start
        self._to_install_package_dict = {}  # A dict of packages that need to be installed at the next start

    installedPackagesChanged = pyqtSignal() # Emitted whenever the installed packages collection have been changed.

    def initialize(self):
        self._loadManagementData()
        self._removeAllScheduledPackages()
        self._installAllScheduledPackages()

    # (for initialize) Loads the package management file if exists
    def _loadManagementData(self) -> None:
        # The bundles package management file should always be there
        if not os.path.exists(self._bundled_package_management_file_path):
            Logger.log("w", "Bundled package management file could not be found!")
            return
        # Load the bundled packages:
        with open(self._bundled_package_management_file_path, "r", encoding = "utf-8") as f:
            self._bundled_package_dict = json.load(f, encoding = "utf-8")
            Logger.log("i", "Loaded bundled packages data from %s", self._bundled_package_management_file_path)

        # Load the user package management file
        if not os.path.exists(self._user_package_management_file_path):
            Logger.log("i", "User package management file %s doesn't exist, do nothing", self._user_package_management_file_path)
            return

        # Need to use the file lock here to prevent concurrent I/O from other processes/threads
        container_registry = self._application.getContainerRegistry()
        with container_registry.lockFile():

            # Load the user packages:
            with open(self._user_package_management_file_path, "r", encoding="utf-8") as f:
                management_dict = json.load(f, encoding="utf-8")
                self._installed_package_dict = management_dict.get("installed", {})
                self._to_remove_package_set = set(management_dict.get("to_remove", []))
                self._to_install_package_dict = management_dict.get("to_install", {})
                Logger.log("i", "Loaded user packages management file from %s", self._user_package_management_file_path)

    def _saveManagementData(self) -> None:
        # Need to use the file lock here to prevent concurrent I/O from other processes/threads
        container_registry = self._application.getContainerRegistry()
        with container_registry.lockFile():
            with open(self._user_package_management_file_path, "w", encoding = "utf-8") as f:
                data_dict = {"version": CuraPackageManager.Version,
                             "installed": self._installed_package_dict,
                             "to_remove": list(self._to_remove_package_set),
                             "to_install": self._to_install_package_dict}
                data_dict["to_remove"] = list(data_dict["to_remove"])
                json.dump(data_dict, f, sort_keys = True, indent = 4)
                Logger.log("i", "Package management file %s was saved", self._user_package_management_file_path)

    # (for initialize) Removes all packages that have been scheduled to be removed.
    def _removeAllScheduledPackages(self) -> None:
        for package_id in self._to_remove_package_set:
            self._purgePackage(package_id)
        self._to_remove_package_set.clear()
        self._saveManagementData()

    # (for initialize) Installs all packages that have been scheduled to be installed.
    def _installAllScheduledPackages(self) -> None:

        while self._to_install_package_dict:
            package_id, package_info = list(self._to_install_package_dict.items())[0]
            self._installPackage(package_info)
            self._installed_package_dict[package_id] = self._to_install_package_dict[package_id]
            del self._to_install_package_dict[package_id]
            self._saveManagementData()

    # Checks the given package is installed. If so, return a dictionary that contains the package's information.
    def getInstalledPackageInfo(self, package_id: str) -> Optional[dict]:
        if package_id in self._to_remove_package_set:
            return None

        if package_id in self._to_install_package_dict:
            package_info = self._to_install_package_dict[package_id]["package_info"]
            return package_info

        if package_id in self._installed_package_dict:
            package_info = self._installed_package_dict[package_id]["package_info"]
            return package_info

        if package_id in self._bundled_package_dict:
            package_info = self._bundled_package_dict[package_id]["package_info"]
            return package_info

        return None

    def getAllInstalledPackagesInfo(self) -> dict:

        # Add bundled, installed, and to-install packages to the set of installed package IDs
        all_installed_ids = set()

        if self._bundled_package_dict.keys():
            all_installed_ids = all_installed_ids.union(set(self._bundled_package_dict.keys()))
        if self._installed_package_dict.keys():
            all_installed_ids = all_installed_ids.union(set(self._installed_package_dict.keys()))
        if self._to_install_package_dict.keys():
            all_installed_ids = all_installed_ids.union(set(self._to_install_package_dict.keys()))
        all_installed_ids = all_installed_ids.difference(self._to_remove_package_set)

        # map of <package_type> -> <package_id> -> <package_info>
        installed_packages_dict = {}
        for package_id in all_installed_ids:

            # Skip required plugins as they should not be tampered with
            if package_id in Application.getInstance().getRequiredPlugins():
                continue

            # Add bundled plugins
            if package_id in self._bundled_package_dict:
                package_info = self._bundled_package_dict[package_id]["package_info"]

            # Add installed plugins
            if package_id in self._installed_package_dict:
                package_info = self._installed_package_dict[package_id]["package_info"]

            # Add to install plugins
            if package_id in self._to_install_package_dict:
                package_info = self._to_install_package_dict[package_id]["package_info"]

            # We also need to get information from the plugin registry such as if a plugin is active
            if package_info["package_type"] == "plugin":
                package_info["is_active"] = self._plugin_registry.isActivePlugin(package_id)
            else:
                package_info["is_active"] = self._plugin_registry.isActivePlugin(package_id)

            # If the package ID is in bundled, label it as such
            if package_info["package_id"] in self._bundled_package_dict.keys():
                package_info["is_bundled"] = True
            else:
                package_info["is_bundled"] = False

            # If there is not a section in the dict for this type, add it
            if package_info["package_type"] not in installed_packages_dict:
                installed_packages_dict[package_info["package_type"]] = []
                
            # Finally, add the data
            installed_packages_dict[package_info["package_type"]].append( package_info )

        return installed_packages_dict

    def __convertPluginMetadataToPackageMetadata(self, plugin_metadata: dict) -> dict:
        package_metadata = {
            "package_id": plugin_metadata["id"],
            "package_type": "plugin",
            "display_name": plugin_metadata["plugin"]["name"],
            "description": plugin_metadata["plugin"].get("description"),
            "package_version": plugin_metadata["plugin"]["version"],
            "cura_version": int(plugin_metadata["plugin"]["api"]),
            "website": "",
            "author_id": plugin_metadata["plugin"].get("author", "UnknownID"),
            "author": {
                "author_id": plugin_metadata["plugin"].get("author", "UnknownID"),
                "display_name": plugin_metadata["plugin"].get("author", ""),
                "email": "",
                "website": "",
            },
            "tags": ["plugin"]
        }
        return package_metadata

    # Checks if the given package is installed.
    def isPackageInstalled(self, package_id: str) -> bool:
        return self.getInstalledPackageInfo(package_id) is not None

    # Schedules the given package file to be installed upon the next start.
    @pyqtSlot(str)
    def installPackage(self, filename: str) -> None:
        has_changes = False
        try:
            # Get package information
            package_info = self.getPackageInfo(filename)
            if not package_info:
                return
            package_id = package_info["package_id"]

            # Check the delayed installation and removal lists first
            if package_id in self._to_remove_package_set:
                self._to_remove_package_set.remove(package_id)
                has_changes = True

            # Check if it is installed
            installed_package_info = self.getInstalledPackageInfo(package_info["package_id"])
            to_install_package = installed_package_info is None  # Install if the package has not been installed
            if installed_package_info is not None:
                # Compare versions and only schedule the installation if the given package is newer
                new_version = package_info["package_version"]
                installed_version = installed_package_info["package_version"]
                if Version(new_version) > Version(installed_version):
                    Logger.log("i", "Package [%s] version [%s] is newer than the installed version [%s], update it.",
                               package_id, new_version, installed_version)
                    to_install_package = True

            if to_install_package:
                # Need to use the lock file to prevent concurrent I/O issues.
                with self._container_registry.lockFile():
                    Logger.log("i", "Package [%s] version [%s] is scheduled to be installed.",
                               package_id, package_info["package_version"])
                    # Copy the file to cache dir so we don't need to rely on the original file to be present
                    package_cache_dir = os.path.join(os.path.abspath(Resources.getCacheStoragePath()), "cura_packages")
                    if not os.path.exists(package_cache_dir):
                        os.makedirs(package_cache_dir, exist_ok=True)

                    target_file_path = os.path.join(package_cache_dir, package_id + ".curapackage")
                    shutil.copy2(filename, target_file_path)

                    self._to_install_package_dict[package_id] = {"package_info": package_info,
                                                                 "filename": target_file_path}
                    has_changes = True
        except:
            Logger.logException("c", "Failed to install package file '%s'", filename)
        finally:
            self._saveManagementData()
            if has_changes:
                self.installedPackagesChanged.emit()

    # Schedules the given package to be removed upon the next start.
    @pyqtSlot(str)
    def removePackage(self, package_id: str) -> None:
        # Check the delayed installation and removal lists first
        if not self.isPackageInstalled(package_id):
            Logger.log("i", "Attempt to remove package [%s] that is not installed, do nothing.", package_id)
            return

        # Remove from the delayed installation list if present
        if package_id in self._to_install_package_dict:
            del self._to_install_package_dict[package_id]

        # Schedule for a delayed removal:
        self._to_remove_package_set.add(package_id)

        self._saveManagementData()
        self.installedPackagesChanged.emit()

    # Removes everything associated with the given package ID.
    def _purgePackage(self, package_id: str) -> None:
        # Iterate through all directories in the data storage directory and look for sub-directories that belong to
        # the package we need to remove, that is the sub-dirs with the package_id as names, and remove all those dirs.
        data_storage_dir = os.path.abspath(Resources.getDataStoragePath())

        for root, dir_names, _ in os.walk(data_storage_dir):
            for dir_name in dir_names:
                package_dir = os.path.join(root, dir_name, package_id)
                if os.path.exists(package_dir):
                    Logger.log("i", "Removing '%s' for package [%s]", package_dir, package_id)
                    shutil.rmtree(package_dir)
            break

    # Installs all files associated with the given package.
    def _installPackage(self, installation_package_data: dict):
        package_info = installation_package_data["package_info"]
        filename = installation_package_data["filename"]

        package_id = package_info["package_id"]

        if not os.path.exists(filename):
            Logger.log("w", "Package [%s] file '%s' is missing, cannot install this package", package_id, filename)
            return

        Logger.log("i", "Installing package [%s] from file [%s]", package_id, filename)

        # If it's installed, remove it first and then install
        if package_id in self._installed_package_dict:
            self._purgePackage(package_id)

        # Install the package
        with zipfile.ZipFile(filename, "r") as archive:

            temp_dir = tempfile.TemporaryDirectory()
            archive.extractall(temp_dir.name)

            from cura.CuraApplication import CuraApplication
            installation_dirs_dict = {
                "materials": Resources.getStoragePath(CuraApplication.ResourceTypes.MaterialInstanceContainer),
                "quality": Resources.getStoragePath(CuraApplication.ResourceTypes.QualityInstanceContainer),
                "plugins": os.path.abspath(Resources.getStoragePath(Resources.Plugins)),
            }

            for sub_dir_name, installation_root_dir in installation_dirs_dict.items():
                src_dir_path = os.path.join(temp_dir.name, "files", sub_dir_name)
                dst_dir_path = os.path.join(installation_root_dir, package_id)

                if not os.path.exists(src_dir_path):
                    continue

                # Need to rename the container files so they don't get ID conflicts
                to_rename_files = sub_dir_name not in ("plugins",)
                self.__installPackageFiles(package_id, src_dir_path, dst_dir_path, need_to_rename_files= to_rename_files)

        # Remove the file
        os.remove(filename)

    def __installPackageFiles(self, package_id: str, src_dir: str, dst_dir: str, need_to_rename_files: bool = True) -> None:
        shutil.move(src_dir, dst_dir)

        # Rename files if needed
        if not need_to_rename_files:
            return
        for root, _, file_names in os.walk(dst_dir):
            for filename in file_names:
                new_filename = self.PREFIX_PLACE_HOLDER + package_id + "-" + filename
                old_file_path = os.path.join(root, filename)
                new_file_path = os.path.join(root, new_filename)
                os.rename(old_file_path, new_file_path)

    # Gets package information from the given file.
    def getPackageInfo(self, filename: str) -> Dict[str, Any]:
        with zipfile.ZipFile(filename) as archive:
            try:
                # All information is in package.json
                with archive.open("package.json") as f:
                    package_info_dict = json.loads(f.read().decode("utf-8"))
                    return package_info_dict
            except Exception as e:
                Logger.logException("w", "Could not get package information from file '%s': %s" % (filename, e))
                return {}

    # Gets the license file content if present in the given package file.
    # Returns None if there is no license file found.
    def getPackageLicense(self, filename: str) -> Optional[str]:
        license_string = None
        with zipfile.ZipFile(filename) as archive:
            # Go through all the files and use the first successful read as the result
            for file_info in archive.infolist():
                is_dir = lambda file_info: file_info.filename.endswith('/')
                if is_dir or not file_info.filename.startswith("files/"):
                    continue

                filename_parts = os.path.basename(file_info.filename.lower()).split(".")
                stripped_filename = filename_parts[0]
                if stripped_filename in ("license", "licence"):
                    Logger.log("d", "Found potential license file '%s'", file_info.filename)
                    try:
                        with archive.open(file_info.filename, "r") as f:
                            data = f.read()
                        license_string = data.decode("utf-8")
                        break
                    except:
                        Logger.logException("e", "Failed to load potential license file '%s' as text file.",
                                            file_info.filename)
                        license_string = None
        return license_string
