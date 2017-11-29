# Copyright (c) 2017 Ultimaker B.V.
# Uranium is released under the terms of the LGPLv3 or higher.

from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.InstanceContainer import InstanceContainer
from cura.MachineAction import MachineAction
from PyQt5.QtCore import pyqtSlot, pyqtSignal, pyqtProperty

from UM.i18n import i18nCatalog
from UM.Application import Application
from UM.Util import parseBool
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
            return parseBool(global_container_stack.getMetaDataEntry("has_variants", "false"))

    @pyqtSlot(bool)
    def setHasVariants(self, has_variants = True):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            variant_container = global_container_stack.extruders["0"].variant

            if has_variants:
                if "has_variants" in global_container_stack.getMetaData():
                    global_container_stack.setMetaDataEntry("has_variants", True)
                else:
                    global_container_stack.addMetaDataEntry("has_variants", True)

                # Set the variant container to a sane default
                empty_container = ContainerRegistry.getInstance().getEmptyInstanceContainer()
                if type(variant_container) == type(empty_container):
                    search_criteria = { "type": "variant", "definition": "ultimaker2", "id": "*0.4*" }
                    containers = self._container_registry.findInstanceContainers(**search_criteria)
                    if containers:
                        global_container_stack.extruders["0"].variant = containers[0]
            else:
                # The metadata entry is stored in an ini, and ini files are parsed as strings only.
                # Because any non-empty string evaluates to a boolean True, we have to remove the entry to make it False.
                if "has_variants" in global_container_stack.getMetaData():
                    global_container_stack.removeMetaDataEntry("has_variants")

                # Set the variant container to an empty variant
                global_container_stack.extruders["0"].variant = ContainerRegistry.getInstance().getEmptyInstanceContainer()

            Application.getInstance().globalContainerStackChanged.emit()
