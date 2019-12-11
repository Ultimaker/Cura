

from unittest.mock import MagicMock

import pytest

from cura.PrinterOutput.Models.PrintJobOutputModel import PrintJobOutputModel
from cura.PrinterOutput.Models.PrinterConfigurationModel import PrinterConfigurationModel
from cura.PrinterOutput.Models.PrinterOutputModel import PrinterOutputModel
from cura.PrinterOutput.Peripheral import Peripheral

test_validate_data_get_set = [
    {"attribute": "name", "value": "YAY"},
    {"attribute": "targetBedTemperature", "value": 192},
    {"attribute": "cameraUrl", "value": "YAY!"}
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


def test_peripherals():
    model = PrinterOutputModel(MagicMock())
    model.peripheralsChanged = MagicMock()

    peripheral = MagicMock(spec=Peripheral)
    peripheral.name = "test"
    peripheral2 = MagicMock(spec=Peripheral)
    peripheral2.name = "test2"

    model.addPeripheral(peripheral)
    assert model.peripheralsChanged.emit.call_count == 1
    model.addPeripheral(peripheral2)
    assert model.peripheralsChanged.emit.call_count == 2

    assert model.peripherals == "test, test2"

    model.removePeripheral(peripheral)
    assert model.peripheralsChanged.emit.call_count == 3
    assert model.peripherals == "test2"


def test_availableConfigurations_addConfiguration():
    model = PrinterOutputModel(MagicMock())

    configuration = MagicMock(spec = PrinterConfigurationModel)

    model.addAvailableConfiguration(configuration)
    assert model.availableConfigurations == [configuration]


def test_availableConfigurations_addConfigTwice():
    model = PrinterOutputModel(MagicMock())

    configuration = MagicMock(spec=PrinterConfigurationModel)

    model.setAvailableConfigurations([configuration])
    assert model.availableConfigurations == [configuration]

    # Adding it again should not have any effect
    model.addAvailableConfiguration(configuration)
    assert model.availableConfigurations == [configuration]


def test_availableConfigurations_removeConfig():
    model = PrinterOutputModel(MagicMock())

    configuration = MagicMock(spec=PrinterConfigurationModel)

    model.addAvailableConfiguration(configuration)
    model.removeAvailableConfiguration(configuration)
    assert model.availableConfigurations == []


def test_removeAlreadyRemovedConfiguration():
    model = PrinterOutputModel(MagicMock())

    configuration = MagicMock(spec=PrinterConfigurationModel)
    model.availableConfigurationsChanged = MagicMock()
    model.removeAvailableConfiguration(configuration)
    assert model.availableConfigurationsChanged.emit.call_count == 0
    assert model.availableConfigurations == []

