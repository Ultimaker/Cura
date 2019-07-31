
from unittest.mock import MagicMock, patch


def createMockedExtruder(extruder_id):
    extruder = MagicMock()
    extruder.getId = MagicMock(return_value = extruder_id)
    return extruder


def test_getAllExtruderSettings(extruder_manager):
    extruder_1 = createMockedExtruder("extruder_1")
    extruder_1.getProperty = MagicMock(return_value ="beep")
    extruder_2 = createMockedExtruder("extruder_2")
    extruder_2.getProperty = MagicMock(return_value="zomg")
    extruder_manager.getActiveExtruderStacks = MagicMock(return_value = [extruder_1, extruder_2])
    assert extruder_manager.getAllExtruderSettings("whatever", "value") == ["beep", "zomg"]


def test_registerExtruder(extruder_manager):
    extruder = createMockedExtruder("beep")
    extruder.getMetaDataEntry = MagicMock(return_value = "0")  # because the extruder position gets called

    extruder_manager.extrudersChanged = MagicMock()
    extruder_manager.registerExtruder(extruder, "zomg")

    assert extruder_manager.extrudersChanged.emit.call_count == 1

    # Doing it again should not trigger anything
    extruder_manager.registerExtruder(extruder, "zomg")
    assert extruder_manager.extrudersChanged.emit.call_count == 1
