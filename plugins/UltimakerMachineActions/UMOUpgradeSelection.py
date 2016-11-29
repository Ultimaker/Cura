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
            # Make sure there is a definition_changes container to store the machine settings
            definition_changes_container = global_container_stack.findContainer({"type": "definition_changes"})
            if not definition_changes_container:
                definition_changes_container = self._createDefinitionChangesContainer(global_container_stack)

            definition_changes_container.setProperty("machine_heated_bed", "value", heated_bed)
            self.heatedBedChanged.emit()

    def _createDefinitionChangesContainer(self, global_container_stack):
        # Create a definition_changes container to store the settings in and add it to the stack
        definition_changes_container = UM.Settings.InstanceContainer(global_container_stack.getName() + "_settings")
        definition = global_container_stack.getBottom()
        definition_changes_container.setDefinition(definition)
        definition_changes_container.addMetaDataEntry("type", "definition_changes")

        UM.Settings.ContainerRegistry.getInstance().addContainer(definition_changes_container)
        # Insert definition_changes between the definition and the variant
        global_container_stack.insertContainer(-1, definition_changes_container)

        return definition_changes_container
