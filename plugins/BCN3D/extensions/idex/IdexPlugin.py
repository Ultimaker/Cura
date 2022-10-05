from typing import List, Optional, Any, Dict

from UM.Extension import Extension
from cura import CuraActions

from cura.CuraApplication import CuraApplication
from UM.i18n import i18nCatalog
from UM.Logger import Logger

i18n_catalog = i18nCatalog("BCN3DIdex")


class IdexPlugin(Extension):
    def __init__(self) -> None:
        super().__init__()
        Logger.info(f"IdexPlugin init")

        self._curaActions = CuraActions.CuraActions()
        self._application = CuraApplication.getInstance()
        self._i18n_catalog = None  # type: Optional[i18nCatalog]
        self._global_container_stack = self._application.getGlobalContainerStack()
        self._application.globalContainerStackChanged.connect(self._onGlobalContainerStackChanged)

        self._settings_dict = {}  # type: Dict[str, Any]
        self._expanded_categories = []  # type: List[str]  # temporary list used while creating nested settings

        self._onGlobalContainerStackChanged()

    def _onGlobalContainerStackChanged(self):
        Logger.info(f"IDEX: _onGlobalContainerStackChanged")

        self._global_container_stack = self._application.getGlobalContainerStack()

        if self._global_container_stack:
            self._global_container_stack.propertyChanged.connect(self._onPropertyChanged)

            # Calling _onPropertyChanged as an initialization
            self._onPropertyChanged("print_mode", "value")

    def _onPropertyChanged(self, key: str, property_name: str) -> None:
        Logger.info(f"IDEX _onPropertyChange: (any property has changed)")
        if key == "print_mode" and property_name == "value":
            Logger.info(f"IdexPlugin: print_mode property changed")
            print_mode = self._global_container_stack.getProperty("print_mode", "value")
            left_extruder = self._global_container_stack.extruderList[0]
            right_extruder = self._global_container_stack.extruderList[1]

            try:
                left_extruder.enabledChanged.disconnect(self._onEnabledChangedLeft)
                right_extruder.enabledChanged.disconnect(self._onEnabledChangedRight)
            except Exception:
                # Just in case the connection didn't exists
                pass

            if print_mode == "singleT0":
                self._application.getMachineManager().setExtruderEnabled(0, True)
                self._application.getMachineManager().setExtruderEnabled(1, False)

            elif print_mode == "singleT1":
                self._application.getMachineManager().setExtruderEnabled(0, False)
                self._application.getMachineManager().setExtruderEnabled(1, True)

            elif print_mode == "dual":
                self._application.getMachineManager().setExtruderEnabled(0, True)
                self._application.getMachineManager().setExtruderEnabled(1, True)

            else:
                self._application.getMachineManager().setExtruderEnabled(0, True)
                self._application.getMachineManager().setExtruderEnabled(1, False)

            left_extruder.enabledChanged.connect(self._onEnabledChangedLeft)
            right_extruder.enabledChanged.connect(self._onEnabledChangedRight)

    def _onEnabledChangedLeft(self):
        print_mode = self._global_container_stack.getProperty("print_mode", "value")
        if print_mode == "singleT0":
            left_extruder = self._global_container_stack.extruderList[0]
            if not left_extruder.isEnabled:
                self._application.getMachineManager().setExtruderEnabled(0, True)

        elif print_mode == "singleT1":
            self._global_container_stack.setProperty("print_mode", "value", "dual")

        elif print_mode == "dual":
            self._global_container_stack.setProperty("print_mode", "value", "singleT1")

        else:
            left_extruder = self._global_container_stack.extruderList[0]
            if not left_extruder.isEnabled:
                self._application.getMachineManager().setExtruderEnabled(0, True)

    def _onEnabledChangedRight(self):
        print_mode = self._global_container_stack.getProperty("print_mode", "value")

        if print_mode == "singleT0":
            self._global_container_stack.setProperty("print_mode", "value", "dual")

        elif print_mode == "singleT1":
            right_extruder = self._global_container_stack.extruderList[1]
            if not right_extruder.isEnabled:
                self._application.getMachineManager().setExtruderEnabled(1, True)

        elif print_mode == "dual":
            self._global_container_stack.setProperty("print_mode", "value", "singleT0")

        else:
            right_extruder = self._global_container_stack.extruderList[1]
            if right_extruder.isEnabled:
                # When in duplication/mirror modes force the right extruder to be disabled
                self._application.getMachineManager().setExtruderEnabled(1, False)
