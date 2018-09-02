# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QObject, QUrl, pyqtSignal, pyqtProperty

from UM.Resources import Resources
from cura.PrinterOutputDevice import PrinterOutputDevice

from enum import IntEnum
from threading import Thread

class FirmwareUpdater(QObject):
    firmwareProgressChanged = pyqtSignal()
    firmwareUpdateStateChanged = pyqtSignal()

    def __init__(self, output_device: PrinterOutputDevice) -> None:
        self._output_device = output_device

        self._update_firmware_thread = Thread(target=self._updateFirmware, daemon = True)

        self._firmware_view = None
        self._firmware_location = None
        self._firmware_progress = 0
        self._firmware_update_state = FirmwareUpdateState.idle

    def updateFirmware(self, file):
        # the file path could be url-encoded.
        if file.startswith("file://"):
            self._firmware_location = QUrl(file).toLocalFile()
        else:
            self._firmware_location = file
        self.showFirmwareInterface()
        self.setFirmwareUpdateState(FirmwareUpdateState.updating)
        self._update_firmware_thread.start()

    def _updateFirmware(self):
        raise NotImplementedError("_updateFirmware needs to be implemented")

    def cleanupAfterUpdate(self):
        # Clean up for next attempt.
        self._update_firmware_thread = Thread(target=self._updateFirmware, daemon=True)
        self._firmware_location = ""
        self._onFirmwareProgress(100)
        self.setFirmwareUpdateState(FirmwareUpdateState.completed)

    ##  Show firmware interface.
    #   This will create the view if its not already created.
    def showFirmwareInterface(self):
        if self._firmware_view is None:
            path = Resources.getPath(self.ResourceTypes.QmlFiles, "FirmwareUpdateWindow.qml")
            self._firmware_view = CuraApplication.getInstance().createQmlComponent(path, {"manager": self})

        self._firmware_view.show()

    @pyqtProperty(float, notify = firmwareProgressChanged)
    def firmwareProgress(self):
        return self._firmware_progress

    @pyqtProperty(int, notify=firmwareUpdateStateChanged)
    def firmwareUpdateState(self):
        return self._firmware_update_state

    def setFirmwareUpdateState(self, state):
        if self._firmware_update_state != state:
            self._firmware_update_state = state
            self.firmwareUpdateStateChanged.emit()

    # Callback function for firmware update progress.
    def _onFirmwareProgress(self, progress, max_progress = 100):
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

