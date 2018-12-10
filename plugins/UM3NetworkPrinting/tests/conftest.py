# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import pytest
from UM.Signal import Signal

from cura.CuraApplication import CuraApplication
from cura.Machines.MaterialManager import MaterialManager


# This mock application must extend from Application and not QtApplication otherwise some QObjects are created and
# a segfault is raised.
class FixtureApplication(CuraApplication):
    def __init__(self):
        super().__init__()
        super().initialize()
        Signal._signalQueue = self

        self.getPreferences().addPreference("cura/favorite_materials", "")

        self._material_manager = MaterialManager(self._container_registry, parent = self)
        self._material_manager.initialize()

    def functionEvent(self, event):
        event.call()

    def parseCommandLine(self):
        pass

    def processEvents(self):
        pass


@pytest.fixture(autouse=True)
def application():
    # Since we need to use it more that once, we create the application the first time and use its instance the second
    application = FixtureApplication.getInstance()
    if application is None:
        application = FixtureApplication()
    return application
