from cura.CuraApplication import CuraApplication
import re

from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from cura.Settings.GlobalStack import GlobalStack

class PrintInformationPatches():
    def __init__(self, print_information) -> None:
        self._print_information = print_information
        self._print_information._defineAbbreviatedMachineName = self._defineAbbreviatedMachineName

        self._global_stack = None # type: Optional[GlobalStack]
        CuraApplication.getInstance().getMachineManager().globalContainerChanged.connect(self._onMachineChanged)
        self._onMachineChanged()

    def _onMachineChanged(self) -> None:
        if self._global_stack:
            definition_container = self._global_stack.getBottom()
            if definition_container.getId() == "blackbelt":
                self._global_stack.containersChanged.disconnect(self._onContainersChanged)

        self._global_stack = CuraApplication.getInstance().getGlobalContainerStack()

        if self._global_stack:
            definition_container = self._global_stack.getBottom()
            if definition_container.getId() == "blackbelt":
                self._global_stack.containersChanged.connect(self._onContainersChanged)

    def _onContainersChanged(self, container: Any) -> None:
        self._print_information._updateJobName()


    ##  Created an acronymn-like abbreviated machine name from the currently active machine name
    #   Called each time the global stack is switched
    #   Copied verbatim from PrintInformation._defineAbbreviatedMachineName, with a minor patch to set the abbreviation from settings
    def _defineAbbreviatedMachineName(self) -> None:
        global_container_stack = self._print_information._application.getGlobalContainerStack()
        if not global_container_stack:
            self._print_information._abbr_machine = ""
            return

        ### START PATCH: construct prefix from variant & material
        definition_container = global_container_stack.getBottom()
        if definition_container.getId() == "blackbelt":
            extruder_stack = self._print_information._application.getMachineManager()._active_container_stack
            if not extruder_stack:
                return

            gantry_angle = global_container_stack.getProperty("blackbelt_gantry_angle", "value")
            nozzle_size = str(global_container_stack.getProperty("machine_nozzle_size", "value")).replace(".", "")
            material_type = extruder_stack.material.getMetaDataEntry("material")
            self._print_information._abbr_machine = "%s_%s_%s" % (gantry_angle, nozzle_size, material_type)
            return
        ### END PATCH

        active_machine_type_name = global_container_stack.definition.getName()

        abbr_machine = ""
        for word in re.findall(r"[\w']+", active_machine_type_name):
            if word.lower() == "ultimaker":
                abbr_machine += "UM"
            elif word.isdigit():
                abbr_machine += word
            else:
                stripped_word = self._print_information._stripAccents(word.upper())
                # - use only the first character if the word is too long (> 3 characters)
                # - use the whole word if it's not too long (<= 3 characters)
                if len(stripped_word) > 3:
                    stripped_word = stripped_word[0]
                abbr_machine += stripped_word

        self._print_information._abbr_machine = abbr_machine
