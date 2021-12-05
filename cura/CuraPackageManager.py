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
        self._local_packages: Optional[List[Dict[str, Any]]] = None
        self.installedPackagesChanged.connect(self._updateLocalPackages)

    def _updateLocalPackages(self) -> None:
        self._local_packages = self.getAllLocalPackages()

    @property
    def local_packages(self) -> List[Dict[str, Any]]:
        """locally installed packages, lazy execution"""
        if self._local_packages is None:
            self._updateLocalPackages()
        return self._local_packages

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
        """ returns an unordered list of all the package_info installed, to be installed or to be returned"""

        class PkgInfo:
            # Needed helper class because a dict isn't hashable
            def __init__(self, package_info):
                self._info = package_info

            def __eq__(self, item):
                return item == self._info["package_id"]

            def __repr__(self):
                return repr(self._info)

            def __iter__(self):
                for k, v in self._info.items():
                    yield k, v

            def asdict(self):
                return self._info

        packages = [PkgInfo(package_info) for package in self.getAllInstalledPackagesInfo().values() for package_info in package]
        packages.extend([PkgInfo(package["package_info"]) for package in self.getPackagesToRemove().values() if package["package_info"]["package_id"] not in packages])
        packages.extend([PkgInfo(package["package_info"]) for package in self.getPackagesToInstall().values() if package["package_info"]["package_id"] not in packages])

        return [dict(package) for package in packages]
