from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice

class ClusterUM3OutputDevice(NetworkedPrinterOutputDevice):
    def __init__(self, device_id, address, properties, parent = None):
        super().__init__(device_id = device_id, parent = parent)