from UM.i18n import i18nCatalog
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Application import Application
from UM.Settings.ContainerRegistry import ContainerRegistry

from cura.MachineAction import MachineAction

from PyQt5.QtCore import pyqtSignal, pyqtSlot, pyqtProperty

import os.path

catalog = i18nCatalog("cura")

class ConnectUSBAction(MachineAction):
    def __init__(self, parent = None):
        super().__init__("ConnectUSBAction", catalog.i18nc("@action", "Connect via USB"))

        self._qml_url = "ConnectUSBAction.qml"
        self._window = None
        self._context = None

        ContainerRegistry.getInstance().containerAdded.connect(self._onContainerAdded)

    instancesChanged = pyqtSignal()

    def _onContainerAdded(self, container):
        # Add this action as a supported action to all machine definitions
        if isinstance(container, DefinitionContainer) and container.getMetaDataEntry("type") == "machine" and container.getMetaDataEntry("supports_usb_connection"):
            Application.getInstance().getMachineActionManager().addSupportedAction(container.getId(), self.getKey())
            Application.getInstance().getMachineActionManager().addFirstStartAction(container.getId(), self.getKey(), index = 0)

    @pyqtSlot(str)
    def setSerialPort(self, serial_port):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            if "serial_port" in global_container_stack.getMetaData():
                global_container_stack.setMetaDataEntry("serial_port", serial_port)
            else:
                global_container_stack.addMetaDataEntry("serial_port", serial_port)
        self.serialPortChanged.emit()

    serialPortChanged = pyqtSignal()

    ##  Get the stored serial port for this machine
    #   \return key String containing the serial port device name, AUTO or NONE
    @pyqtProperty(str, notify = serialPortChanged)
    def serialPort(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            return global_container_stack.getMetaDataEntry("serial_port", "NONE")
        else:
            return "NONE"

    @pyqtSlot(str)
    def setSerialRate(self, serial_rate):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            if "serial_rate" in global_container_stack.getMetaData():
                global_container_stack.setMetaDataEntry("serial_rate", serial_rate)
            else:
                global_container_stack.addMetaDataEntry("serial_rate", serial_rate)
        self.serialRateChanged.emit()

    serialRateChanged = pyqtSignal()

    ##  Get the stored serial rate for this machine
    #   \return key String containing the serial rate device name, AUTO or NONE
    @pyqtProperty(str, notify = serialRateChanged)
    def serialRate(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            return global_container_stack.getMetaDataEntry("serial_rate", "AUTO")
        else:
            return "AUTO"

    @pyqtSlot(bool)
    def setAutoConnect(self, serial_auto_connect):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            if "serial_auto_connect" in global_container_stack.getMetaData():
                global_container_stack.setMetaDataEntry("serial_auto_connect", str(serial_auto_connect))
            else:
                global_container_stack.addMetaDataEntry("serial_auto_connect", str(serial_auto_connect))
        self.autoConnectChanged.emit()

    autoConnectChanged = pyqtSignal()

    ##  Get the stored serial rate for this machine
    #   \return key String containing the serial rate device name, AUTO or NONE
    @pyqtProperty(bool, notify = autoConnectChanged)
    def autoConnect(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            return global_container_stack.getMetaDataEntry("serial_auto_connect") == "True"
        else:
            return False
