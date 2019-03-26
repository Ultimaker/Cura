

from unittest.mock import MagicMock

import pytest

from cura.PrinterOutput.Models.PrinterConfigurationModel import PrinterConfigurationModel
from cura.PrinterOutput.Models.ExtruderConfigurationModel import ExtruderConfigurationModel

test_validate_data_get_set = [
    {"attribute": "extruderConfigurations", "value": [ExtruderConfigurationModel()]},
    {"attribute": "buildplateConfiguration", "value": "BHDHAHHADAD"},
    {"attribute": "printerType", "value": ":(", "check_signal": False},
]


@pytest.mark.parametrize("data", test_validate_data_get_set)
def test_getAndSet(data):
    model = PrinterConfigurationModel()

    # Convert the first letter into a capital
    attribute = list(data["attribute"])
    attribute[0] = attribute[0].capitalize()
    attribute = "".join(attribute)

    # mock the correct emit
    model.configurationChanged = MagicMock()
    signal = model.configurationChanged

    # Attempt to set the value
    getattr(model, "set" + attribute)(data["value"])

    # Check if signal fired.
    if data.get("check_signal", True):
        assert signal.emit.call_count == 1

    # Ensure that the value got set
    assert getattr(model, data["attribute"]) == data["value"]

    # Attempt to set the value again
    getattr(model, "set" + attribute)(data["value"])

    # The signal should not fire again
    if data.get("check_signal", True):
        assert signal.emit.call_count == 1
