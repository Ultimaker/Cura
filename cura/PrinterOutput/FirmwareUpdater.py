# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QObject, QUrl, pyqtSignal, pyqtProperty

from enum import IntEnum
from threading import Thread
from typing import Union

MYPY = False
if MYPY:
    from cura.PrinterOutputDevice import PrinterOutputDevice

class FirmwareUpdater(QObject):
    firmwareProgressChanged = pyqtSignal()
    firmwareUpdateStateChanged = pyqtSignal()

    def __init__(self, output_device: "PrinterOutputDevice") -> None:
        super().__init__()

        self._output_device = output_device

        self._update_firmware_thread = Thread(target=self._updateFirmware, daemon=True)

        self._firmware_location = ""
        self._firmware_progress = 0
        self._firmware_update_state = FirmwareUpdateState.idle

    def updateFirmware(self, file: Union[str, QUrl]) -> None:
        # the file path could be url-encoded.
        if file.startswith("file://"):
            self._firmware_location = QUrl(file).toLocalFile()
        else:
            self._firmware_location = file

        self._setFirmwareUpdateState(FirmwareUpdateState.updating)

        self._update_firmware_thread.start()

    def _updateFirmware(self) -> None:
        raise NotImplementedError("_updateFirmware needs to be implemented")

    ##  Cleanup after a succesful update
    def _cleanupAfterUpdate(self) -> None:
        # Clean up for next attempt.
        self._update_firmware_thread = Thread(target=self._updateFirmware, daemon=True)
        self._firmware_location = ""
        self._onFirmwareProgress(100)
        self._setFirmwareUpdateState(FirmwareUpdateState.completed)

    @pyqtProperty(float, notify = firmwareProgressChanged)
    def firmwareProgress(self) -> float:
        return self._firmware_progress

    @pyqtProperty(int, notify=firmwareUpdateStateChanged)
    def firmwareUpdateState(self) -> "FirmwareUpdateState":
        return self._firmware_update_state

    def _setFirmwareUpdateState(self, state) -> None:
        if self._firmware_update_state != state:
            self._firmware_update_state = state
            self.firmwareUpdateStateChanged.emit()

    # Callback function for firmware update progress.
    def _onFirmwareProgress(self, progress, max_progress = 100) -> None:
        self._firmware_progress = (progress / max_progress) * 100  # Convert to scale of 0-100
        self.firmwareProgressChanged.emit()


class FirmwareUpdateState(IntEnum):
    idle = 0
    updating = 1
    completed = 2
    unknown_error = 3
    communication_error = 4
    io_error = 5
    firmware_not_found_error = 6

