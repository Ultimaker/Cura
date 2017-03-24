# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import pytest #This module contains automated tests.
import unittest.mock #For the mocking and monkeypatching functionality.

import cura.Settings.ExtruderStack #The module we're testing.
from cura.Settings.Exceptions import InvalidOperationError #To check whether the correct exceptions are raised.

##  An empty extruder stack to test with.
@pytest.fixture()
def extruder_stack() -> cura.Settings.ExtruderStack.ExtruderStack:
    return cura.Settings.ExtruderStack.ExtruderStack

##  Tests whether adding a container is properly forbidden.
def test_addContainer(extruder_stack):
    with pytest.raises(InvalidOperationError):
        extruder_stack.addContainer(unittest.mock.MagicMock())

##  Tests whether inserting a container is properly forbidden.
def test_insertContainer(extruder_stack):
    with pytest.raises(InvalidOperationError):
        extruder_stack.insertContainer(0, unittest.mock.MagicMock())

##  Tests whether removing a container is properly forbidden.
def test_removeContainer(extruder_stack):
    with pytest.raises(InvalidOperationError):
        extruder_stack.removeContainer(unittest.mock.MagicMock())