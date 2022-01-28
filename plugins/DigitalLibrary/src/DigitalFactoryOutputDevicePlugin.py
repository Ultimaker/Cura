# Copyright (c) 2021 Ultimaker B.V.
# Uranium is released under the terms of the LGPLv3 or higher.

from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from .DigitalFactoryOutputDevice import DigitalFactoryOutputDevice
from .DigitalFactoryController import DigitalFactoryController


class DigitalFactoryOutputDevicePlugin(OutputDevicePlugin):
    def __init__(self, df_controller: DigitalFactoryController) -> None:
        super().__init__()
        self.df_controller = df_controller

    def start(self) -> None:
        self.getOutputDeviceManager().addProjectOutputDevice(DigitalFactoryOutputDevice(plugin_id = self.getPluginId(), df_controller = self.df_controller, add_to_output_devices = True))

    def stop(self) -> None:
        self.getOutputDeviceManager().removeProjectOutputDevice("digital_factory")
