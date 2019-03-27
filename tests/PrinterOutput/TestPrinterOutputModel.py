

from unittest.mock import MagicMock

import pytest

from cura.PrinterOutput.PrintJobOutputModel import PrintJobOutputModel
from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel

test_validate_data_get_set = [
    {"attribute": "name", "value": "YAY"},
    {"attribute": "targetBedTemperature", "value": 192},
]

test_validate_data_get_update = [
    {"attribute": "isPreheating", "value": True},
    {"attribute": "type", "value": "WHOO"},
    {"attribute": "buildplate", "value": "NFHA"},
    {"attribute": "key", "value": "YAY"},
    {"attribute": "name", "value": "Turtles"},
    {"attribute": "bedTemperature", "value": 200},
    {"attribute": "targetBedTemperature", "value": 9001},
    {"attribute": "activePrintJob", "value": PrintJobOutputModel(MagicMock())},
    {"attribute": "state", "value": "BEEPBOOP"},
]


@pytest.mark.parametrize("data", test_validate_data_get_set)
def test_getAndSet(data):
    model = PrinterOutputModel(MagicMock())

    # Convert the first letter into a capital
    attribute = list(data["attribute"])
    attribute[0] = attribute[0].capitalize()
    attribute = "".join(attribute)

    # mock the correct emit
    setattr(model, data["attribute"] + "Changed", MagicMock())

    # Attempt to set the value
    getattr(model, "set" + attribute)(data["value"])

    # Check if signal fired.
    signal = getattr(model, data["attribute"] + "Changed")
    assert signal.emit.call_count == 1

    # Ensure that the value got set
    assert getattr(model, data["attribute"]) == data["value"]

    # Attempt to set the value again
    getattr(model, "set" + attribute)(data["value"])
    # The signal should not fire again
    assert signal.emit.call_count == 1


@pytest.mark.parametrize("data", test_validate_data_get_update)
def test_getAndUpdate(data):
    model = PrinterOutputModel(MagicMock())

    # Convert the first letter into a capital
    attribute = list(data["attribute"])
    attribute[0] = attribute[0].capitalize()
    attribute = "".join(attribute)

    # mock the correct emit
    setattr(model, data["attribute"] + "Changed", MagicMock())

    # Attempt to set the value
    getattr(model, "update" + attribute)(data["value"])

    # Check if signal fired.
    signal = getattr(model, data["attribute"] + "Changed")
    assert signal.emit.call_count == 1

    # Ensure that the value got set
    assert getattr(model, data["attribute"]) == data["value"]

    # Attempt to set the value again
    getattr(model, "update" + attribute)(data["value"])
    # The signal should not fire again
    assert signal.emit.call_count == 1
