# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from cura.CuraApplication import CuraApplication
from UM.Settings.DefinitionContainer import DefinitionContainer
from cura.MachineAction import MachineAction
from UM.i18n import i18nCatalog
from UM.Settings.ContainerRegistry import ContainerRegistry
from cura.PrinterOutput.FirmwareUpdater import FirmwareUpdateState

from PyQt5.QtCore import pyqtSignal, pyqtProperty, QObject
from typing import Optional

MYPY = False
if MYPY:
    from cura.PrinterOutput.FirmwareUpdater import FirmwareUpdater
    from cura.PrinterOutput.PrinterOutputDevice import PrinterOutputDevice
    from UM.Settings.ContainerInterface import ContainerInterface

catalog = i18nCatalog("cura")

##  Upgrade the firmware of a machine by USB with this action.
class FirmwareUpdaterMachineAction(MachineAction):
    def __init__(self) -> None:
        super().__init__("UpgradeFirmware", catalog.i18nc("@action", "Update Firmware"))
        self._qml_url = "FirmwareUpdaterMachineAction.qml"
        ContainerRegistry.getInstance().containerAdded.connect(self._onContainerAdded)

        self._active_output_device = None  # type: Optional[PrinterOutputDevice]
        self._active_firmware_updater = None  # type: Optional[FirmwareUpdater]

        CuraApplication.getInstance().engineCreatedSignal.connect(self._onEngineCreated)

    def _onEngineCreated(self) -> None:
        CuraApplication.getInstance().getMachineManager().outputDevicesChanged.connect(self._onOutputDevicesChanged)

    def _onContainerAdded(self, container: "ContainerInterface") -> None:
        # Add this action as a supported action to all machine definitions if they support USB connection
        if isinstance(container, DefinitionContainer) and container.getMetaDataEntry("type") == "machine" and container.getMetaDataEntry("supports_usb_connection"):
            CuraApplication.getInstance().getMachineActionManager().addSupportedAction(container.getId(), self.getKey())

    def _onOutputDevicesChanged(self) -> None:
        if self._active_output_device and self._active_output_device.activePrinter:
            self._active_output_device.activePrinter.getController().canUpdateFirmwareChanged.disconnect(self._onControllerCanUpdateFirmwareChanged)

        output_devices = CuraApplication.getInstance().getMachineManager().printerOutputDevices
        self._active_output_device = output_devices[0] if output_devices else None

        if self._active_output_device and self._active_output_device.activePrinter:
            self._active_output_device.activePrinter.getController().canUpdateFirmwareChanged.connect(self._onControllerCanUpdateFirmwareChanged)

        self.outputDeviceCanUpdateFirmwareChanged.emit()

    def _onControllerCanUpdateFirmwareChanged(self) -> None:
        self.outputDeviceCanUpdateFirmwareChanged.emit()

    outputDeviceCanUpdateFirmwareChanged = pyqtSignal()
    @pyqtProperty(QObject, notify = outputDeviceCanUpdateFirmwareChanged)
    def firmwareUpdater(self) -> Optional["FirmwareUpdater"]:
        if self._active_output_device and self._active_output_device.activePrinter and self._active_output_device.activePrinter.getController() is not None and self._active_output_device.activePrinter.getController().can_update_firmware:
            self._active_firmware_updater = self._active_output_device.getFirmwareUpdater()
            return self._active_firmware_updater

        elif self._active_firmware_updater and self._active_firmware_updater.firmwareUpdateState not in [FirmwareUpdateState.idle, FirmwareUpdateState.completed]:
            # During a firmware update, the PrinterOutputDevice is disconnected but the FirmwareUpdater is still there
            return self._active_firmware_updater

        self._active_firmware_updater = None
        return None
