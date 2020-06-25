# Copyright (c) 2017 Ultimaker B.V.
# Uranium is released under the terms of the LGPLv3 or higher.

from UM.Settings.ContainerRegistry import ContainerRegistry
from cura.MachineAction import MachineAction
from PyQt5.QtCore import pyqtSlot, pyqtSignal, pyqtProperty

from UM.i18n import i18nCatalog
from UM.Application import Application
catalog = i18nCatalog("cura")

from cura.Settings.CuraStackBuilder import CuraStackBuilder


class UMOUpgradeSelection(MachineAction):
    """The Ultimaker Original can have a few revisions & upgrades.
    This action helps with selecting them, so they are added as a variant.
    """

    def __init__(self):
        super().__init__("UMOUpgradeSelection", catalog.i18nc("@action", "Select upgrades"))
        self._qml_url = "UMOUpgradeSelectionMachineAction.qml"

    def _reset(self):
        self.heatedBedChanged.emit()

    heatedBedChanged = pyqtSignal()

    @pyqtProperty(bool, notify = heatedBedChanged)
    def hasHeatedBed(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            return global_container_stack.getProperty("machine_heated_bed", "value")

    @pyqtSlot(bool)
    def setHeatedBed(self, heated_bed = True):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            # Make sure there is a definition_changes container to store the machine settings
            definition_changes_container = global_container_stack.definitionChanges
            if definition_changes_container == ContainerRegistry.getInstance().getEmptyInstanceContainer():
                definition_changes_container = CuraStackBuilder.createDefinitionChangesContainer(
                    global_container_stack, global_container_stack.getId() + "_settings")

            definition_changes_container.setProperty("machine_heated_bed", "value", heated_bed)
            self.heatedBedChanged.emit()
