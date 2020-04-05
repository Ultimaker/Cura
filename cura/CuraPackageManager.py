# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import List, Tuple, TYPE_CHECKING, Optional

from cura.CuraApplication import CuraApplication #To find some resource types.
from cura.Settings.GlobalStack import GlobalStack

from UM.PackageManager import PackageManager #The class we're extending.
from UM.Resources import Resources #To find storage paths for some resource types.

if TYPE_CHECKING:
    from UM.Qt.QtApplication import QtApplication
    from PyQt5.QtCore import QObject


class CuraPackageManager(PackageManager):
    def __init__(self, application: "QtApplication", parent: Optional["QObject"] = None) -> None:
        super().__init__(application, parent)

    def initialize(self) -> None:
        self._installation_dirs_dict["materials"] = Resources.getStoragePath(CuraApplication.ResourceTypes.MaterialInstanceContainer)
        self._installation_dirs_dict["qualities"] = Resources.getStoragePath(CuraApplication.ResourceTypes.QualityInstanceContainer)

        super().initialize()

    ##  Returns a list of where the package is used
    #   empty if it is never used.
    #   It loops through all the package contents and see if some of the ids are used.
    #   The list consists of 3-tuples: (global_stack, extruder_nr, container_id)
    def getMachinesUsingPackage(self, package_id: str) -> Tuple[List[Tuple[GlobalStack, str, str]], List[Tuple[GlobalStack, str, str]]]:
        ids = self.getPackageContainerIds(package_id)
        container_stacks = self._application.getContainerRegistry().findContainerStacks()
        global_stacks = [container_stack for container_stack in container_stacks if isinstance(container_stack, GlobalStack)]
        machine_with_materials = []
        machine_with_qualities = []
        for container_id in ids:
            for global_stack in global_stacks:
                for extruder_nr, extruder_stack in global_stack.extruders.items():
                    if container_id in (extruder_stack.material.getId(), extruder_stack.material.getMetaData().get("base_file")):
                        machine_with_materials.append((global_stack, extruder_nr, container_id))
                    if container_id == extruder_stack.quality.getId():
                        machine_with_qualities.append((global_stack, extruder_nr, container_id))

        return machine_with_materials, machine_with_qualities
