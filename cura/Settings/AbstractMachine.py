from typing import List

from cura.Settings.GlobalStack import GlobalStack


class AbstractMachine(GlobalStack):
    """ Behaves as a type of machine, represents multiple machines of the same type """

    def __init__(self, container_id: str):
        super().__init__(container_id)
        self.setMetaDataEntry("type", "abstract_machine")

    def getMachinesOfType(self) -> List[GlobalStack]:
        pass


