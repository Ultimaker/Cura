from cura.MachineAction import MachineAction

class BedLevelMachineAction(MachineAction):
    def __init__(self):
        super().__init__("BedLevel", "Level bed")

    def _execute(self):
        pass

