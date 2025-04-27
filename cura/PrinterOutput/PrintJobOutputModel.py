# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import warnings
warnings.warn("Importing cura.PrinterOutput.PrintJobOutputModel has been deprecated since 4.1, use cura.PrinterOutput.Models.PrintJobOutputModel instead", DeprecationWarning, stacklevel=2)
# We moved the the models to one submodule deeper
from cura.PrinterOutput.Models.PrintJobOutputModel import PrintJobOutputModel