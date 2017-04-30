# Copyright (c) 2017 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.InstanceContainer import InstanceContainer
from cura.MachineAction import MachineAction
from PyQt5.QtCore import pyqtSlot, pyqtSignal, pyqtProperty

from UM.i18n import i18nCatalog
from UM.Application import Application
catalog = i18nCatalog("cura")

import UM.Settings.InstanceContainer


##  The Ultimaker 2 can have a few revisions & upgrades.
class UM2UpgradeSelection(MachineAction):
    def __init__(self):
        super().__init__("UM2UpgradeSelection", catalog.i18nc("@action", "Select upgrades"))
        self._qml_url = "UM2UpgradeSelectionMachineAction.qml"

        self._container_registry = ContainerRegistry.getInstance()

    def _reset(self):
        self.hasVariantsChanged.emit()

    hasVariantsChanged = pyqtSignal()

    @pyqtProperty(bool, notify = hasVariantsChanged)
    def hasVariants(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            return global_container_stack.getMetaDataEntry("has_variants", "false") == "True"

    @pyqtSlot(bool)
    def setHasVariants(self, has_variants = True):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            variant_container = global_container_stack.findContainer({"type": "variant"})
            variant_index = global_container_stack.getContainerIndex(variant_container)

            if has_variants:
                if "has_variants" in global_container_stack.getMetaData():
                    global_container_stack.setMetaDataEntry("has_variants", True)
                else:
                    global_container_stack.addMetaDataEntry("has_variants", True)

                # Set the variant container to a sane default
                if variant_container.getId() == "empty_variant":
                    search_criteria = { "type": "variant", "definition": "ultimaker2", "id": "*0.4*" }
                    containers = self._container_registry.findInstanceContainers(**search_criteria)
                    if containers:
                        global_container_stack.replaceContainer(variant_index, containers[0])
            else:
                # The metadata entry is stored in an ini, and ini files are parsed as strings only.
                # Because any non-empty string evaluates to a boolean True, we have to remove the entry to make it False.
                if "has_variants" in global_container_stack.getMetaData():
                    global_container_stack.removeMetaDataEntry("has_variants")

                # Set the variant container to an empty variant
                if variant_container.getId() == "empty_variant":
                    global_container_stack.replaceContainer(variant_index, self._container_registry.findInstanceContainers(id="empty_variant")[0])

            Application.getInstance().globalContainerStackChanged.emit()
