from UM.Application import Application
from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from UM import Util
#from .PrintersManager import PrintersManager

from ...extensions.api.AuthService import AuthService
from ...extensions.api.Device import Device

from UM.i18n import i18nCatalog




catalog = i18nCatalog("cura")


##  Implements an OutputDevicePlugin that provides a single instance of CloudOutputDevice
class DevicePlugin(OutputDevicePlugin):
    def __init__(self):
        super().__init__()
        self._global_stack = None
        self._printers_manager = None
        self._supports_cloud_connection = False
        self._is_logged_in = AuthService.getInstance().isLoggedIn

    def start(self):
        AuthService.getInstance().authStateChanged.connect(self._authStateChanged)
        Application.getInstance().globalContainerStackChanged.connect(self._globalStackChanged)
        self._globalStackChanged()

    def stop(self):
        self.getOutputDeviceManager().removeOutputDevice("cloud")
        self.getOutputDeviceManager().removeOutputDevice("cloud_save")

    def _authStateChanged(self, logged_in):
        self._is_logged_in = logged_in
        if self._is_logged_in and self._supports_cloud_connection:
            self.getOutputDeviceManager().addOutputDevice(Device(""))
            self.getOutputDeviceManager().addOutputDevice(Device("cloud_save"))
        else:
            self.stop()

    def _globalStackChanged(self):
        self._global_stack = Application.getInstance().getGlobalContainerStack()

        if self._global_stack:
            self._supports_cloud_connection = Util.parseBool(self._global_stack.getMetaDataEntry("is_network_machine"))

            if self._supports_cloud_connection and self._is_logged_in:
                self.getOutputDeviceManager().addOutputDevice(Device(""))
                self.getOutputDeviceManager().addOutputDevice(Device("cloud_save"))
            else:
                self.stop()

"""     def getPrintersManager(self, *args):
        if self._printers_manager is None:
            self._printers_manager = PrintersManager.getInstance()
        return self._printers_manager """