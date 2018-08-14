# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

# The purpose of this class is to create fixtures or methods that can be shared among all tests.

import pytest
from UM.Qt.QtApplication import QtApplication #QTApplication import is required, even though it isn't used.
from cura.CuraApplication import CuraApplication
from cura.MachineActionManager import MachineActionManager

# Create a CuraApplication object that will be shared among all tests. It needs to be initialized.
# Since we need to use it more that once, we create the application the first time and use its instance afterwards.
@pytest.fixture()
def application() -> CuraApplication:
    application = CuraApplication.getInstance()
    if application is None:
        application = CuraApplication()
        application.initialize()
    return application

# Returns a MachineActionManager instance.
@pytest.fixture()
def machine_action_manager(application) -> MachineActionManager:
    return application.getMachineActionManager()

# @pytest.fixture()
# def plugin_registry(application):
#     PluginRegistry._PluginRegistry__instance = None
#     plugin_registry = PluginRegistry(application)
#     plugin_registry._plugin_locations = [] # Clear pre-defined plugin locations
#     return plugin_registry
#
# @pytest.fixture()
# def upgrade_manager(application):
#     VersionUpgradeManager._VersionUpgradeManager__instance = None
#     upgrade_manager = VersionUpgradeManager(application)
#     return upgrade_manager

