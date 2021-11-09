from unittest.mock import MagicMock, PropertyMock

import pytest

from cura.Machines.Models.DiscoveredPrintersModel import DiscoveredPrintersModel, DiscoveredPrinter


@pytest.fixture()
def discovered_printer_model(application) -> DiscoveredPrintersModel:
    return DiscoveredPrintersModel(application)

@pytest.fixture()
def discovered_printer() -> DiscoveredPrinter:
    return DiscoveredPrinter("127.0.0.1", "zomg", "yay", None, "bleep", MagicMock())


@pytest.mark.skip  # TODO: This has some unknown dependency on the application / registry, which is hard to patch out. (which doesn't mean we shouldn't fix it!)
def test_discoveredPrinters(discovered_printer_model):
    mocked_device = MagicMock()
    cluster_size = PropertyMock(return_value = 1)
    type(mocked_device).clusterSize = cluster_size

    mocked_callback = MagicMock()
    discovered_printer_model.addDiscoveredPrinter("ip", "key", "name", mocked_callback, "machine_type", mocked_device)
    device = discovered_printer_model.discoveredPrinters[0]
    discovered_printer_model.createMachineFromDiscoveredPrinter(device)
    mocked_callback.assert_called_with("key")

    assert len(discovered_printer_model.discoveredPrinters) == 1

    discovered_printer_model.discoveredPrintersChanged = MagicMock()
    # Test if removing it works
    discovered_printer_model.removeDiscoveredPrinter("ip")
    assert len(discovered_printer_model.discoveredPrinters) == 0
    assert discovered_printer_model.discoveredPrintersChanged.emit.call_count == 1
    # Removing it again shouldn't cause another signal emit
    discovered_printer_model.removeDiscoveredPrinter("ip")
    assert discovered_printer_model.discoveredPrintersChanged.emit.call_count == 1


test_validate_data_get_set = [
    {"attribute": "name", "value": "zomg"},
    {"attribute": "machineType", "value": "BHDHAHHADAD"},
]

@pytest.mark.parametrize("data", test_validate_data_get_set)
def test_getAndSet(data, discovered_printer):
    # Attempt to set the value
    # Convert the first letter into a capital
    attribute = list(data["attribute"])
    attribute[0] = attribute[0].capitalize()
    attribute = "".join(attribute)

    # Attempt to set the value
    getattr(discovered_printer, "set" + attribute)(data["value"])

    # Ensure that the value got set
    assert getattr(discovered_printer, data["attribute"]) == data["value"]


def test_isHostofGroup(discovered_printer):
    discovered_printer.device.clusterSize = 0
    assert not discovered_printer.isHostOfGroup
    discovered_printer.device.clusterSize = 2
    assert discovered_printer.isHostOfGroup