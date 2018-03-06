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
        Application.getInstance().engineCreatedSignal.connect(self._onEngineCreated)
        self._printer_output_device = None

        self._active_print_job = None
        self._active_printer = None

    def _setActivePrintJob(self, print_job):
        if self._active_print_job != print_job:
            if self._active_print_job:
                self._active_print_job.stateChanged.disconnect(self._updateIconSource)
            self._active_print_job = print_job
            if self._active_print_job:
                self._active_print_job.stateChanged.connect(self._updateIconSource)

            # Ensure that the right icon source is returned.
            self._updateIconSource()

    def _setActivePrinter(self, printer):
        if self._active_printer != printer:
            if self._active_printer:
                self._active_printer.activePrintJobChanged.disconnect(self._onActivePrintJobChanged)
            self._active_printer = printer
            if self._active_printer:
                self._setActivePrintJob(self._active_printer.activePrintJob)
                # Jobs might change, so we need to listen to it's changes.
                self._active_printer.activePrintJobChanged.connect(self._onActivePrintJobChanged)
            else:
                self._setActivePrintJob(None)

            # Ensure that the right icon source is returned.
            self._updateIconSource()

    def _onActivePrintJobChanged(self):
        self._setActivePrintJob(self._active_printer.activePrintJob)

    def _onActivePrinterChanged(self):
        self._setActivePrinter(self._printer_output_device.activePrinter)

    def _onOutputDevicesChanged(self):
        try:
            # We assume that you are monitoring the device with the highest priority.
            new_output_device = Application.getInstance().getMachineManager().printerOutputDevices[0]
            if new_output_device != self._printer_output_device:
                if self._printer_output_device:
                    self._printer_output_device.acceptsCommandsChanged.disconnect(self._updateIconSource)
                    self._printer_output_device.connectionStateChanged.disconnect(self._updateIconSource)
                    self._printer_output_device.printersChanged.disconnect(self._onActivePrinterChanged)

                self._printer_output_device = new_output_device

                self._printer_output_device.acceptsCommandsChanged.connect(self._updateIconSource)
                self._printer_output_device.printersChanged.connect(self._onActivePrinterChanged)
                self._printer_output_device.connectionStateChanged.connect(self._updateIconSource)
                self._setActivePrinter(self._printer_output_device.activePrinter)

            # Force an update of the icon source
            self._updateIconSource()
        except IndexError:
            #If index error occurs, then the icon on monitor button also should be updated
            self._updateIconSource()
            pass

    def _onEngineCreated(self):
        # We can only connect now, as we need to be sure that everything is loaded (plugins get created quite early)
        Application.getInstance().getMachineManager().outputDevicesChanged.connect(self._onOutputDevicesChanged)
        self._onOutputDevicesChanged()
        self._updateMainOverlay()
        self._updateSidebar()
        self._updateIconSource()

    def _updateMainOverlay(self):
        main_component_path = os.path.join(PluginRegistry.getInstance().getPluginPath("MonitorStage"), "MonitorMainView.qml")
        self.addDisplayComponent("main", main_component_path)

    def _updateSidebar(self):
        # TODO: currently the sidebar component for prepare and monitor stages is the same, this will change with the printer output device refactor!
        sidebar_component_path = os.path.join(Resources.getPath(Application.getInstance().ResourceTypes.QmlFiles), "Sidebar.qml")
        self.addDisplayComponent("sidebar", sidebar_component_path)

    def _updateIconSource(self):
        if Application.getInstance().getTheme() is not None:
            icon_name = self._getActiveOutputDeviceStatusIcon()
            self.setIconSource(Application.getInstance().getTheme().getIcon(icon_name))

    ##  Find the correct status icon depending on the active output device state
    def _getActiveOutputDeviceStatusIcon(self):
        # We assume that you are monitoring the device with the highest priority.
        try:
            output_device = Application.getInstance().getMachineManager().printerOutputDevices[0]
        except IndexError:
            return "tab_status_unknown"

        if not output_device.acceptsCommands:
            return "tab_status_unknown"

        if output_device.activePrinter is None:
            return "tab_status_connected"

        # TODO: refactor to use enum instead of hardcoded strings?
        if output_device.activePrinter.state == "maintenance":
            return "tab_status_busy"

        if output_device.activePrinter.activePrintJob is None:
            return "tab_status_connected"

        if output_device.activePrinter.activePrintJob.state in ["printing", "pre_print", "pausing", "resuming"]:
            return "tab_status_busy"

        if output_device.activePrinter.activePrintJob.state == "wait_cleanup":
            return "tab_status_finished"

        if output_device.activePrinter.activePrintJob.state in ["ready", ""]:
            return "tab_status_connected"

        if output_device.activePrinter.activePrintJob.state == "paused":
            return "tab_status_paused"

        if output_device.activePrinter.activePrintJob.state == "error":
            return "tab_status_stopped"

        return "tab_status_unknown"
