from cura.MachineAction import MachineAction
from UM.i18n import i18nCatalog
import cura.Settings.CuraContainerRegistry
import UM.Settings.DefinitionContainer
catalog = i18nCatalog("cura")


class UpgradeFirmwareMachineAction(MachineAction):
    def __init__(self):
        super().__init__("UpgradeFirmware", catalog.i18nc("@action", "Upgrade Firmware"))
        self._qml_url = "UpgradeFirmwareMachineAction.qml"
        cura.Settings.CuraContainerRegistry.getInstance().containerAdded.connect(self._onContainerAdded)

    def _onContainerAdded(self, container):
        # Add this action as a supported action to all machine definitions
        if isinstance(container, UM.Settings.DefinitionContainer) and container.getMetaDataEntry("type") == "machine" and container.getMetaDataEntry("supports_usb_connection"):
            UM.Application.getInstance().getMachineActionManager().addSupportedAction(container.getId(), self.getKey())
