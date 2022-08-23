from typing import List

from UM.Settings.ContainerStack import ContainerStack
from cura.PrinterOutput.PrinterOutputDevice import ConnectionType
from cura.Settings.GlobalStack import GlobalStack
from UM.MimeTypeDatabase import MimeType, MimeTypeDatabase
from UM.Settings.ContainerRegistry import ContainerRegistry


class AbstractMachine(GlobalStack):
    """ Represents a group of machines of the same type. This allows the user to select settings before selecting a printer. """

    def __init__(self, container_id: str) -> None:
        super().__init__(container_id)
        self.setMetaDataEntry("type", "abstract_machine")

    @classmethod
    def getMachines(cls, abstract_machine: ContainerStack) -> List[ContainerStack]:
        """ Fetches all container stacks that match definition_id with an abstract machine.

        :param abstractMachine: The abstract machine stack.
        :return: A list of Containers or an empty list if abstract_machine is not an "abstract_machine"
        """
        if not abstract_machine.getMetaDataEntry("type") == "abstract_machine":
            return []

        from cura.CuraApplication import CuraApplication  # In function to avoid circular import
        application = CuraApplication.getInstance()
        registry = application.getContainerRegistry()

        printer_type = abstract_machine.definition.getId()

        return [machine for machine in registry.findContainerStacks(type="machine") if machine.definition.id == printer_type and ConnectionType.CloudConnection in machine.configuredConnectionTypes]


## private:
_abstract_machine_mime = MimeType(
    name = "application/x-cura-abstract-machine",
    comment = "Cura Abstract Machine",
    suffixes = ["global.cfg"]
)

MimeTypeDatabase.addMimeType(_abstract_machine_mime)
ContainerRegistry.addContainerTypeByName(AbstractMachine, "abstract_machine", _abstract_machine_mime.name)
