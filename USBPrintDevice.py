from UM.StorageDevice import StorageDevice
from UM.Signal import Signal, SignalEmitter

class USBPrintDevice(StorageDevice, SignalEmitter):
    def __init__(self):
        super().__init__()