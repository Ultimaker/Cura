# Copyright (c) 2018 Ultimaker B.V.
# Uranium is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtSignal, pyqtProperty

from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.i18n import i18nCatalog
from UM.Application import Application
from UM.Util import parseBool

from cura.MachineAction import MachineAction

catalog = i18nCatalog("cura")


##  The Ultimaker 2 can have a few revisions & upgrades.
class UM2UpgradeSelection(MachineAction):
    def __init__(self):
        super().__init__("UM2UpgradeSelection", catalog.i18nc("@action", "Select upgrades"))
        self._qml_url = "UM2UpgradeSelectionMachineAction.qml"

        self._container_registry = ContainerRegistry.getInstance()

        self._current_global_stack = None

        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalStackChanged)
        self._reset()

    def _reset(self):
        self.hasVariantsChanged.emit()

    def _onGlobalStackChanged(self):
        if self._current_global_stack:
            self._current_global_stack.metaDataChanged.disconnect(self._onGlobalStackMetaDataChanged)

        self._current_global_stack = Application.getInstance().getGlobalContainerStack()
        if self._current_global_stack:
            self._current_global_stack.metaDataChanged.connect(self._onGlobalStackMetaDataChanged)
        self._reset()

    def _onGlobalStackMetaDataChanged(self):
        self._reset()

    hasVariantsChanged = pyqtSignal()

    def setHasVariants(self, has_variants = True):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            variant_container = global_container_stack.extruders["0"].variant

            if has_variants:
                global_container_stack.setMetaDataEntry("has_variants", True)

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
            self._reset()

    @pyqtProperty(bool, fset = setHasVariants, notify = hasVariantsChanged)
    def hasVariants(self):
        if self._current_global_stack:
            return parseBool(self._current_global_stack.getMetaDataEntry("has_variants", "false"))
