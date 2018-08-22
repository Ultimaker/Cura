# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from cura.PrinterOutputDevice import PrinterOutputDevice
from cura.FirmwareUpdater import FirmwareUpdater, FirmwareUpdateState

from .avr_isp import stk500v2, intelHex

class AvrFirmwareUpdater(FirmwareUpdater):
    def __init__(self, output_device: PrinterOutputDevice) -> None:
        super().__init__(output_device)

    def _updateFirmware(self):
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

        # Try to re-connect with the machine again, which must be done on the Qt thread, so we use call later.
        CuraApplication.getInstance().callLater(self.connect)

        self.cleanupAfterUpdate()
