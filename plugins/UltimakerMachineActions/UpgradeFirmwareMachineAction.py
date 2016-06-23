from cura.MachineAction import MachineAction

class UpgradeFirmwareMachineAction(MachineAction):
    def __init__(self):
        super().__init__("UpgradeFirmware", "Upgrade Firmware")
        self._qml_url = "UpgradeFirmwareMachineAction.qml"