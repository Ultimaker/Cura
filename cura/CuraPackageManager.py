# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, List, Tuple, TYPE_CHECKING, Optional, Generator

from cura.CuraApplication import CuraApplication #To find some resource types.
from cura.Settings.GlobalStack import GlobalStack

from UM.PackageManager import PackageManager #The class we're extending.
from UM.Resources import Resources #To find storage paths for some resource types.
from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

if TYPE_CHECKING:
    from UM.Qt.QtApplication import QtApplication
    from PyQt5.QtCore import QObject


class CuraPackageManager(PackageManager):
    def __init__(self, application: "QtApplication", parent: Optional["QObject"] = None) -> None:
        super().__init__(application, parent)
        self._locally_installed_packages = None
        self.installedPackagesChanged.connect(self._updateLocallyInstalledPackages)

    def _updateLocallyInstalledPackages(self):
        self._locally_installed_packages = list(self.iterateAllLocalPackages())

    @property
    def locally_installed_packages(self):
        """locally installed packages, lazy execution"""
        if self._locally_installed_packages is None:
            self._updateLocallyInstalledPackages()
        return self._locally_installed_packages

    @locally_installed_packages.setter
    def locally_installed_packages(self, value):
        self._locally_installed_packages = value

    def initialize(self) -> None:
        self._installation_dirs_dict["materials"] = Resources.getStoragePath(CuraApplication.ResourceTypes.MaterialInstanceContainer)
        self._installation_dirs_dict["qualities"] = Resources.getStoragePath(CuraApplication.ResourceTypes.QualityInstanceContainer)

        super().initialize()

    def getMachinesUsingPackage(self, package_id: str) -> Tuple[List[Tuple[GlobalStack, str, str]], List[Tuple[GlobalStack, str, str]]]:
        """Returns a list of where the package is used

        It loops through all the package contents and see if some of the ids are used.

        :param package_id: package id to search for
        :return: empty if it is never used, otherwise a list consisting of 3-tuples
        """

        ids = self.getPackageContainerIds(package_id)
        container_stacks = self._application.getContainerRegistry().findContainerStacks()
        global_stacks = [container_stack for container_stack in container_stacks if isinstance(container_stack, GlobalStack)]
        machine_with_materials = []
        machine_with_qualities = []
        for container_id in ids:
            for global_stack in global_stacks:
                for extruder_nr, extruder_stack in enumerate(global_stack.extruderList):
                    if container_id in (extruder_stack.material.getId(), extruder_stack.material.getMetaData().get("base_file")):
                        machine_with_materials.append((global_stack, str(extruder_nr), container_id))
                    if container_id == extruder_stack.quality.getId():
                        machine_with_qualities.append((global_stack, str(extruder_nr), container_id))

        return machine_with_materials, machine_with_qualities

    def iterateAllLocalPackages(self) -> Generator[Dict[str, Any], None, None]:
        """ A generator which returns an unordered list of all the PackageModels"""
        handled_packages = {}

        for packages in self.getAllInstalledPackagesInfo().values():
            for package_info in packages:
                handled_packages.add(package_info["package_id"])
                yield package_info

        # Get all to be removed package_info's. These packages are still used in the current session so the user might
        # still want to interact with these.
        for package_data in self.getPackagesToRemove().values():
            if not package_data["package_info"]["package_id"] in handled_packages:
                handled_packages.add(package_data["package_info"]["package_id"])
                yield package_data["package_info"]

        # Get all to be installed package_info's. Since the user might want to interact with these
        for package_data in self.getPackagesToInstall().values():
            if not package_data["package_info"]["package_id"] in handled_packages:
                handled_packages.add(package_data["package_info"]["package_id"])
                yield package_data["package_info"]
