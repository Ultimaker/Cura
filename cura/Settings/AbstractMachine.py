from typing import List

from UM.Settings.ContainerStack import ContainerStack
from cura.Settings.GlobalStack import GlobalStack


class AbstractMachine(GlobalStack):
    """ Represents a group of machines of the same type. This allows the user to select settings before selecting a printer. """

    def __init__(self, container_id: str):
        super().__init__(container_id)
        self.setMetaDataEntry("type", "abstract_machine")

    def getMachines(self) -> List[ContainerStack]:
        from cura.CuraApplication import CuraApplication
        application = CuraApplication.getInstance()
        registry = application.getContainerRegistry()

        printer_type = self.definition.getId()
        cloud_printer_type = 3
        return [machine for machine in registry.findContainerStacks(type="machine") if machine.definition.id == printer_type and cloud_printer_type in machine.configuredConnectionTypes]
