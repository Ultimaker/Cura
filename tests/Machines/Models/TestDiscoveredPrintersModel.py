from unittest.mock import MagicMock, PropertyMock

import pytest

from cura.Machines.Models.DiscoveredPrintersModel import DiscoveredPrintersModel


@pytest.fixture()
def discovered_printer_model(application) -> DiscoveredPrintersModel:
    return DiscoveredPrintersModel()


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

    # Test if removing it works
    discovered_printer_model.removeDiscoveredPrinter("ip")
    assert len(discovered_printer_model.discoveredPrinters) == 0
