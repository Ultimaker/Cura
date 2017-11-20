from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice

class LegacyUM3OutputDevice(NetworkedPrinterOutputDevice):
    def __init__(self, device_id, address: str, properties, parent = None):
        super().__init__(device_id = device_id, address = address, parent = parent)

    def _update(self):
        pass
