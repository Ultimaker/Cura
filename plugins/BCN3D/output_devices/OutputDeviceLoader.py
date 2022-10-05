
from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from UM.Logger import Logger

from .device_plugin import DevicePlugin

class OutputDeviceLoader(OutputDevicePlugin):

    def __init__(self):
        super().__init__()
        Logger.info(f"apoyo device OutputDeviceLoader loader")
        self.device_plugin = DevicePlugin.DevicePlugin()