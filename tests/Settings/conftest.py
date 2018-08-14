# Copyright (c) 2018 Ultimaker B.V.
# Uranium is released under the terms of the LGPLv3 or higher.

# The purpose of this class is to create fixtures or methods that can be shared among all settings tests.

import pytest
import copy

from UM.Settings.DefinitionContainer import DefinitionContainer #To provide definition containers in the registry fixtures.

# Returns the CuraContainerRegistry instance with some empty containers.
@pytest.fixture()
def container_registry(application):
    return application.getContainerRegistry()

# Gives an arbitrary definition container.
@pytest.fixture()
def definition_container():
    return DefinitionContainer(container_id = "Test Definition")