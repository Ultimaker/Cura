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
        return global_container_stack.getProperty("machine_heated_bed", "value")

    @pyqtSlot()
    def addHeatedBed(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            variant = global_container_stack.findContainer({"type": "variant"})
            if variant:
                if variant.getId() == "empty_variant":
                    variant_index = global_container_stack.getContainerIndex(variant)
                    stack_name = global_container_stack.getName()
                    new_variant = UM.Settings.InstanceContainer(stack_name + "_variant")
                    new_variant.addMetaDataEntry("type", "variant")
                    new_variant.setDefinition(global_container_stack.getBottom())
                    UM.Settings.ContainerRegistry.getInstance().addContainer(new_variant)
                    global_container_stack.replaceContainer(variant_index, new_variant)
                    variant = new_variant
            variant.setProperty("machine_heated_bed", "value", True)
            self.heatedBedChanged.emit()

    @pyqtSlot()
    def removeHeatedBed(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            variant = global_container_stack.findContainer({"type": "variant"})
            if variant:
                variant.setProperty("machine_heated_bed", "value", False)
                self.heatedBedChanged.emit()