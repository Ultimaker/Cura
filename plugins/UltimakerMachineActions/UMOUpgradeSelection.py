from cura.MachineAction import MachineAction

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


class UMOUpgradeSelection(MachineAction):
    def __init__(self):
        super().__init__("UMOUpgradeSelection", catalog.i18nc("@action", "Select upgrades"))
        self._qml_url = "UMOUpgradeSelectionMachineAction.qml"