# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import os.path
from UM.Application import Application
from UM.PluginRegistry import PluginRegistry
from UM.Resources import Resources
from cura.Stages.CuraStage import CuraStage


##  Stage for monitoring a 3D printing while it's printing.
class MonitorStage(CuraStage):

    def __init__(self, parent = None):
        super().__init__(parent)

        # Wait until QML engine is created, otherwise creating the new QML components will fail
        Application.getInstance().engineCreatedSignal.connect(self._setComponents)

        # TODO: connect output device state to icon source

    def _setComponents(self):
        self._setMainOverlay()
        self._setSidebar()
        self._setIconSource()

    def _setMainOverlay(self):
        main_component_path = os.path.join(PluginRegistry.getInstance().getPluginPath("MonitorStage"), "MonitorMainView.qml")
        self.addDisplayComponent("main", main_component_path)

    def _setSidebar(self):
        # Note: currently the sidebar component for prepare and monitor stages is the same, this will change with the printer output device refactor!
        sidebar_component_path = os.path.join(Resources.getPath(Application.getInstance().ResourceTypes.QmlFiles), "Sidebar.qml")
        self.addDisplayComponent("sidebar", sidebar_component_path)

    def _setIconSource(self):
        if Application.getInstance().getTheme() is not None:
            self.setIconSource(Application.getInstance().getTheme().getIcon("tab_status_connected"))

# property string iconSource:
# //            {
# //                if (!printerConnected)
# //                {
# //                    return UM.Theme.getIcon("tab_status_unknown");
# //                }
# //                else if (!printerAcceptsCommands)
# //                {
# //                    return UM.Theme.getIcon("tab_status_unknown");
# //                }
# //
# //                if (Cura.MachineManager.printerOutputDevices[0].printerState == "maintenance")
# //                {
# //                    return UM.Theme.getIcon("tab_status_busy");
# //                }
# //
# //                switch (Cura.MachineManager.printerOutputDevices[0].jobState)
# //                {
# //                    case "printing":
# //                    case "pre_print":
# //                    case "pausing":
# //                    case "resuming":
# //                        return UM.Theme.getIcon("tab_status_busy");
# //                    case "wait_cleanup":
# //                        return UM.Theme.getIcon("tab_status_finished");
# //                    case "ready":
# //                    case "":
# //                        return UM.Theme.getIcon("tab_status_connected")
# //                    case "paused":
# //                        return UM.Theme.getIcon("tab_status_paused")
# //                    case "error":
# //                        return UM.Theme.getIcon("tab_status_stopped")
# //                    default:
# //                        return UM.Theme.getIcon("tab_status_unknown")
# //                }
# //            }