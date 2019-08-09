import warnings
warnings.warn("Importing cura.PrinterOutputDevice has been deprecated since 4.1, use cura.PrinterOutput.PrinterOutputDevice instead", DeprecationWarning, stacklevel=2)
# We moved the PrinterOutput device to it's own submodule.
from cura.PrinterOutput.PrinterOutputDevice import PrinterOutputDevice, ConnectionState