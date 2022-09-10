"""
Synchronizing things between the idex_print_mode setting with which extruders are enabled.
"""

from UM.Extension import Extension
from cura.CuraApplication import CuraApplication


class IdexPrintMode(Extension):
    def __init__(self) -> None:
        super().__init__()
        self._application = CuraApplication.getInstance()
        self._application.globalContainerStackChanged.connect(self._onGlobalContainerStackChanged)
        self._onGlobalContainerStackChanged()

    def _onGlobalContainerStackChanged(self) -> None:
        self._global_container_stack = self._application.getGlobalContainerStack()
        if self._global_container_stack:
            self._global_container_stack.propertyChanged.connect(self._onPropertyChanged)
            # Calling _onPropertyChanged as an initialization
            self._onPropertyChanged("idex_print_mode", "value")

    def _onPropertyChanged(self, key: str, property_name: str) -> None:
        if key != "idex_print_mode" or property_name != "value": return
        print_mode = self._global_container_stack.getProperty("idex_print_mode", "value")
        extruders = self._global_container_stack.extruderList
        if print_mode == None or len(extruders) != 2: return

        left, right = extruders

        try: left.enabledChanged.disconnect(self._onEnabledChangedLeft)
        except Exception: pass # Just in case the connection didn't exists
        try: right.enabledChanged.disconnect(self._onEnabledChangedRight)
        except Exception: pass # Just in case the connection didn't exists

        self._application.getMachineManager().setExtruderEnabled(0, True)
        self._application.getMachineManager().setExtruderEnabled(1, print_mode == "standard")

        left.enabledChanged.connect(self._onEnabledChangedLeft)
        right.enabledChanged.connect(self._onEnabledChangedRight)

    def _onEnabledChangedLeft(self) -> None:
        print_mode = self._global_container_stack.getProperty("idex_print_mode", "value")
        extruders = self._global_container_stack.extruderList
        if print_mode == None or len(extruders) != 2: return
        if print_mode == "standard": return  # can have any combination of extruders
        if not extruders[0].isEnabled:  # force left extruder to stay on for mirror/duplication
            self._application.getMachineManager().setExtruderEnabled(0, True)

    def _onEnabledChangedRight(self) -> None:
        print_mode = self._global_container_stack.getProperty("idex_print_mode", "value")
        extruders = self._global_container_stack.extruderList
        if print_mode == None or len(extruders) != 2: return
        if print_mode == "standard": return  # can have any combination of extruders
        if extruders[1].isEnabled:
            self._global_container_stack.setProperty("idex_print_mode", "value", "standard")
