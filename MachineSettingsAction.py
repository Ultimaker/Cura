from PyQt5.QtCore import pyqtSlot

from cura.MachineAction import MachineAction
import cura.Settings.CuraContainerRegistry

import UM.Application
import UM.Settings.InstanceContainer
import UM.Settings.DefinitionContainer

import UM.i18n
catalog = UM.i18n.i18nCatalog("cura")

class MachineSettingsAction(MachineAction):
    def __init__(self, parent = None):
        super().__init__("MachineSettingsAction", catalog.i18nc("@action", "Machine Settings"))
        self._qml_url = "MachineSettingsAction.qml"

        cura.Settings.CuraContainerRegistry.getInstance().containerAdded.connect(self._onContainerAdded)

    def _reset(self):
        global_container_stack = UM.Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            variant = global_container_stack.findContainer({"type": "variant"})
            if variant and variant.getId() == "empty_variant":
                variant_index = global_container_stack.getContainerIndex(variant)
                self._createVariant(global_container_stack, variant_index)

    def _createVariant(self, global_container_stack, variant_index):
        # Create and switch to a variant to store the settings in
        new_variant = UM.Settings.InstanceContainer(global_container_stack.getName() + "_machinesettings")
        new_variant.addMetaDataEntry("type", "variant")
        new_variant.addMetaDataEntry("purpose", "machinesettings")
        new_variant.setDefinition(global_container_stack.getBottom())
        UM.Settings.ContainerRegistry.getInstance().addContainer(new_variant)
        global_container_stack.replaceContainer(variant_index, new_variant)

    def _onContainerAdded(self, container):
        # Add this action as a supported action to all machine definitions
        if isinstance(container, UM.Settings.DefinitionContainer) and container.getMetaDataEntry("type") == "machine":
            UM.Application.getInstance().getMachineActionManager().addSupportedAction(container.getId(), self.getKey())

    @pyqtSlot()
    def forceUpdate(self):
        # Force rebuilding the build volume by reloading the global container stack.
        # This is a bit of a hack, but it seems quick enough.
        UM.Application.getInstance().globalContainerStackChanged.emit()