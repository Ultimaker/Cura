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

        # Update the status icon when the output device is changed
        Application.getInstance().getOutputDeviceManager().activeDeviceChanged.connect(self._setIconSource)

    def _setComponents(self):
        self._setMainOverlay()
        self._setSidebar()
        self._setIconSource()

    def _setMainOverlay(self):
        main_component_path = os.path.join(PluginRegistry.getInstance().getPluginPath("MonitorStage"), "MonitorMainView.qml")
        self.addDisplayComponent("main", main_component_path)

    def _setSidebar(self):
        # TODO: currently the sidebar component for prepare and monitor stages is the same, this will change with the printer output device refactor!
        sidebar_component_path = os.path.join(Resources.getPath(Application.getInstance().ResourceTypes.QmlFiles), "Sidebar.qml")
        self.addDisplayComponent("sidebar", sidebar_component_path)

    def _setIconSource(self):
        if Application.getInstance().getTheme() is not None:
            icon_name = self._getActiveOutputDeviceStatusIcon()
            self.setIconSource(Application.getInstance().getTheme().getIcon(icon_name))

    ##  Find the correct status icon depending on the active output device state
    def _getActiveOutputDeviceStatusIcon(self):
        output_device = Application.getInstance().getOutputDeviceManager().getActiveDevice()

        if not output_device:
            return "tab_status_unknown"

        if hasattr(output_device, "acceptsCommands") and not output_device.acceptsCommands:
            return "tab_status_unknown"

        if not hasattr(output_device, "printerState") or not hasattr(output_device, "jobState"):
            return "tab_status_unknown"

        # TODO: refactor to use enum instead of hardcoded strings?
        if output_device.printerState == "maintenance":
            return "tab_status_busy"

        if output_device.jobState in ["printing", "pre_print", "pausing", "resuming"]:
            return "tab_status_busy"

        if output_device.jobState == "wait_cleanup":
            return "tab_status_finished"

        if output_device.jobState in ["ready", ""]:
            return "tab_status_connected"

        if output_device.jobState == "paused":
            return "tab_status_paused"

        if output_device.jobState == "error":
            return "tab_status_stopped"

        return "tab_status_unknown"
