from unittest.mock import MagicMock

import pytest
from unittest.mock import patch

from cura.PrinterOutput.Models.ExtruderConfigurationModel import ExtruderConfigurationModel
from cura.PrinterOutput.Models.MaterialOutputModel import MaterialOutputModel
from cura.PrinterOutput.Models.PrinterConfigurationModel import PrinterConfigurationModel
from cura.PrinterOutput.Models.PrinterOutputModel import PrinterOutputModel
from cura.PrinterOutput.PrinterOutputDevice import PrinterOutputDevice

test_validate_data_get_set = [
    {"attribute": "connectionText", "value": "yay"},
    {"attribute": "connectionState", "value": 1},
]

@pytest.fixture()
def printer_output_device():
    with patch("UM.Application.Application.getInstance"):
        return PrinterOutputDevice("whatever")


@pytest.mark.parametrize("data", test_validate_data_get_set)
def test_getAndSet(data, printer_output_device):
    model = printer_output_device

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


def test_uniqueConfigurations(printer_output_device):
    printer = PrinterOutputModel(MagicMock())
    # Add a printer and fire the signal that ensures they get hooked up correctly.
    printer_output_device._printers = [printer]
    printer_output_device._onPrintersChanged()

    assert printer_output_device.uniqueConfigurations == []
    configuration = PrinterConfigurationModel()
    printer.addAvailableConfiguration(configuration)

    assert printer_output_device.uniqueConfigurations == [configuration]

    # Once the type of printer is set, it's active configuration counts as being set.
    # In that case, that should also be added to the list of available configurations
    printer.updateType("blarg!")
    loaded_material = MaterialOutputModel(guid = "", type = "PLA", color = "Blue", brand = "Generic", name = "Blue PLA")
    loaded_left_extruder = ExtruderConfigurationModel(0)
    loaded_left_extruder.setMaterial(loaded_material)
    loaded_right_extruder = ExtruderConfigurationModel(1)
    loaded_right_extruder.setMaterial(loaded_material)
    printer.printerConfiguration.setExtruderConfigurations([loaded_left_extruder, loaded_right_extruder])
    assert printer_output_device.uniqueConfigurations == [configuration, printer.printerConfiguration]


def test_uniqueConfigurations_empty_is_filtered_out(printer_output_device):
    printer = PrinterOutputModel(MagicMock())
    # Add a printer and fire the signal that ensures they get hooked up correctly.
    printer_output_device._printers = [printer]
    printer_output_device._onPrintersChanged()

    printer.updateType("blarg!")
    empty_material = MaterialOutputModel(guid = "", type = "empty", color = "empty", brand = "Generic", name = "Empty")
    empty_left_extruder = ExtruderConfigurationModel(0)
    empty_left_extruder.setMaterial(empty_material)
    empty_right_extruder = ExtruderConfigurationModel(1)
    empty_right_extruder.setMaterial(empty_material)
    printer.printerConfiguration.setExtruderConfigurations([empty_left_extruder, empty_right_extruder])
    assert printer_output_device.uniqueConfigurations == []
