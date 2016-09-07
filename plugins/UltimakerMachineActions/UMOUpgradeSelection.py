from cura.MachineAction import MachineAction
from PyQt5.QtCore import pyqtSlot, pyqtSignal, pyqtProperty

from UM.i18n import i18nCatalog
from UM.Application import Application
catalog = i18nCatalog("cura")

import UM.Settings.InstanceContainer

class UMOUpgradeSelection(MachineAction):
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
            variant = global_container_stack.findContainer({"type": "variant"})
            if variant:
                if variant.getId() == "empty_variant":
                    variant_index = global_container_stack.getContainerIndex(variant)
                    variant = self._createVariant(global_container_stack, variant_index)
                variant.setProperty("machine_heated_bed", "value", heated_bed)
                self.heatedBedChanged.emit()

    def _createVariant(self, global_container_stack, variant_index):
        # Create and switch to a variant to store the settings in
        new_variant = UM.Settings.InstanceContainer(global_container_stack.getName() + "_variant")
        new_variant.addMetaDataEntry("type", "variant")
        new_variant.setDefinition(global_container_stack.getBottom())
        UM.Settings.ContainerRegistry.getInstance().addContainer(new_variant)
        global_container_stack.replaceContainer(variant_index, new_variant)
        return new_variant