# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import os
from typing import List, Optional, Dict

from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject, pyqtSlot, QUrl

from UM.Logger import Logger
from UM.Qt.Duration import Duration, DurationFormat
from cura.CuraApplication import CuraApplication
from cura.PrinterOutput.Models.PrinterOutputModel import PrinterOutputModel
from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice, AuthState
from cura.PrinterOutput.PrinterOutputDevice import ConnectionType

from .Utils import formatTimeCompleted, formatDateCompleted
from .ClusterOutputController import ClusterOutputController
from .PrintJobUploadProgressMessage import PrintJobUploadProgressMessage
from .Models.UM3PrintJobOutputModel import UM3PrintJobOutputModel
from .Models.Http.ClusterPrinterStatus import ClusterPrinterStatus
from .Models.Http.ClusterPrintJobStatus import ClusterPrintJobStatus


## Output device class that forms the basis of Ultimaker networked printer output devices.
#  Currently used for local networking and cloud printing using Ultimaker Connect.
#  This base class primarily contains all the Qt properties and slots needed for the monitor page to work.
class UltimakerNetworkedPrinterOutputDevice(NetworkedPrinterOutputDevice):

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

        # Keeps track of all printers in the cluster.
        self._printers = []  # type: List[PrinterOutputModel]

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

    ##  The IP address of the printer.
    @pyqtProperty(str, constant=True)
    def address(self) -> str:
        return self._address

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

    @pyqtProperty(bool, notify=printJobsChanged)
    def receivedPrintJobs(self) -> bool:
        return bool(self._print_jobs)

    # Get the amount of printers in the cluster.
    @pyqtProperty(int, notify=_clusterPrintersChanged)
    def clusterSize(self) -> int:
        return max(1, len(self._printers))

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

    ##  Whether the printer that this output device represents supports print job actions via the local network.
    @pyqtProperty(bool, constant=True)
    def supportsPrintJobActions(self) -> bool:
        return True

    ##  Set the remote print job state.
    def setJobState(self, print_job_uuid: str, state: str) -> None:
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

    ## Load Monitor tab QML.
    def _loadMonitorTab(self):
        plugin_registry = CuraApplication.getInstance().getPluginRegistry()
        if not plugin_registry:
            Logger.log("e", "Could not get plugin registry")
            return
        plugin_path = plugin_registry.getPluginPath("UM3NetworkPrinting")
        if not plugin_path:
            Logger.log("e", "Could not get plugin path")
            return
        self._monitor_view_qml_path = os.path.join(plugin_path, "resources", "qml", "MonitorStage.qml")

    def _updatePrinters(self, remote_printers: List[ClusterPrinterStatus]) -> None:

        # Keep track of the new printers to show.
        # We create a new list instead of changing the existing one to get the correct order.
        new_printers = []  # type: List[PrinterOutputModel]

        # Check which printers need to be created or updated.
        for index, printer_data in enumerate(remote_printers):
            printer = next(iter(printer for printer in self._printers if printer.key == printer_data.uuid), None)
            if printer:
                printer_data.updateOutputModel(printer)
                new_printers.append(printer)
            else:
                printer = printer_data.createOutputModel(ClusterOutputController(self))
                new_printers.append(printer)

        # Check which printers need to be removed (de-referenced).
        remote_printers_keys = [printer_data.uuid for printer_data in remote_printers]
        removed_printers = [printer for printer in self._printers if printer.key not in remote_printers_keys]
        for removed_printer in removed_printers:
            if self._active_printer and self._active_printer.key == removed_printer.key:
                self.setActivePrinter(None)

        self._printers = new_printers
        if self._printers and not self.activePrinter:
            self.setActivePrinter(self._printers[0])

        self.printersChanged.emit()

    ## Updates the local list of print jobs with the list received from the cluster.
    #  \param remote_jobs: The print jobs received from the cluster.
    def _updatePrintJobs(self, remote_jobs: List[ClusterPrintJobStatus]) -> None:

        # Keep track of the new print jobs to show.
        # We create a new list instead of changing the existing one to get the correct order.
        new_print_jobs = []

        # Check which print jobs need to be created or updated.
        for index, print_job_data in enumerate(remote_jobs):
            print_job = next(
                iter(print_job for print_job in self._print_jobs if print_job.key == print_job_data.uuid), None)
            if not print_job:
                new_print_jobs.append(self._createPrintJobModel(print_job_data))
            else:
                print_job_data.updateOutputModel(print_job)
                if print_job_data.printer_uuid:
                    self._updateAssignedPrinter(print_job, print_job_data.printer_uuid)
                new_print_jobs.append(print_job)

        # Check which print job need to be removed (de-referenced).
        remote_job_keys = [print_job_data.uuid for print_job_data in remote_jobs]
        removed_jobs = [print_job for print_job in self._print_jobs if print_job.key not in remote_job_keys]
        for removed_job in removed_jobs:
            if removed_job.assignedPrinter:
                removed_job.assignedPrinter.updateActivePrintJob(None)

        self._print_jobs = new_print_jobs
        self.printJobsChanged.emit()

    ## Create a new print job model based on the remote status of the job.
    #  \param remote_job: The remote print job data.
    def _createPrintJobModel(self, remote_job: ClusterPrintJobStatus) -> UM3PrintJobOutputModel:
        model = remote_job.createOutputModel(ClusterOutputController(self))
        if remote_job.printer_uuid:
            self._updateAssignedPrinter(model, remote_job.printer_uuid)
        return model

    ## Updates the printer assignment for the given print job model.
    def _updateAssignedPrinter(self, model: UM3PrintJobOutputModel, printer_uuid: str) -> None:
        printer = next((p for p in self._printers if printer_uuid == p.key), None)
        if not printer:
            return
        printer.updateActivePrintJob(model)
        model.updateAssignedPrinter(printer)
