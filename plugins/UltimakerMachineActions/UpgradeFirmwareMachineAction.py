from cura.MachineAction import MachineAction
from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


class UpgradeFirmwareMachineAction(MachineAction):
    def __init__(self):
        super().__init__("UpgradeFirmware", catalog.i18nc("@action", "Upgrade Firmware"))
        self._qml_url = "UpgradeFirmwareMachineAction.qml"