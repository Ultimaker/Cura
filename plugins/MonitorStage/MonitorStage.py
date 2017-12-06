# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import os.path
from UM.Application import Application
from UM.Resources import Resources
from cura.Stages.CuraStage import CuraStage


##  Stage for monitoring a 3D printing while it's printing.
class MonitorStage(CuraStage):

    def __init__(self):
        super().__init__()
        Application.getInstance().engineCreatedSignal.connect(self._engineCreated)
        # TODO: connect output device state to icon source

    def _engineCreated(self):
        # Note: currently the sidebar component for prepare and monitor stages is the same, this will change with the printer output device refactor!
        sidebar_component_path = os.path.join(Resources.getPath(Application.getInstance().ResourceTypes.QmlFiles), "Sidebar.qml")
        sidebar_component = Application.getInstance().createQmlComponent(sidebar_component_path)
        self.addDisplayComponent("sidebar", sidebar_component)
        self.setIconSource(Application.getInstance().getTheme().getIcon("tab_status_connected"))
