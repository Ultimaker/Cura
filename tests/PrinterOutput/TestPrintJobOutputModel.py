from unittest.mock import MagicMock

import pytest

from cura.PrinterOutput.ConfigurationModel import ConfigurationModel
from cura.PrinterOutput.PrintJobOutputModel import PrintJobOutputModel
from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel

test_validate_data_get_set = [
    {"attribute": "compatibleMachineFamilies", "value": ["yay"]},
]

test_validate_data_get_update = [
    {"attribute": "configuration", "value": ConfigurationModel()},
    {"attribute": "owner", "value": "WHOO"},
    {"attribute": "assignedPrinter", "value": PrinterOutputModel(MagicMock())},
    {"attribute": "key", "value": "YAY"},
    {"attribute": "name", "value": "Turtles"},
    {"attribute": "timeTotal", "value": 10},
    {"attribute": "timeElapsed", "value": 20},
    {"attribute": "state", "value": "BANANNA!"},
]


@pytest.mark.parametrize("data", test_validate_data_get_set)
def test_getAndSet(data):
    model = PrintJobOutputModel(MagicMock())

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
    model = PrintJobOutputModel(MagicMock())

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
