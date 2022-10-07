
from UM.Scene.Selection import Selection
from UM.Application import Application
from UM.Logger import Logger
from cura.CuraApplication import CuraApplication
from PyQt6.QtCore import QObject, pyqtSlot

from UM.i18n import i18nCatalog
from UM.Logger import Logger


class PrintModesLitsener(QObject):

    def __init__(self):
        super().__init__()
        if PrintModesLitsener.__instance is not None:
            raise ValueError("Duplicate singleton creation")
        self._cura_application = CuraApplication.getInstance()
        self._application = CuraApplication.getInstance()
        Logger.info("PrintModesLitsener initialized")

    # Function to set the state checked inside the qml of the plugin
    @pyqtSlot(result = str)
    def getPrintMode(self):
        self._global_container_stack = self._application.getGlobalContainerStack()
        print_mode = self._global_container_stack.getProperty("print_mode", "value")
        return print_mode

    @pyqtSlot(str)
    def setPrintMode(self, print_mode: str):
        Logger.info(f"set printmode")
        # setPrintModeToLoad does not exists in CuraApplication, we need either to modifify it as a plugin to override functions and params, or save the parameter in our plugins"""
        #self._application.setPrintModeToLoad(print_mode)
        self._global_container_stack = self._application.getGlobalContainerStack()
        #left_extruder = self._global_container_stack.extruderList[0]
        #right_extruder = self._global_container_stack.extruderList[1]
        try:
            '''Exception on self._onEnabledChangedLeft/_onEnabledChangedRight Due it does not exits
                in class, perhaps this should be in other class but why do we disable it?
            '''
            #left_extruder.enabledChanged.disconnect(self._onEnabledChangedLeft)
            #right_extruder.enabledChanged.disconnect(self._onEnabledChangedRight)
            self._application.getMachineManager().setExtruderEnabled(0, False)
            self._application.getMachineManager().setExtruderEnabled(1, False)
        except Exception as e:
            Logger.error ("error setting extruders: ".format(e))
            pass
        if print_mode == "singleT0":
            self._global_container_stack.setProperty("print_mode", "value", "singleT0")

            # Now we select all the nodes and set the printmode to them to avoid different nodes on differents printmodes

            CuraApplication.selectAll(CuraApplication.getInstance())
            for node in Selection.getAllSelectedObjects():
                node.setSetting("print_mode", "singleTO")

        elif print_mode == "singleT1":
            self._global_container_stack.setProperty("print_mode", "value", "singleT1")
            CuraApplication.selectAll(CuraApplication.getInstance())
            for node in Selection.getAllSelectedObjects():
                node.setSetting("print_mode", "singleT1")

        elif print_mode == "dual":
            Logger.info(f"print mode is dual")
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

    @classmethod
    def getInstance(cls) -> "PrintModesLitsener":
        if not cls.__instance:
            cls.__instance = PrintModesLitsener()
        return cls.__instance

    __instance = None