from UM.Application import Application
from UM.Settings.DefinitionContainer import DefinitionContainer
from cura.MachineAction import MachineAction
from UM.i18n import i18nCatalog
from UM.Settings.ContainerRegistry import ContainerRegistry

catalog = i18nCatalog("cura")

##  Upgrade the firmware of a machine by USB with this action.
class UpgradeFirmwareMachineAction(MachineAction):
    def __init__(self):
        super().__init__("UpgradeFirmware", catalog.i18nc("@action", "Upgrade Firmware"))
        self._qml_url = "UpgradeFirmwareMachineAction.qml"
        ContainerRegistry.getInstance().containerAdded.connect(self._onContainerAdded)

    def _onContainerAdded(self, container):
        # Add this action as a supported action to all machine definitions if they support USB connection
        if isinstance(container, DefinitionContainer) and container.getMetaDataEntry("type") == "machine" and container.getMetaDataEntry("supports_usb_connection"):
            Application.getInstance().getMachineActionManager().addSupportedAction(container.getId(), self.getKey())
