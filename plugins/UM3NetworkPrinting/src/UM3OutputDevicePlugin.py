# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional, Callable, Dict

from UM.Signal import Signal
from cura.CuraApplication import CuraApplication

from UM.OutputDevice.OutputDeviceManager import ManualDeviceAdditionAttempt
from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin

from .Network.LocalClusterOutputDevice import LocalClusterOutputDevice
from .Network.LocalClusterOutputDeviceManager import LocalClusterOutputDeviceManager
from .Cloud.CloudOutputDeviceManager import CloudOutputDeviceManager


class UM3OutputDevicePlugin(OutputDevicePlugin):
    """This plugin handles the discovery and networking for Ultimaker 3D printers"""

    discoveredDevicesChanged = Signal()
    """Signal emitted when the list of discovered devices changed. Used by printer action in this plugin."""

    def __init__(self) -> None:
        super().__init__()

        # Create a network output device manager that abstracts all network connection logic away.
        self._network_output_device_manager = LocalClusterOutputDeviceManager()
        self._network_output_device_manager.discoveredDevicesChanged.connect(self.discoveredDevicesChanged)

        # Create a cloud output device manager that abstracts all cloud connection logic away.
        self._cloud_output_device_manager = CloudOutputDeviceManager()

        # Refresh network connections when another machine was selected in Cura.
        # This ensures no output devices are still connected that do not belong to the new active machine.
        CuraApplication.getInstance().globalContainerStackChanged.connect(self.refreshConnections)

    def start(self):
        """Start looking for devices in the network and cloud."""

        self._network_output_device_manager.start()
        self._cloud_output_device_manager.start()

    # Stop network and cloud discovery.
    def stop(self) -> None:
        self._network_output_device_manager.stop()
        self._cloud_output_device_manager.stop()

    def startDiscovery(self) -> None:
        """Restart network discovery."""

        self._network_output_device_manager.startDiscovery()

    def refreshConnections(self) -> None:
        """Force refreshing the network connections."""

        self._network_output_device_manager.refreshConnections()
        self._cloud_output_device_manager.refreshConnections()

    def canAddManualDevice(self, address: str = "") -> ManualDeviceAdditionAttempt:
        """Indicate that this plugin supports adding networked printers manually."""

        return ManualDeviceAdditionAttempt.PRIORITY

    def addManualDevice(self, address: str, callback: Optional[Callable[[bool, str], None]] = None) -> None:
        """Add a networked printer manually based on its network address."""

        self._network_output_device_manager.addManualDevice(address, callback)

    def removeManualDevice(self, key: str, address: Optional[str] = None) -> None:
        """Remove a manually connected networked printer."""

        self._network_output_device_manager.removeManualDevice(key, address)

    def getDiscoveredDevices(self) -> Dict[str, LocalClusterOutputDevice]:
        """Get the discovered devices from the local network."""

        return self._network_output_device_manager.getDiscoveredDevices()

    def associateActiveMachineWithPrinterDevice(self, device: LocalClusterOutputDevice) -> None:
        """Connect the active machine to a device."""

        self._network_output_device_manager.associateActiveMachineWithPrinterDevice(device)
