import datetime
import getpass
import gzip
import json
import os
import os.path
import time

from enum import Enum
from PyQt5.QtNetwork import QNetworkRequest, QHttpPart, QHttpMultiPart
from PyQt5.QtCore import QUrl, QByteArray, pyqtSlot, pyqtProperty, QCoreApplication, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply
from PyQt5.QtQml import QQmlComponent, QQmlContext
from UM.Application import Application
from UM.Decorators import override
from UM.Logger import Logger
from UM.Message import Message
from UM.OutputDevice import OutputDeviceError
from UM.i18n import i18nCatalog
from UM.Qt.Duration import Duration, DurationFormat

from . import NetworkPrinterOutputDevice


i18n_catalog = i18nCatalog("cura")


class OutputStage(Enum):
    ready = 0
    uploading = 2


class NetworkClusterPrinterOutputDevice(NetworkPrinterOutputDevice.NetworkPrinterOutputDevice):
    printJobsChanged = pyqtSignal()
    printersChanged = pyqtSignal()
    selectedPrinterChanged = pyqtSignal()

    def __init__(self, key, address, properties, api_prefix, plugin_path):
        super().__init__(key, address, properties, api_prefix)
        # Store the address of the master.
        self._master_address = address
        name_property = properties.get(b"name", b"")
        if name_property:
            name = name_property.decode("utf-8")
        else:
            name = key

        self._authentication_state = NetworkPrinterOutputDevice.AuthState.Authenticated  # The printer is always authenticated
        self._plugin_path = plugin_path

        self.setName(name)
        description = i18n_catalog.i18nc("@action:button Preceded by 'Ready to'.", "Print over network")
        self.setShortDescription(description)
        self.setDescription(description)

        self._stage = OutputStage.ready
        host_override = os.environ.get("CLUSTER_OVERRIDE_HOST", "")
        if host_override:
            Logger.log(
                "w",
                "Environment variable CLUSTER_OVERRIDE_HOST is set to [%s], cluster hosts are now set to this host",
                host_override)
            self._host = "http://" + host_override
        else:
            self._host = "http://" + address

        # is the same as in NetworkPrinterOutputDevicePlugin
        self._cluster_api_version = "1"
        self._cluster_api_prefix = "/cluster-api/v" + self._cluster_api_version + "/"
        self._api_base_uri = self._host + self._cluster_api_prefix

        self._file_name = None
        self._progress_message = None
        self._request = None
        self._reply = None

        # The main reason to keep the 'multipart' form data on the object
        # is to prevent the Python GC from claiming it too early.
        self._multipart = None

        self._print_view = None
        self._request_job = []

        self._monitor_view_qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ClusterMonitorItem.qml")
        self._control_view_qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ClusterControlItem.qml")

        self._print_jobs = []
        self._print_job_by_printer_uuid = {}
        self._print_job_by_uuid = {} # Print jobs by their own uuid
        self._printers = []
        self._printers_dict = {}  # by unique_name

        self._connected_printers_type_count = []
        self._automatic_printer = {"unique_name": "", "friendly_name": "Automatic"}  # empty unique_name IS automatic selection
        self._selected_printer = self._automatic_printer

        self._cluster_status_update_timer = QTimer()
        self._cluster_status_update_timer.setInterval(5000)
        self._cluster_status_update_timer.setSingleShot(False)
        self._cluster_status_update_timer.timeout.connect(self._requestClusterStatus)

        self._can_pause = True
        self._can_abort = True
        self._can_pre_heat_bed = False
        self._cluster_size = int(properties.get(b"cluster_size", 0))

        self._cleanupRequest()

        #These are texts that are to be translated for future features.
        temporary_translation = i18n_catalog.i18n("This printer is not set up to host a group of connected Ultimaker 3 printers.")
        temporary_translation2 = i18n_catalog.i18nc("Count is number of printers.", "This printer is the host for a group of {count} connected Ultimaker 3 printers.").format(count = 3)
        temporary_translation3 = i18n_catalog.i18n("{printer_name} has finished printing '{job_name}'. Please collect the print and confirm clearing the build plate.") #When finished.
        temporary_translation4 = i18n_catalog.i18n("{printer_name} is reserved to print '{job_name}'. Please change the printer's configuration to match the job, for it to start printing.") #When configuration changed.

    ##  No authentication, so requestAuthentication should do exactly nothing
    @pyqtSlot()
    def requestAuthentication(self, message_id = None, action_id = "Retry"):
        pass    # Cura Connect doesn't do any authorization

    def setAuthenticationState(self, auth_state):
        self._authentication_state = NetworkPrinterOutputDevice.AuthState.Authenticated  # The printer is always authenticated

    def _verifyAuthentication(self):
        pass

    def _checkAuthentication(self):
        Logger.log("d", "_checkAuthentication Cura Connect - nothing to be done")

    @pyqtProperty(QObject, notify=selectedPrinterChanged)
    def controlItem(self):
        # TODO: Probably not the nicest way to do this. This needs to be done better at some point in time.
        if not self._control_component:
            self._createControlViewFromQML()
        name = self._selected_printer.get("friendly_name")
        if name == self._automatic_printer.get("friendly_name") or name == "":
            return self._control_item
        # Let cura use the default.
        return None

    @pyqtSlot(int, result = str)
    def getTimeCompleted(self, time_remaining):
        current_time = time.time()
        datetime_completed = datetime.datetime.fromtimestamp(current_time + time_remaining)
        return "{hour:02d}:{minute:02d}".format(hour = datetime_completed.hour, minute = datetime_completed.minute)

    @pyqtSlot(int, result = str)
    def getDateCompleted(self, time_remaining):
        current_time = time.time()
        datetime_completed = datetime.datetime.fromtimestamp(current_time + time_remaining)
        return (datetime_completed.strftime("%a %b ") + "{day}".format(day=datetime_completed.day)).upper()

    @pyqtProperty(int, constant = True)
    def clusterSize(self):
        return self._cluster_size

    @pyqtProperty(str, notify=selectedPrinterChanged)
    def name(self):
        # Show the name of the selected printer.
        # This is not the nicest way to do this, but changes to the Cura UI are required otherwise.
        name = self._selected_printer.get("friendly_name")
        if name != self._automatic_printer.get("friendly_name"):
            return name
        # Return name of cluster master.
        return self._properties.get(b"name", b"").decode("utf-8")

    def connect(self):
        super().connect()
        self._cluster_status_update_timer.start()

    def close(self):
        super().close()
        self._cluster_status_update_timer.stop()

    def _setJobState(self, job_state):
        if not self._selected_printer:
            return

        selected_printer_uuid = self._printers_dict[self._selected_printer["unique_name"]]["uuid"]
        if selected_printer_uuid not in self._print_job_by_printer_uuid:
            return

        print_job_uuid = self._print_job_by_printer_uuid[selected_printer_uuid]["uuid"]

        url = QUrl(self._api_base_uri + "print_jobs/" + print_job_uuid + "/action")
        put_request = QNetworkRequest(url)
        put_request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        data = '{"action": "' + job_state + '"}'
        self._manager.put(put_request, data.encode())

    def _requestClusterStatus(self):
        # TODO: Handle timeout. We probably want to know if the cluster is still reachable or not.
        url = QUrl(self._api_base_uri + "printers/")
        printers_request = QNetworkRequest(url)
        self._addUserAgentHeader(printers_request)
        self._manager.get(printers_request)
        # See _finishedPrintersRequest()

        if self._printers:  # if printers is not empty
            url = QUrl(self._api_base_uri + "print_jobs/")
            print_jobs_request = QNetworkRequest(url)
            self._addUserAgentHeader(print_jobs_request)
            self._manager.get(print_jobs_request)
            # See _finishedPrintJobsRequest()

    def _finishedPrintJobsRequest(self, reply):
        try:
            json_data = json.loads(bytes(reply.readAll()).decode("utf-8"))
        except json.decoder.JSONDecodeError:
            Logger.log("w", "Received an invalid print job state message: Not valid JSON.")
            return
        self.setPrintJobs(json_data)

    def _finishedPrintersRequest(self, reply):
        try:
            json_data = json.loads(bytes(reply.readAll()).decode("utf-8"))
        except json.decoder.JSONDecodeError:
            Logger.log("w", "Received an invalid print job state message: Not valid JSON.")
            return
        self.setPrinters(json_data)

    def materialHotendChangedMessage(self, callback):
        pass # Do nothing.

    def _startCameraStream(self):
        ## Request new image
        url = QUrl("http://" + self._printers_dict[self._selected_printer["unique_name"]]["ip_address"] + ":8080/?action=stream")
        self._image_request = QNetworkRequest(url)
        self._addUserAgentHeader(self._image_request)
        self._image_reply = self._manager.get(self._image_request)
        self._image_reply.downloadProgress.connect(self._onStreamDownloadProgress)

    def spawnPrintView(self):
        if self._print_view is None:
            path = QUrl.fromLocalFile(os.path.join(self._plugin_path, "PrintWindow.qml"))
            component = QQmlComponent(Application.getInstance()._engine, path)

            self._print_context = QQmlContext(Application.getInstance()._engine.rootContext())
            self._print_context.setContextProperty("OutputDevice", self)
            self._print_view = component.create(self._print_context)

            if component.isError():
                Logger.log("e", " Errors creating component: \n%s", "\n".join(
                    [e.toString() for e in component.errors()]))

        if self._print_view is not None:
            self._print_view.show()

    ##  Store job info, show Print view for settings
    def requestWrite(self, nodes, file_name=None, filter_by_machine=False, file_handler=None, **kwargs):
        self._selected_printer = self._automatic_printer  # reset to default option
        self._request_job = [nodes, file_name, filter_by_machine, file_handler, kwargs]

        if self._stage != OutputStage.ready:
            if self._error_message:
                self._error_message.hide()
            self._error_message = Message(
                i18n_catalog.i18nc("@info:status",
                                   "Sending new jobs (temporarily) blocked, still sending the previous print job."))
            self._error_message.show()
            return

        if len(self._printers) > 1:
            self.spawnPrintView()  # Ask user how to print it.
        elif len(self._printers) == 1:
            # If there is only one printer, don't bother asking.
            self.selectAutomaticPrinter()
            self.sendPrintJob()
        else:
            # Cluster has no printers, warn the user of this.
            if self._error_message:
                self._error_message.hide()
            self._error_message = Message(
                i18n_catalog.i18nc("@info:status",
                                   "Unable to send new print job: this 3D printer is not (yet) set up to host a group of connected Ultimaker 3 printers."))
            self._error_message.show()

    ##  Actually send the print job, called from the dialog
    #   :param: require_printer_name: name of printer, or ""
    @pyqtSlot()
    def sendPrintJob(self):
        nodes, file_name, filter_by_machine, file_handler, kwargs = self._request_job
        require_printer_name = self._selected_printer["unique_name"]

        self._send_gcode_start = time.time()
        Logger.log("d", "Sending print job [%s] to host..." % file_name)

        if self._stage != OutputStage.ready:
            Logger.log("d", "Unable to send print job as the state is %s", self._stage)
            raise OutputDeviceError.DeviceBusyError()
        self._stage = OutputStage.uploading

        self._file_name = "%s.gcode.gz" % file_name
        self._showProgressMessage()

        new_request = self._buildSendPrintJobHttpRequest(require_printer_name)
        if new_request is None or self._stage != OutputStage.uploading:
            return
        self._request = new_request
        self._reply = self._manager.post(self._request, self._multipart)
        self._reply.uploadProgress.connect(self._onUploadProgress)
        # See _finishedPostPrintJobRequest()

    def _buildSendPrintJobHttpRequest(self, require_printer_name):
        api_url = QUrl(self._api_base_uri + "print_jobs/")
        request = QNetworkRequest(api_url)
        # Create multipart request and add the g-code.
        self._multipart = QHttpMultiPart(QHttpMultiPart.FormDataType)

        # Add gcode
        part = QHttpPart()
        part.setHeader(QNetworkRequest.ContentDispositionHeader,
                       'form-data; name="file"; filename="%s"' % self._file_name)

        gcode = getattr(Application.getInstance().getController().getScene(), "gcode_list")
        compressed_gcode = self._compressGcode(gcode)
        if compressed_gcode is None:
            return None     # User aborted print, so stop trying.

        part.setBody(compressed_gcode)
        self._multipart.append(part)

        # require_printer_name "" means automatic
        if require_printer_name:
            self._multipart.append(self.__createKeyValueHttpPart("require_printer_name", require_printer_name))
        user_name = self.__get_username()
        if user_name is None:
            user_name = "unknown"
        self._multipart.append(self.__createKeyValueHttpPart("owner", user_name))

        self._addUserAgentHeader(request)
        return request

    def _compressGcode(self, gcode):
        self._compressing_print = True
        batched_line = ""
        max_chars_per_line = int(1024 * 1024 / 4)  # 1 / 4  MB

        byte_array_file_data = b""

        def _compressDataAndNotifyQt(data_to_append):
            compressed_data = gzip.compress(data_to_append.encode("utf-8"))
            self._progress_message.setProgress(-1)  # Tickle the message so that it's clear that it's still being used.
            QCoreApplication.processEvents()  # Ensure that the GUI does not freeze.
            # Pretend that this is a response, as zipping might take a bit of time.
            self._last_response_time = time.time()
            return compressed_data

        if gcode is None:
            Logger.log("e", "Unable to find sliced gcode, returning empty.")
            return byte_array_file_data

        for line in gcode:
            if not self._compressing_print:
                self._progress_message.hide()
                return None     # Stop trying to zip, abort was called.
            batched_line += line
            # if the gcode was read from a gcode file, self._gcode will be a list of all lines in that file.
            # Compressing line by line in this case is extremely slow, so we need to batch them.
            if len(batched_line) < max_chars_per_line:
                continue
            byte_array_file_data += _compressDataAndNotifyQt(batched_line)
            batched_line = ""

        # Also compress the leftovers.
        if batched_line:
            byte_array_file_data += _compressDataAndNotifyQt(batched_line)

        return byte_array_file_data

    def __createKeyValueHttpPart(self, key, value):
        metadata_part = QHttpPart()
        metadata_part.setHeader(QNetworkRequest.ContentTypeHeader, 'text/plain')
        metadata_part.setHeader(QNetworkRequest.ContentDispositionHeader, 'form-data; name="%s"' % (key))
        metadata_part.setBody(bytearray(value, "utf8"))
        return metadata_part

    def __get_username(self):
        try:
            return getpass.getuser()
        except:
            Logger.log("d", "Could not get the system user name, returning 'unknown' instead.")
            return None

    def _finishedPrintJobPostRequest(self, reply):
        self._stage = OutputStage.ready
        if self._progress_message:
            self._progress_message.hide()
        self._progress_message = None
        self.writeFinished.emit(self)

        if reply.error():
            self._showRequestFailedMessage(reply)
            self.writeError.emit(self)
        else:
            self._showRequestSucceededMessage()
            self.writeSuccess.emit(self)

        self._cleanupRequest()

    def _showRequestFailedMessage(self, reply):
        if reply is not None:
            Logger.log("w", "Unable to send print job to group {cluster_name}: {error_string} ({error})".format(
                cluster_name = self.getName(),
                error_string = str(reply.errorString()),
                error = str(reply.error())))
            error_message_template = i18n_catalog.i18nc("@info:status", "Unable to send print job to group {cluster_name}.")
            message = Message(text=error_message_template.format(
                cluster_name = self.getName()))
            message.show()

    def _showRequestSucceededMessage(self):
        confirmation_message_template = i18n_catalog.i18nc(
            "@info:status",
            "Sent {file_name} to group {cluster_name}."
        )
        file_name = os.path.basename(self._file_name).split(".")[0]
        message_text = confirmation_message_template.format(cluster_name = self.getName(), file_name = file_name)
        message = Message(text=message_text)
        button_text = i18n_catalog.i18nc("@action:button", "Show print jobs")
        button_tooltip = i18n_catalog.i18nc("@info:tooltip", "Opens the print jobs interface in your browser.")
        message.addAction("open_browser", button_text, "globe", button_tooltip)
        message.actionTriggered.connect(self._onMessageActionTriggered)
        message.show()

    def setPrintJobs(self, print_jobs):
        #TODO: hack, last seen messes up the check, so drop it.
        for job in print_jobs:
            del job["last_seen"]
            # Strip any extensions
            job["name"] = self._removeGcodeExtension(job["name"])

        if self._print_jobs != print_jobs:
            old_print_jobs = self._print_jobs
            self._print_jobs = print_jobs

            self._notifyFinishedPrintJobs(old_print_jobs, print_jobs)
            self._notifyConfigurationChangeRequired(old_print_jobs, print_jobs)

            # Yes, this is a hacky way of doing it, but it's quick and the API doesn't give the print job per printer
            # for some reason. ugh.
            self._print_job_by_printer_uuid = {}
            self._print_job_by_uuid = {}
            for print_job in print_jobs:
                if "printer_uuid" in print_job and print_job["printer_uuid"] is not None:
                    self._print_job_by_printer_uuid[print_job["printer_uuid"]] = print_job
                self._print_job_by_uuid[print_job["uuid"]] = print_job
            self.printJobsChanged.emit()

    def _removeGcodeExtension(self, name):
        parts = name.split(".")
        if parts[-1].upper() == "GZ":
            parts = parts[:-1]
        if parts[-1].upper() == "GCODE":
            parts = parts[:-1]
        return ".".join(parts)

    def _notifyFinishedPrintJobs(self, old_print_jobs, new_print_jobs):
        """Notify the user when any of their print jobs have just completed.

        Arguments:

        old_print_jobs -- the previous list of print job status information as returned by the cluster REST API.
        new_print_jobs -- the current list of print job status information as returned by the cluster REST API.
        """
        if old_print_jobs is None:
            return

        username = self.__get_username()
        if username is None:
            return

        our_old_print_jobs = self.__filterOurPrintJobs(old_print_jobs)
        our_old_not_finished_print_jobs = [pj for pj in our_old_print_jobs if pj["status"] != "wait_cleanup"]

        our_new_print_jobs = self.__filterOurPrintJobs(new_print_jobs)
        our_new_finished_print_jobs = [pj for pj in our_new_print_jobs if pj["status"] == "wait_cleanup"]

        old_not_finished_print_job_uuids = set([pj["uuid"] for pj in our_old_not_finished_print_jobs])

        for print_job in our_new_finished_print_jobs:
            if print_job["uuid"] in old_not_finished_print_job_uuids:

                printer_name = self.__getPrinterNameFromUuid(print_job["printer_uuid"])
                if printer_name is None:
                    printer_name = i18n_catalog.i18nc("@label", "Unknown")

                message_text = (i18n_catalog.i18nc("@info:status",
                                "Printer '{printer_name}' has finished printing '{job_name}'.")
                                .format(printer_name=printer_name, job_name=print_job["name"]))
                message = Message(text=message_text, title=i18n_catalog.i18nc("@info:status", "Print finished"))
                Application.getInstance().showMessage(message)
                Application.getInstance().showToastMessage(
                    i18n_catalog.i18nc("@info:status", "Print finished"),
                    message_text)

    def __filterOurPrintJobs(self, print_jobs):
        username = self.__get_username()
        return [print_job for print_job in print_jobs if print_job["owner"] == username]

    def _notifyConfigurationChangeRequired(self, old_print_jobs, new_print_jobs):
        if old_print_jobs is None:
            return

        old_change_required_print_jobs = self.__filterConfigChangePrintJobs(self.__filterOurPrintJobs(old_print_jobs))
        new_change_required_print_jobs = self.__filterConfigChangePrintJobs(self.__filterOurPrintJobs(new_print_jobs))
        old_change_required_print_job_uuids = set([pj["uuid"] for pj in old_change_required_print_jobs])

        for print_job in new_change_required_print_jobs:
            if print_job["uuid"] not in old_change_required_print_job_uuids:

                printer_name = self.__getPrinterNameFromUuid(print_job["assigned_to"])
                if printer_name is None:
                    # don't report on yet unknown printers
                    continue

                message_text = (i18n_catalog.i18n("{printer_name} is reserved to print '{job_name}'. Please change the printer's configuration to match the job, for it to start printing.")
                                .format(printer_name=printer_name, job_name=print_job["name"]))
                message = Message(text=message_text, title=i18n_catalog.i18nc("@label:status", "Action required"))
                Application.getInstance().showMessage(message)
                Application.getInstance().showToastMessage(
                    i18n_catalog.i18nc("@label:status", "Action required"),
                    message_text)

    def __filterConfigChangePrintJobs(self, print_jobs):
        return filter(self.__isConfigurationChangeRequiredPrintJob, print_jobs)

    def __isConfigurationChangeRequiredPrintJob(self, print_job):
        if print_job["status"] == "queued":
            changes_required = print_job.get("configuration_changes_required", [])
            return len(changes_required) != 0
        return False

    def __getPrinterNameFromUuid(self, printer_uuid):
        for printer in self._printers:
            if printer["uuid"] == printer_uuid:
                return printer["friendly_name"]
        return None

    def setPrinters(self, printers):
        if self._printers != printers:
            self._connected_printers_type_count = []
            printers_count = {}
            self._printers = printers
            self._printers_dict = dict((p["unique_name"], p) for p in printers)  # for easy lookup by unique_name

            for printer in printers:
                variant = printer["machine_variant"]
                if variant in printers_count:
                    printers_count[variant] += 1
                else:
                    printers_count[variant] = 1
            for type in printers_count:
                self._connected_printers_type_count.append({"machine_type": type, "count": printers_count[type]})
            self.printersChanged.emit()

    @pyqtProperty("QVariantList", notify=printersChanged)
    def connectedPrintersTypeCount(self):
        return self._connected_printers_type_count

    @pyqtProperty("QVariantList", notify=printersChanged)
    def connectedPrinters(self):
        return self._printers

    @pyqtProperty(int, notify=printJobsChanged)
    def numJobsPrinting(self):
        num_jobs_printing = 0
        for job in self._print_jobs:
            if job["status"] in ["printing", "wait_cleanup", "sent_to_printer", "pre_print", "post_print"]:
                num_jobs_printing += 1
        return num_jobs_printing

    @pyqtProperty(int, notify=printJobsChanged)
    def numJobsQueued(self):
        num_jobs_queued = 0
        for job in self._print_jobs:
            if job["status"] == "queued":
                num_jobs_queued += 1
        return num_jobs_queued

    @pyqtProperty("QVariantMap", notify=printJobsChanged)
    def printJobsByUUID(self):
        return self._print_job_by_uuid

    @pyqtProperty("QVariantMap", notify=printJobsChanged)
    def printJobsByPrinterUUID(self):
        return self._print_job_by_printer_uuid

    @pyqtProperty("QVariantList", notify=printJobsChanged)
    def printJobs(self):
        return self._print_jobs

    @pyqtProperty("QVariantList", notify=printersChanged)
    def printers(self):
        return [self._automatic_printer, ] + self._printers

    @pyqtSlot(str, str)
    def selectPrinter(self, unique_name, friendly_name):
        self.stopCamera()
        self._selected_printer = {"unique_name": unique_name, "friendly_name": friendly_name}
        Logger.log("d", "Selected printer: %s %s", friendly_name, unique_name)
        # TODO: Probably not the nicest way to do this. This needs to be done better at some point in time.
        if unique_name == "":
            self._address = self._master_address
        else:
            self._address = self._printers_dict[self._selected_printer["unique_name"]]["ip_address"]

        self.selectedPrinterChanged.emit()

    def _updateJobState(self, job_state):
        name = self._selected_printer.get("friendly_name")
        if name == "" or name == "Automatic":
            # TODO: This is now a bit hacked; If no printer is selected, don't show job state.
            if self._job_state != "":
                self._job_state = ""
                self.jobStateChanged.emit()
        else:
            if self._job_state != job_state:
                self._job_state = job_state
                self.jobStateChanged.emit()

    @pyqtSlot()
    def selectAutomaticPrinter(self):
        self.stopCamera()
        self._selected_printer = self._automatic_printer
        self.selectedPrinterChanged.emit()

    @pyqtProperty("QVariant", notify=selectedPrinterChanged)
    def selectedPrinterName(self):
        return self._selected_printer.get("unique_name", "")

    def getPrintJobsUrl(self):
        return self._host + "/print_jobs"

    def getPrintersUrl(self):
        return self._host + "/printers"

    def _showProgressMessage(self):
        progress_message_template = i18n_catalog.i18nc("@info:progress",
                                               "Sending <filename>{file_name}</filename> to group {cluster_name}")
        file_name = os.path.basename(self._file_name).split(".")[0]
        self._progress_message = Message(progress_message_template.format(file_name = file_name, cluster_name = self.getName()), 0, False, -1)
        self._progress_message.addAction("Abort", i18n_catalog.i18nc("@action:button", "Cancel"), None, "")
        self._progress_message.actionTriggered.connect(self._onMessageActionTriggered)
        self._progress_message.show()

    def _addUserAgentHeader(self, request):
        request.setRawHeader(b"User-agent", b"CuraPrintClusterOutputDevice Plugin")

    def _cleanupRequest(self):
        self._request = None
        self._stage = OutputStage.ready
        self._file_name = None

    def _onFinished(self, reply):
        super()._onFinished(reply)
        reply_url = reply.url().toString()
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status_code == 500:
            Logger.log("w", "Request to {url} returned a 500.".format(url = reply_url))
            return
        if reply.error() == QNetworkReply.ContentOperationNotPermittedError:
            # It was probably "/api/v1/materials" for legacy UM3
            return
        if reply.error() == QNetworkReply.ContentNotFoundError:
            # It was probably "/api/v1/print_job" for legacy UM3
            return

        if reply.operation() == QNetworkAccessManager.PostOperation:
            if self._cluster_api_prefix + "print_jobs" in reply_url:
                self._finishedPrintJobPostRequest(reply)
                return

        # We need to do this check *after* we process the post operation!
        # If the sending of g-code is cancelled by the user it will result in an error, but we do need to handle this.
        if reply.error() != QNetworkReply.NoError:
            Logger.log("e", "After requesting [%s] we got a network error [%s]. Not processing anything...", reply_url, reply.error())
            return

        elif reply.operation() == QNetworkAccessManager.GetOperation:
            if self._cluster_api_prefix + "print_jobs" in reply_url:
                self._finishedPrintJobsRequest(reply)
            elif self._cluster_api_prefix + "printers" in reply_url:
                self._finishedPrintersRequest(reply)

    @pyqtSlot()
    def openPrintJobControlPanel(self):
        Logger.log("d", "Opening print job control panel...")
        QDesktopServices.openUrl(QUrl(self.getPrintJobsUrl()))

    @pyqtSlot()
    def openPrinterControlPanel(self):
        Logger.log("d", "Opening printer control panel...")
        QDesktopServices.openUrl(QUrl(self.getPrintersUrl()))

    def _onMessageActionTriggered(self, message, action):
        if action == "open_browser":
            QDesktopServices.openUrl(QUrl(self.getPrintJobsUrl()))

        if action == "Abort":
            Logger.log("d", "User aborted sending print to remote.")
            self._progress_message.hide()
            self._compressing_print = False
            if self._reply:
                self._reply.abort()
            self._stage = OutputStage.ready
            Application.getInstance().showPrintMonitor.emit(False)

    @pyqtSlot(int, result=str)
    def formatDuration(self, seconds):
        return Duration(seconds).getDisplayString(DurationFormat.Format.Short)
