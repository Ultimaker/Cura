
from UM.Scene.Selection import Selection
from UM.Application import Application
from UM.Logger import Logger
from cura.CuraApplication import CuraApplication
from PyQt6.QtCore import QObject, pyqtSlot

from UM.i18n import i18nCatalog
from UM.Logger import Logger
from cura.Utils.BCN3Dutils.PrintModeManager import PrintModeManager

class PrintModesLitsener(QObject):

    def __init__(self):
        super().__init__()
        if PrintModesLitsener.__instance is not None:
            raise ValueError("Duplicate singleton creation")
        self._cura_application = CuraApplication.getInstance()
        self._application = CuraApplication.getInstance()
        self.printModeManager = PrintModeManager.getInstance()

    # Function to set the state checked inside the qml of the plugin
    @pyqtSlot(result = str)
    def getPrintMode(self):
        self._global_container_stack = self._application.getGlobalContainerStack()
        print_mode = self._global_container_stack.getProperty("print_mode", "value")
        return print_mode

    @pyqtSlot(str)
    def setPrintMode(self, print_mode: str):
        Logger.debug("Set printmode: %s ", print_mode)
        self.printModeManager.setPrintModeToLoad(print_mode)
        self._global_container_stack = self._application.getGlobalContainerStack()
        left_extruder = self._global_container_stack.extruderList[0]
        right_extruder = self._global_container_stack.extruderList[1]
        self._global_container_stack = self._application.getGlobalContainerStack()
        left_extruder = self._global_container_stack.extruderList[0]
        right_extruder = self._global_container_stack.extruderList[1]
        try:
            left_extruder.enabledChanged.disconnect(self._onEnabledChangedLeft)
            right_extruder.enabledChanged.disconnect(self._onEnabledChangedRight)
            self._application.getMachineManager().setExtruderEnabled(0, False)
            self._application.getMachineManager().setExtruderEnabled(1, False)
        except Exception:
            # Just in case the connection didn't exists
            pass
        if print_mode == "singleT0":
            self._global_container_stack.setProperty("print_mode", "value", "singleT0")
            CuraApplication.selectAll(CuraApplication.getInstance())
            for node in Selection.getAllSelectedObjects():
                node.setSetting("print_mode", "singleTO")

        elif print_mode == "singleT1":
            self._global_container_stack.setProperty("print_mode", "value", "singleT1")
            CuraApplication.selectAll(CuraApplication.getInstance())
            for node in Selection.getAllSelectedObjects():
                node.setSetting("print_mode", "singleT1")

        elif print_mode == "dual":
            self._global_container_stack.setProperty("print_mode", "value", "dual")
            CuraApplication.selectAll(CuraApplication.getInstance())
            for node in Selection.getAllSelectedObjects():
                node.setSetting("print_mode", "dual")

        elif print_mode == "mirror":
            self._global_container_stack.setProperty("print_mode", "value", "mirror")
            CuraApplication.selectAll(CuraApplication.getInstance())
            for node in Selection.getAllSelectedObjects():
                node.setSetting("print_mode", "mirror")

        elif print_mode == "duplication":
            self._global_container_stack.setProperty("print_mode", "value", "duplication")
            CuraApplication.selectAll(CuraApplication.getInstance())
            for node in Selection.getAllSelectedObjects():
                node.setSetting("print_mode", "duplication")

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

    @classmethod
    def getInstance(cls) -> "PrintModesLitsener":
        if not cls.__instance:
            cls.__instance = PrintModesLitsener()
        return cls.__instance

    __instance = None