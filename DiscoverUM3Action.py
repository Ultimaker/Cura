from cura.MachineAction import MachineAction

class DiscoverUM3Action(MachineAction):
    def __init__(self):
        super().__init__("DiscoverUM3Action", "Discover printers")
        self._qml_url = "DiscoverUM3Action.qml"

    def _execute(self):
        pass