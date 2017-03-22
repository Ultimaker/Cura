# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import os.path #To find the test files.
import pytest #This module contains unit tests.
import unittest.mock #To monkeypatch some mocks in place of dependencies.

from cura.Settings.GlobalStack import GlobalStack #The module we're testing.
from UM.Settings.DefinitionContainer import DefinitionContainer #To test against the class DefinitionContainer.
import UM.Settings.ContainerRegistry

##  Tests whether the user changes are being read properly from a global stack.
@pytest.mark.parametrize("filename, user_changes_id", [
                        ("Global.global.cfg", "empty"),
                        ("Global.stack.cfg", "empty"),
                        ("MachineLegacy.stack.cfg", "empty")
])
def test_deserializeUserChanges(filename, user_changes_id):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "stacks", filename)) as file_handle:
        serialized = file_handle.read()
    stack = GlobalStack("TestStack")

    #Mock the loading of the instances.
    def findContainer(container_id = "*", container_type = None, type = None, category = "*"):
        if id == "some_material":
            return UM.Settings.ContainerRegistry._EmptyInstanceContainer(id)
        if container_type == DefinitionContainer:
            return unittest.mock.MagicMock()
    stack.findContainer = findContainer

    stack.deserialize(serialized)

    assert stack.userChanges.getId() == user_changes_id