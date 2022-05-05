# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, cast, Dict, List, Set, Tuple, TYPE_CHECKING, Optional

from cura.CuraApplication import CuraApplication  # To find some resource types.
from cura.Settings.GlobalStack import GlobalStack

from UM.PackageManager import PackageManager  # The class we're extending.
from UM.Resources import Resources  # To find storage paths for some resource types.
from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

if TYPE_CHECKING:
    from UM.Qt.QtApplication import QtApplication
    from PyQt6.QtCore import QObject


class CuraPackageManager(PackageManager):
    def __init__(self, application: "QtApplication", parent: Optional["QObject"] = None) -> None:
        super().__init__(application, parent)
        self._local_packages: Optional[List[Dict[str, Any]]] = None
        self._local_packages_ids: Optional[Set[str]] = None
        self.installedPackagesChanged.connect(self._updateLocalPackages)

    def _updateLocalPackages(self) -> None:
        self._local_packages = self.getAllLocalPackages()
        self._local_packages_ids = set(pkg["package_id"] for pkg in self._local_packages)

    @property
    def local_packages(self) -> List[Dict[str, Any]]:
        """locally installed packages, lazy execution"""
        if self._local_packages is None:
            self._updateLocalPackages()
            # _updateLocalPackages always results in a list of packages, not None.
            # It's guaranteed to be a list now.
        return cast(List[Dict[str, Any]], self._local_packages)

    @property
    def local_packages_ids(self) -> Set[str]:
        """locally installed packages, lazy execution"""
        if self._local_packages_ids is None:
            self._updateLocalPackages()
            # _updateLocalPackages always results in a list of packages, not None.
            # It's guaranteed to be a list now.
        return cast(Set[str], self._local_packages_ids)

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

    def getAllLocalPackages(self) -> List[Dict[str, Any]]:
        """ Returns an unordered list of all the package_info of installed, to be installed, or bundled packages"""
        packages: List[Dict[str, Any]] = []

        for packages_to_add in self.getAllInstalledPackagesInfo().values():
            packages.extend(packages_to_add)

        return packages
