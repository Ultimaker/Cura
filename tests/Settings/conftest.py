# Copyright (c) 2018 Ultimaker B.V.
# Uranium is released under the terms of the LGPLv3 or higher.

# The purpose of this class is to create fixtures or methods that can be shared among all settings tests.

import pytest

from UM.Settings.DefinitionContainer import DefinitionContainer #To provide definition containers in the registry fixtures.
from UM.Settings.InstanceContainer import InstanceContainer
from cura.Settings.CuraContainerRegistry import CuraContainerRegistry
from cura.Settings.ExtruderStack import ExtruderStack
from cura.Settings.GlobalStack import GlobalStack
import cura.Settings.CuraContainerStack

# Returns the CuraContainerRegistry instance with some empty containers.
@pytest.fixture()
def container_registry(application) -> CuraContainerRegistry:
    return application.getContainerRegistry()

# Gives an arbitrary definition container.
@pytest.fixture()
def definition_container() -> DefinitionContainer:
    return DefinitionContainer(container_id = "Test Definition")

#An empty global stack to test with.
@pytest.fixture()
def global_stack() -> GlobalStack:
    global_stack = GlobalStack("TestGlobalStack")
    # There is a restriction here that the definition changes cannot be an empty container. Added in CURA-5281
    definition_changes_container = InstanceContainer(container_id = "InstanceContainer")
    definition_changes_container.setMetaDataEntry("type", "definition_changes")
    global_stack._containers[cura.Settings.CuraContainerStack._ContainerIndexes.DefinitionChanges] = definition_changes_container
    return global_stack

##  An empty extruder stack to test with.
@pytest.fixture()
def extruder_stack() -> ExtruderStack:
    extruder_stack= ExtruderStack("TestExtruderStack")
    # There is a restriction here that the definition changes cannot be an empty container. Added in CURA-5281
    definition_changes_container = InstanceContainer(container_id = "InstanceContainer")
    definition_changes_container.setMetaDataEntry("type", "definition_changes")
    extruder_stack._containers[cura.Settings.CuraContainerStack._ContainerIndexes.DefinitionChanges] = definition_changes_container
    return extruder_stack