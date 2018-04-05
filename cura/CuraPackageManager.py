# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional, Dict
import json
import os
import re
import shutil
import urllib.parse
import zipfile

from PyQt5.QtCore import pyqtSlot, QObject, QUrl

from UM.Logger import Logger
from UM.MimeTypeDatabase import MimeTypeDatabase
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Resources import Resources


class CuraPackageManager(QObject):

    # The prefix that's added to all files for an installed package to avoid naming conflicts with user created
    # files.
    PREFIX_PLACE_HOLDER = "-CP;"

    def __init__(self, parent = None):
        super().__init__(parent)

        self._application = parent
        self._registry = self._application.getContainerRegistry()

        # The JSON file that keeps track of all installed packages.
        self._package_management_file_path = os.path.join(os.path.abspath(Resources.getDataStoragePath()),
                                                          "packages.json")
        self._installed_package_dict = {}  # type: Dict[str, dict]

        self._semantic_version_regex = re.compile(r"^[0-9]+(.[0-9]+)+$")

    def initialize(self):
        # Load the package management file if exists
        if os.path.exists(self._package_management_file_path):
            with open(self._package_management_file_path, "r", encoding = "utf-8") as f:
                self._installed_package_dict = json.loads(f.read(), encoding = "utf-8")
                Logger.log("i", "Package management file %s is loaded", self._package_management_file_path)

    def _saveManagementData(self):
        with open(self._package_management_file_path, "w", encoding = "utf-8") as f:
            json.dump(self._installed_package_dict, f)
            Logger.log("i", "Package management file %s is saved", self._package_management_file_path)

    @pyqtSlot(str, result = bool)
    def isPackageFile(self, file_name: str):
        extension = os.path.splitext(file_name)[1].strip(".")
        if extension.lower() in ("curapackage",):
            return True
        return False

    # Checks the given package is installed. If so, return a dictionary that contains the package's information.
    def getInstalledPackage(self, package_id: str) -> Optional[dict]:
        return self._installed_package_dict.get(package_id)

    # Gets all installed packages
    def getAllInstalledPackages(self) -> Dict[str, dict]:
        return self._installed_package_dict

    # Installs the given package file.
    @pyqtSlot(str)
    def install(self, file_name: str) -> None:
        file_url = QUrl(file_name)
        file_name = file_url.toLocalFile()

        archive = zipfile.ZipFile(file_name)

        # Get package information
        try:
            with archive.open("package.json", "r") as f:
                package_info_dict = json.loads(f.read(), encoding = "utf-8")
        except Exception as e:
            raise RuntimeError("Could not get package information from file '%s': %s" % (file_name, e))

        # Check if it is installed
        installed_package = self.getInstalledPackage(package_info_dict["package_id"])
        has_installed_version = installed_package is not None

        if has_installed_version:
            # Remove the existing package first
            Logger.log("i", "Another version of [%s] [%s] has already been installed, will overwrite it with version [%s]",
                       installed_package["package_id"], installed_package["package_version"],
                       package_info_dict["package_version"])
            self.remove(package_info_dict["package_id"])

        # Install the package
        self._installPackage(file_name, archive, package_info_dict)

        archive.close()

    def _installPackage(self, file_name: str, archive: zipfile.ZipFile, package_info_dict: dict):
        from cura.CuraApplication import CuraApplication

        package_id = package_info_dict["package_id"]
        package_type = package_info_dict["package_type"]
        if package_type == "material":
            package_root_dir = Resources.getPath(CuraApplication.ResourceTypes.MaterialInstanceContainer)
            material_class = self._registry.getContainerForMimeType(MimeTypeDatabase.getMimeType("application/x-ultimaker-material-profile"))
            file_extension = self._registry.getMimeTypeForContainer(material_class).preferredSuffix
        elif package_type == "quality":
            package_root_dir = Resources.getPath(CuraApplication.ResourceTypes.QualityInstanceContainer)
            file_extension = "." + self._registry.getMimeTypeForContainer(InstanceContainer).preferredSuffix
        else:
            raise RuntimeError("Unexpected package type [%s] in file [%s]" % (package_type, file_name))

        Logger.log("i", "Prepare package directory [%s]", package_root_dir)

        # get package directory
        package_installation_path = os.path.join(os.path.abspath(package_root_dir), package_id)
        if os.path.exists(package_installation_path):
            Logger.log("w", "Path [%s] exists, removing it.", package_installation_path)
            if os.path.isfile(package_installation_path):
                os.remove(package_installation_path)
            else:
                shutil.rmtree(package_installation_path, ignore_errors = True)

        os.makedirs(package_installation_path, exist_ok = True)

        # Only extract the needed files
        for file_info in archive.infolist():
            if file_info.is_dir():
                continue

            file_name = os.path.basename(file_info.filename)
            if not file_name.endswith(file_extension):
                continue

            # Generate new file name and save to file
            new_file_name = urllib.parse.quote_plus(self.PREFIX_PLACE_HOLDER + package_id + "-" + file_name)
            new_file_path = os.path.join(package_installation_path, new_file_name)
            with archive.open(file_info.filename, "r") as f:
                content = f.read()
                with open(new_file_path, "wb") as f2:
                    f2.write(content)

            Logger.log("i", "Installed package file to [%s]", new_file_name)

        self._installed_package_dict[package_id] = package_info_dict
        self._saveManagementData()
        Logger.log("i", "Package [%s] has been installed", package_id)

    # Removes a package with the given package ID.
    @pyqtSlot(str)
    def remove(self, package_id: str) -> None:
        from cura.CuraApplication import CuraApplication

        package_info_dict = self.getInstalledPackage(package_id)
        if package_info_dict is None:
            Logger.log("w", "Attempt to remove non-existing package [%s], do nothing.", package_id)
            return

        package_type = package_info_dict["package_type"]
        if package_type == "material":
            package_root_dir = Resources.getPath(CuraApplication.ResourceTypes.MaterialInstanceContainer)
        elif package_type == "quality":
            package_root_dir = Resources.getPath(CuraApplication.ResourceTypes.QualityInstanceContainer)
        else:
            raise RuntimeError("Unexpected package type [%s] for package [%s]" % (package_type, package_id))

        # Get package directory
        package_installation_path = os.path.join(os.path.abspath(package_root_dir), package_id)
        if os.path.exists(package_installation_path):
            if os.path.isfile(package_installation_path):
                os.remove(package_installation_path)
            else:
                shutil.rmtree(package_installation_path, ignore_errors=True)

        if package_id in self._installed_package_dict:
            del self._installed_package_dict[package_id]
        self._saveManagementData()
        Logger.log("i", "Package [%s] has been removed.", package_id)

    # Gets package information from the given file.
    def getPackageInfo(self, file_name: str) -> dict:
        archive = zipfile.ZipFile(file_name)
        try:
            # All information is in package.json
            with archive.open("package.json", "r") as f:
                package_info_dict = json.loads(f.read().decode("utf-8"))
                return package_info_dict
        except Exception as e:
            raise RuntimeError("Could not get package information from file '%s': %s" % (e, file_name))
        finally:
            archive.close()
