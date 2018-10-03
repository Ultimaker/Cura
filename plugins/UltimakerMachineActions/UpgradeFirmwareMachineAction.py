# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Application import Application
from UM.Settings.DefinitionContainer import DefinitionContainer
from cura.MachineAction import MachineAction
from UM.i18n import i18nCatalog
from UM.Settings.ContainerRegistry import ContainerRegistry

from PyQt5.QtCore import pyqtSignal, pyqtProperty, QObject
from typing import Optional

MYPY = False
if MYPY:
    from cura.PrinterOutput.FirmwareUpdater import FirmwareUpdater

catalog = i18nCatalog("cura")

##  Upgrade the firmware of a machine by USB with this action.
class UpgradeFirmwareMachineAction(MachineAction):
    def __init__(self) -> None:
        super().__init__("UpgradeFirmware", catalog.i18nc("@action", "Upgrade Firmware"))
        self._qml_url = "UpgradeFirmwareMachineAction.qml"
        ContainerRegistry.getInstance().containerAdded.connect(self._onContainerAdded)

        self._active_output_device = None

        Application.getInstance().engineCreatedSignal.connect(self._onEngineCreated)

    def _onEngineCreated(self) -> None:
        Application.getInstance().getMachineManager().outputDevicesChanged.connect(self._onOutputDevicesChanged)

    def _onContainerAdded(self, container) -> None:
        # Add this action as a supported action to all machine definitions if they support USB connection
        if isinstance(container, DefinitionContainer) and container.getMetaDataEntry("type") == "machine" and container.getMetaDataEntry("supports_usb_connection"):
            Application.getInstance().getMachineActionManager().addSupportedAction(container.getId(), self.getKey())

    def _onOutputDevicesChanged(self) -> None:
        if self._active_output_device:
            self._active_output_device.activePrinter.getController().canUpdateFirmwareChanged.disconnect(self._onControllerCanUpdateFirmwareChanged)
        output_devices = Application.getInstance().getMachineManager().printerOutputDevices
        print(output_devices)
        self._active_output_device = output_devices[0] if output_devices else None
        if self._active_output_device:
            self._active_output_device.activePrinter.getController().canUpdateFirmwareChanged.connect(self._onControllerCanUpdateFirmwareChanged)

        self.outputDeviceCanUpdateFirmwareChanged.emit()

    def _onControllerCanUpdateFirmwareChanged(self) -> None:
        self.outputDeviceCanUpdateFirmwareChanged.emit()

    outputDeviceCanUpdateFirmwareChanged = pyqtSignal()
    @pyqtProperty(QObject, notify = outputDeviceCanUpdateFirmwareChanged)
    def firmwareUpdater(self) -> Optional["firmwareUpdater"]:
        if self._active_output_device and self._active_output_device.activePrinter.getController().can_update_firmware:
            return self._active_output_device.getFirmwareUpdater()

        return None