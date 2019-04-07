# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

# The purpose of this class is to create fixtures or methods that can be shared among all tests.

import unittest.mock
import pytest

# Prevents error: "PyCapsule_GetPointer called with incorrect name" with conflicting SIP configurations between Arcus and PyQt: Import Arcus and Savitar first!
import Savitar  # Dont remove this line
import Arcus  # No really. Don't. It needs to be there!
from UM.Qt.QtApplication import QtApplication  # QtApplication import is required, even though it isn't used.
# Even though your IDE says these files are not used, don't believe it. It's lying. They need to be there.

from cura.CuraApplication import CuraApplication
from cura.UI.MachineActionManager import MachineActionManager

# Create a CuraApplication object that will be shared among all tests. It needs to be initialized.
# Since we need to use it more that once, we create the application the first time and use its instance afterwards.
@pytest.fixture()
def application() -> CuraApplication:
    app = unittest.mock.MagicMock()
    return app

# Returns a MachineActionManager instance.
@pytest.fixture()
def machine_action_manager(application) -> MachineActionManager:
    return MachineActionManager(application)
