# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QObject, QUrl, pyqtSignal, pyqtProperty

from cura.PrinterOutputDevice import PrinterOutputDevice

from .avr_isp import stk500v2, intelHex

from enum import IntEnum

class AvrFirmwareUpdater(QObject):
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
        # Ensure that other connections are closed.
        if self._connection_state != ConnectionState.closed:
            self.close()

        try:
            hex_file = intelHex.readHex(self._firmware_location)
            assert len(hex_file) > 0
        except (FileNotFoundError, AssertionError):
            Logger.log("e", "Unable to read provided hex file. Could not update firmware.")
            self.setFirmwareUpdateState(FirmwareUpdateState.firmware_not_found_error)
            return

        programmer = stk500v2.Stk500v2()
        programmer.progress_callback = self._onFirmwareProgress

        try:
            programmer.connect(self._serial_port)
        except:
            programmer.close()
            Logger.logException("e", "Failed to update firmware")
            self.setFirmwareUpdateState(FirmwareUpdateState.communication_error)
            return

        # Give programmer some time to connect. Might need more in some cases, but this worked in all tested cases.
        sleep(1)
        if not programmer.isConnected():
            Logger.log("e", "Unable to connect with serial. Could not update firmware")
            self.setFirmwareUpdateState(FirmwareUpdateState.communication_error)
        try:
            programmer.programChip(hex_file)
        except SerialException:
            self.setFirmwareUpdateState(FirmwareUpdateState.io_error)
            return
        except:
            self.setFirmwareUpdateState(FirmwareUpdateState.unknown_error)
            return

        programmer.close()

        # Clean up for next attempt.
        self._update_firmware_thread = Thread(target=self._updateFirmware, daemon=True)
        self._firmware_location = ""
        self._onFirmwareProgress(100)
        self.setFirmwareUpdateState(FirmwareUpdateState.completed)

        # Try to re-connect with the machine again, which must be done on the Qt thread, so we use call later.
        CuraApplication.getInstance().callLater(self.connect)

    ##  Show firmware interface.
    #   This will create the view if its not already created.
    def showFirmwareInterface(self):
        if self._firmware_view is None:
            path = os.path.join(PluginRegistry.getInstance().getPluginPath("USBPrinting"), "FirmwareUpdateWindow.qml")
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

