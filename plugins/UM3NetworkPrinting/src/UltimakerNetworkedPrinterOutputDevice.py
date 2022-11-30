# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import os
from time import time
from typing import List, Optional, Dict

from PyQt6.QtCore import pyqtProperty, pyqtSignal, QObject, pyqtSlot, QUrl

from UM.Logger import Logger
from UM.Qt.Duration import Duration, DurationFormat
from cura.CuraApplication import CuraApplication
from cura.PrinterOutput.Models.PrinterOutputModel import PrinterOutputModel
from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice, AuthState
from cura.PrinterOutput.PrinterOutputDevice import ConnectionType, ConnectionState

from .Utils import formatTimeCompleted, formatDateCompleted
from .ClusterOutputController import ClusterOutputController
from .Messages.PrintJobUploadProgressMessage import PrintJobUploadProgressMessage
from .Messages.NotClusterHostMessage import NotClusterHostMessage
from .Models.UM3PrintJobOutputModel import UM3PrintJobOutputModel
from .Models.Http.ClusterPrinterStatus import ClusterPrinterStatus
from .Models.Http.ClusterPrintJobStatus import ClusterPrintJobStatus


class UltimakerNetworkedPrinterOutputDevice(NetworkedPrinterOutputDevice):
    """Output device class that forms the basis of Ultimaker networked printer output devices.

    Currently used for local networking and cloud printing using Ultimaker Connect.
    This base class primarily contains all the Qt properties and slots needed for the monitor page to work.
    """

    META_NETWORK_KEY = "um_network_key"
    META_CLUSTER_ID = "um_cloud_cluster_id"

    # Signal emitted when the status of the print jobs for this cluster were changed over the network.
    printJobsChanged = pyqtSignal()

    # Signal emitted when the currently visible printer card in the UI was changed by the user.
    activePrinterChanged = pyqtSignal()

    # Notify can only use signals that are defined by the class that they are in, not inherited ones.
    # Therefore we create a private signal used to trigger the printersChanged signal.
    _clusterPrintersChanged = pyqtSignal()

    # States indicating if a print job is queued.
    QUEUED_PRINT_JOBS_STATES = {"queued", "error"}

    def __init__(self, device_id: str, address: str, properties: Dict[bytes, bytes], connection_type: ConnectionType,
                 parent=None) -> None:

        super().__init__(device_id=device_id, address=address, properties=properties, connection_type=connection_type,
                         parent=parent)
        # Trigger the printersChanged signal when the private signal is triggered.
        self.printersChanged.connect(self._clusterPrintersChanged)

        # Keeps track the last network response to determine if we are still connected.
        self._time_of_last_response = time()
        self._time_of_last_request = time()

        # Set the display name from the properties.
        self.setName(self.getProperty("name"))

        # Set the display name of the printer type.
        definitions = CuraApplication.getInstance().getContainerRegistry().findContainers(id = self.printerType)
        self._printer_type_name = definitions[0].getName() if definitions else ""

        # Keeps track of all printers in the cluster.
        self._printers = []  # type: List[PrinterOutputModel]
        self._has_received_printers = False

        # Keeps track of all print jobs in the cluster.
        self._print_jobs = []  # type: List[UM3PrintJobOutputModel]

        # Keep track of the printer currently selected in the UI.
        self._active_printer = None  # type: Optional[PrinterOutputModel]

        # By default we are not authenticated. This state will be changed later.
        self._authentication_state = AuthState.NotAuthenticated

        # Load the Monitor UI elements.
        self._loadMonitorTab()

        # The job upload progress message modal.
        self._progress = PrintJobUploadProgressMessage()

        self._timeout_time = 30

        self._num_is_host_check_failed = 0

    @pyqtProperty(str, constant=True)
    def address(self) -> str:
        """The IP address of the printer."""

        return self._address

    @pyqtProperty(str, constant=True)
    def printerTypeName(self) -> str:
        """The display name of the printer."""

        return self._printer_type_name

    # Get all print jobs for this cluster.
    @pyqtProperty("QVariantList", notify=printJobsChanged)
    def printJobs(self) -> List[UM3PrintJobOutputModel]:
        return self._print_jobs

    # Get all print jobs for this cluster that are queued.
    @pyqtProperty("QVariantList", notify=printJobsChanged)
    def queuedPrintJobs(self) -> List[UM3PrintJobOutputModel]:
        return [print_job for print_job in self._print_jobs if print_job.state in self.QUEUED_PRINT_JOBS_STATES]

    # Get all print jobs for this cluster that are currently printing.
    @pyqtProperty("QVariantList", notify=printJobsChanged)
    def activePrintJobs(self) -> List[UM3PrintJobOutputModel]:
        return [print_job for print_job in self._print_jobs if
                print_job.assignedPrinter is not None and print_job.state not in self.QUEUED_PRINT_JOBS_STATES]

    @pyqtProperty(bool, notify=_clusterPrintersChanged)
    def receivedData(self) -> bool:
        return self._has_received_printers

    # Get the amount of printers in the cluster.
    @pyqtProperty(int, notify=_clusterPrintersChanged)
    def clusterSize(self) -> int:
        if not self._has_received_printers:
            discovered_size = self.getProperty("cluster_size")
            if discovered_size == "":
                return 1  # prevent false positives for new devices
            return int(discovered_size)
        return len(self._printers)

    # Get the amount of printer in the cluster per type.
    @pyqtProperty("QVariantList", notify=_clusterPrintersChanged)
    def connectedPrintersTypeCount(self) -> List[Dict[str, str]]:
        printer_count = {}  # type: Dict[str, int]
        for printer in self._printers:
            if printer.type in printer_count:
                printer_count[printer.type] += 1
            else:
                printer_count[printer.type] = 1
        result = []
        for machine_type in printer_count:
            result.append({"machine_type": machine_type, "count": str(printer_count[machine_type])})
        return result

    # Get a list of all printers.
    @pyqtProperty("QVariantList", notify=_clusterPrintersChanged)
    def printers(self) -> List[PrinterOutputModel]:
        return self._printers

    # Get the currently active printer in the UI.
    @pyqtProperty(QObject, notify=activePrinterChanged)
    def activePrinter(self) -> Optional[PrinterOutputModel]:
        return self._active_printer

    # Set the currently active printer from the UI.
    @pyqtSlot(QObject, name="setActivePrinter")
    def setActivePrinter(self, printer: Optional[PrinterOutputModel]) -> None:
        if self.activePrinter == printer:
            return
        self._active_printer = printer
        self.activePrinterChanged.emit()

    @pyqtProperty(bool, constant=True)
    def supportsPrintJobActions(self) -> bool:
        """Whether the printer that this output device represents supports print job actions via the local network."""

        return True

    def setJobState(self, print_job_uuid: str, state: str) -> None:
        """Set the remote print job state."""

        raise NotImplementedError("setJobState must be implemented")

    @pyqtSlot(str, name="sendJobToTop")
    def sendJobToTop(self, print_job_uuid: str) -> None:
        raise NotImplementedError("sendJobToTop must be implemented")

    @pyqtSlot(str, name="deleteJobFromQueue")
    def deleteJobFromQueue(self, print_job_uuid: str) -> None:
        raise NotImplementedError("deleteJobFromQueue must be implemented")

    @pyqtSlot(str, name="forceSendJob")
    def forceSendJob(self, print_job_uuid: str) -> None:
        raise NotImplementedError("forceSendJob must be implemented")

    @pyqtProperty(bool, constant = True)
    def supportsPrintJobQueue(self) -> bool:
        """
        Whether this printer knows about queueing print jobs.
        """
        return True  # This API always supports print job queueing.

    @pyqtProperty(bool, constant = True)
    def canReadPrintJobs(self) -> bool:
        """
        Whether this user can read the list of print jobs and their properties.
        """
        return True

    @pyqtProperty(bool, constant = True)
    def canWriteOthersPrintJobs(self) -> bool:
        """
        Whether this user can change things about print jobs made by other
        people.
        """
        return True

    @pyqtProperty(bool, constant = True)
    def canWriteOwnPrintJobs(self) -> bool:
        """
        Whether this user can change things about print jobs made by themself.
        """
        return True

    @pyqtProperty(bool, constant = True)
    def canReadPrinterDetails(self) -> bool:
        """
        Whether this user can read the status of the printer.
        """
        return True

    @pyqtSlot(name="openPrintJobControlPanel")
    def openPrintJobControlPanel(self) -> None:
        raise NotImplementedError("openPrintJobControlPanel must be implemented")

    @pyqtSlot(name="openPrinterControlPanel")
    def openPrinterControlPanel(self) -> None:
        raise NotImplementedError("openPrinterControlPanel must be implemented")

    @pyqtProperty(QUrl, notify=_clusterPrintersChanged)
    def activeCameraUrl(self) -> QUrl:
        return QUrl()

    @pyqtSlot(QUrl, name="setActiveCameraUrl")
    def setActiveCameraUrl(self, camera_url: QUrl) -> None:
        pass

    @pyqtSlot(int, result=str, name="getTimeCompleted")
    def getTimeCompleted(self, time_remaining: int) -> str:
        return formatTimeCompleted(time_remaining)

    @pyqtSlot(int, result=str, name="getDateCompleted")
    def getDateCompleted(self, time_remaining: int) -> str:
        return formatDateCompleted(time_remaining)

    @pyqtSlot(int, result=str, name="formatDuration")
    def formatDuration(self, seconds: int) -> str:
        return Duration(seconds).getDisplayString(DurationFormat.Format.Short)

    def _update(self) -> None:
        super()._update()
        self._checkStillConnected()

    def _checkStillConnected(self) -> None:
        """Check if we're still connected by comparing the last timestamps for network response and the current time.

        This implementation is similar to the base NetworkedPrinterOutputDevice, but is tweaked slightly.
        Re-connecting is handled automatically by the output device managers in this plugin.
        TODO: it would be nice to have this logic in the managers, but connecting those with signals causes crashes.
        """
        time_since_last_response = time() - self._time_of_last_response
        if time_since_last_response > self._timeout_time:
            Logger.log("d", "It has been %s seconds since the last response for outputdevice %s, so assume a timeout", time_since_last_response, self.key)
            self.setConnectionState(ConnectionState.Closed)
            if self.key in CuraApplication.getInstance().getOutputDeviceManager().getOutputDeviceIds():
                CuraApplication.getInstance().getOutputDeviceManager().removeOutputDevice(self.key)
        elif self.connectionState == ConnectionState.Closed:
            self._reconnectForActiveMachine()

    def _reconnectForActiveMachine(self) -> None:
        """Reconnect for the active output device.

        Does nothing if the device is not meant for the active machine.
        """
        active_machine = CuraApplication.getInstance().getGlobalContainerStack()
        if not active_machine:
            return

        # Indicate this device is now connected again.
        Logger.log("d", "Reconnecting output device after timeout.")
        self.setConnectionState(ConnectionState.Connected)

        # If the device was already registered we don't need to register it again.
        if self.key in CuraApplication.getInstance().getOutputDeviceManager().getOutputDeviceIds():
            return

        # Try for local network device.
        stored_device_id = active_machine.getMetaDataEntry(self.META_NETWORK_KEY)
        if self.key == stored_device_id:
            CuraApplication.getInstance().getOutputDeviceManager().addOutputDevice(self)

        # Try for cloud device.
        stored_cluster_id = active_machine.getMetaDataEntry(self.META_CLUSTER_ID)
        if self.key == stored_cluster_id:
            CuraApplication.getInstance().getOutputDeviceManager().addOutputDevice(self)

    def _responseReceived(self) -> None:
        self._time_of_last_response = time()

    def _updatePrinters(self, remote_printers: List[ClusterPrinterStatus]) -> None:
        self._responseReceived()

        # Keep track of the new printers to show.
        # We create a new list instead of changing the existing one to get the correct order.
        new_printers = []  # type: List[PrinterOutputModel]

        # Check which printers need to be created or updated.
        for index, printer_data in enumerate(remote_printers):
            printer = next(iter(printer for printer in self._printers if printer.key == printer_data.uuid), None)
            if printer is None:
                printer = printer_data.createOutputModel(ClusterOutputController(self))
            else:
                printer_data.updateOutputModel(printer)
            new_printers.append(printer)

        # Check which printers need to be removed (de-referenced).
        remote_printers_keys = [printer_data.uuid for printer_data in remote_printers]
        removed_printers = [printer for printer in self._printers if printer.key not in remote_printers_keys]
        for removed_printer in removed_printers:
            if self._active_printer and self._active_printer.key == removed_printer.key:
                self.setActivePrinter(None)

        self._printers = new_printers
        self._has_received_printers = True
        if self._printers and not self.activePrinter:
            self.setActivePrinter(self._printers[0])

        self.printersChanged.emit()
        self._checkIfClusterHost()

    def _checkIfClusterHost(self):
        """Check is this device is a cluster host and takes the needed actions when it is not."""
        if len(self._printers) < 1 and self.isConnected():
            self._num_is_host_check_failed += 1
        else:
            self._num_is_host_check_failed = 0

        # Since we request the status of the cluster itself way less frequent in the cloud, it can happen that a cloud
        # printer reports having 0 printers (since they are offline!) but we haven't asked if the entire cluster is
        # offline. (See CURA-7360)
        # So by just counting a number of subsequent times that this has happened fixes the incorrect display.
        if self._num_is_host_check_failed >= 6:
            NotClusterHostMessage(self).show()
            self.close()
            CuraApplication.getInstance().getOutputDeviceManager().removeOutputDevice(self.key)

    def _updatePrintJobs(self, remote_jobs: List[ClusterPrintJobStatus]) -> None:
        """Updates the local list of print jobs with the list received from the cluster.

        :param remote_jobs: The print jobs received from the cluster.
        """
        self._responseReceived()

        # Keep track of the new print jobs to show.
        # We create a new list instead of changing the existing one to get the correct order.
        new_print_jobs = []

        # Check which print jobs need to be created or updated.
        for print_job_data in remote_jobs:
            print_job = next(
                iter(print_job for print_job in self._print_jobs if print_job.key == print_job_data.uuid), None)
            if not print_job:
                new_print_jobs.append(self._createPrintJobModel(print_job_data))
            else:
                print_job_data.updateOutputModel(print_job)
                if print_job_data.printer_uuid:
                    self._updateAssignedPrinter(print_job, print_job_data.printer_uuid)
                if print_job_data.assigned_to:
                    self._updateAssignedPrinter(print_job, print_job_data.assigned_to)
                new_print_jobs.append(print_job)

        # Check which print job need to be removed (de-referenced).
        remote_job_keys = [print_job_data.uuid for print_job_data in remote_jobs]
        removed_jobs = [print_job for print_job in self._print_jobs if print_job.key not in remote_job_keys]
        for removed_job in removed_jobs:
            if removed_job.assignedPrinter:
                removed_job.assignedPrinter.updateActivePrintJob(None)

        self._print_jobs = new_print_jobs
        self.printJobsChanged.emit()

    def _createPrintJobModel(self, remote_job: ClusterPrintJobStatus) -> UM3PrintJobOutputModel:
        """Create a new print job model based on the remote status of the job.

        :param remote_job: The remote print job data.
        """
        model = remote_job.createOutputModel(ClusterOutputController(self))
        if remote_job.printer_uuid:
            self._updateAssignedPrinter(model, remote_job.printer_uuid)
        if remote_job.assigned_to:
            self._updateAssignedPrinter(model, remote_job.assigned_to)
        if remote_job.preview_url:
            model.loadPreviewImageFromUrl(remote_job.preview_url)
        return model

    def _updateAssignedPrinter(self, model: UM3PrintJobOutputModel, printer_uuid: str) -> None:
        """Updates the printer assignment for the given print job model."""

        printer = next((p for p in self._printers if printer_uuid == p.key), None)
        if not printer:
            return
        printer.updateActivePrintJob(model)
        model.updateAssignedPrinter(printer)

    def _loadMonitorTab(self) -> None:
        """Load Monitor tab QML."""

        plugin_registry = CuraApplication.getInstance().getPluginRegistry()
        if not plugin_registry:
            Logger.log("e", "Could not get plugin registry")
            return
        plugin_path = plugin_registry.getPluginPath("UM3NetworkPrinting")
        if not plugin_path:
            Logger.log("e", "Could not get plugin path")
            return
        self._monitor_view_qml_path = os.path.join(plugin_path, "resources", "qml", "MonitorStage.qml")
