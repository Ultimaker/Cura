from typing import List

from UM.Settings.ContainerStack import ContainerStack
from UM.Util import parseBool
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
    def getMachines(cls, abstract_machine: ContainerStack, online_only = False) -> List[ContainerStack]:
        """ Fetches all container stacks that match definition_id with an abstract machine.

        :param abstractMachine: The abstract machine stack.
        :return: A list of Containers or an empty list if abstract_machine is not an "abstract_machine"
        """
        if not abstract_machine.getMetaDataEntry("type") == "abstract_machine":
            return []

        from cura.CuraApplication import CuraApplication  # In function to avoid circular import
        application = CuraApplication.getInstance()
        registry = application.getContainerRegistry()

        machines = registry.findContainerStacks(type="machine")
        # Filter machines that match definition
        machines = filter(lambda machine: machine.definition.id == abstract_machine.definition.getId(), machines)
        # Filter only LAN and Cloud printers
        machines = filter(lambda machine: ConnectionType.CloudConnection in machine.configuredConnectionTypes or ConnectionType.NetworkConnection in machine.configuredConnectionTypes, machines)
        if online_only:
            # LAN printers have is_online = False but should still be included
            machines = filter(lambda machine: parseBool(machine.getMetaDataEntry("is_online", False) or ConnectionType.NetworkConnection in machine.configuredConnectionTypes), machines)

        return list(machines)


## private:
_abstract_machine_mime = MimeType(
    name = "application/x-cura-abstract-machine",
    comment = "Cura Abstract Machine",
    suffixes = ["global.cfg"]
)

MimeTypeDatabase.addMimeType(_abstract_machine_mime)
ContainerRegistry.addContainerTypeByName(AbstractMachine, "abstract_machine", _abstract_machine_mime.name)
