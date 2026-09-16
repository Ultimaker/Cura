import sys
import os.path
from typing import Dict, Optional
import pytest

from unittest.mock import patch, MagicMock, PropertyMock

from UM.PackageManager import PackageManager
from cura.CuraApplication import CuraApplication

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import ThreeMFWriter

PLUGIN_ID = "my_plugin"
DISPLAY_NAME = "MyPlugin"
PACKAGE_VERSION = "0.0.1"
SDK_VERSION = "8.0.0"


@pytest.fixture
def package_manager() -> MagicMock:
    pm = MagicMock(spec=PackageManager)
    pm.getInstalledPackageInfo.return_value = {
        "display_name": DISPLAY_NAME,
        "package_version": PACKAGE_VERSION,
        "sdk_version_semver": SDK_VERSION
    }
    return pm


@pytest.fixture
def machine_manager() -> MagicMock:
    mm = MagicMock(spec=PackageManager)
    active_machine = MagicMock()
    active_machine.getAllKeys.return_value = ["infill_pattern", "layer_height", "material_bed_temperature"]
    active_machine.getProperty.return_value = f"PLUGIN::{PLUGIN_ID}@{PACKAGE_VERSION}::custom_value"
    active_machine.getContainers.return_value = []
    active_machine.extruderList = []
    mm.activeMachine = active_machine
    return mm


@pytest.fixture
def application(package_manager, machine_manager):
    app = MagicMock()
    app.getPackageManager.return_value = package_manager
    app.getMachineManager.return_value = machine_manager
    return app


def test_enumParsing(application):
    with patch("cura.CuraApplication.CuraApplication.getInstance", MagicMock(return_value=application)):
        packages_metadata = ThreeMFWriter.ThreeMFWriter._getPluginPackageMetadata()[0]

        assert packages_metadata.get("id") == PLUGIN_ID
        assert packages_metadata.get("display_name") == DISPLAY_NAME
        assert packages_metadata.get("package_version") == PACKAGE_VERSION
        assert packages_metadata.get("sdk_version_semver") == SDK_VERSION
        assert packages_metadata.get("type") == "plugin"
