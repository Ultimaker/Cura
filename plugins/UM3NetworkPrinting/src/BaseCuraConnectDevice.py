# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice


## this is the base class for the UM3 output devices (via connect or cloud)
class BaseCuraConnectDevice(NetworkedPrinterOutputDevice):
    pass
