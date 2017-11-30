# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Logger import Logger
from UM.Application import Application
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.i18n import i18nCatalog
from UM.Message import Message
from UM.Qt.Duration import Duration, DurationFormat

from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice, AuthState
from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel
from cura.PrinterOutput.PrintJobOutputModel import PrintJobOutputModel
from cura.PrinterOutput.MaterialOutputModel import MaterialOutputModel

from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import pyqtSlot, QUrl, pyqtSignal, pyqtProperty

from time import time

import json
import os

i18n_catalog = i18nCatalog("cura")


class ClusterUM3OutputDevice(NetworkedPrinterOutputDevice):
    printJobsChanged = pyqtSignal()

    # This is a bit of a hack, as the notify can only use signals that are defined by the class that they are in.
    # Inheritance doesn't seem to work. Tying them together does work, but i'm open for better suggestions.
    clusterPrintersChanged = pyqtSignal()

    def __init__(self, device_id, address, properties, parent = None):
        super().__init__(device_id = device_id, address = address, properties=properties, parent = parent)
        self._api_prefix = "/cluster-api/v1/"

        self._number_of_extruders = 2

        self._print_jobs = []

        self._monitor_view_qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ClusterMonitorItem.qml")
        self._control_view_qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ClusterControlItem.qml")

        # See comments about this hack with the clusterPrintersChanged signal
        self.printersChanged.connect(self.clusterPrintersChanged)

        self._accepts_commands = True

        # Cluster does not have authentication, so default to authenticated
        self._authentication_state = AuthState.Authenticated

        self._error_message = None
        self._progress_message = None

    def requestWrite(self, nodes, file_name=None, filter_by_machine=False, file_handler=None, **kwargs):
        # Notify the UI that a switch to the print monitor should happen
        Application.getInstance().showPrintMonitor.emit(True)
        self.writeStarted.emit(self)

        self._gcode = getattr(Application.getInstance().getController().getScene(), "gcode_list", [])
        if not self._gcode:
            # Unable to find g-code. Nothing to send
            return

        # TODO; DEBUG
        self.sendPrintJob()

    @pyqtSlot()
    def sendPrintJob(self):
        Logger.log("i", "Sending print job to printer.")
        if self._sending_gcode:
            self._error_message = Message(
                i18n_catalog.i18nc("@info:status",
                                   "Sending new jobs (temporarily) blocked, still sending the previous print job."))
            self._error_message.show()
            return

        self._sending_gcode = True

        self._progress_message = Message(i18n_catalog.i18nc("@info:status", "Sending data to printer"), 0, False, -1,
                                         i18n_catalog.i18nc("@info:title", "Sending Data"))
        self._progress_message.addAction("Abort", i18n_catalog.i18nc("@action:button", "Cancel"), None, "")
        self._progress_message.actionTriggered.connect(self._progressMessageActionTriggered)

        compressed_gcode = self._compressGCode()
        if compressed_gcode is None:
            # Abort was called.
            return

        parts = []

        # If a specific printer was selected, it should be printed with that machine.
        require_printer_name = "" # Todo; actually needs to be set
        if require_printer_name:
            parts.append(self._createFormPart("name=require_printer_name", bytes(require_printer_name, "utf-8"), "text/plain"))

        # Add user name to the print_job
        parts.append(self._createFormPart("name=owner", bytes(self._getUserName(), "utf-8"), "text/plain"))

        file_name = "%s.gcode.gz" % Application.getInstance().getPrintInformation().jobName

        parts.append(self._createFormPart("name=\"file\"; filename=\"%s\"" % file_name, compressed_gcode))

        self.postFormWithParts("print_jobs/", parts, onFinished=self._onPostPrintJobFinished, onProgress=self._onUploadPrintJobProgress)

    def _onPostPrintJobFinished(self, reply):
        self._progress_message.hide()
        self._compressing_gcode = False
        self._sending_gcode = False
        Application.getInstance().showPrintMonitor.emit(False)

    def _onUploadPrintJobProgress(self, bytes_sent, bytes_total):
        if bytes_total > 0:
            new_progress = bytes_sent / bytes_total * 100
            # Treat upload progress as response. Uploading can take more than 10 seconds, so if we don't, we can get
            # timeout responses if this happens.
            self._last_response_time = time()
            if new_progress > self._progress_message.getProgress():
                self._progress_message.show()  # Ensure that the message is visible.
                self._progress_message.setProgress(bytes_sent / bytes_total * 100)
        else:
            self._progress_message.setProgress(0)
            self._progress_message.hide()

    def _progressMessageActionTriggered(self, message_id=None, action_id=None):
        if action_id == "Abort":
            Logger.log("d", "User aborted sending print to remote.")
            self._progress_message.hide()
            self._compressing_gcode = False
            self._sending_gcode = False
            Application.getInstance().showPrintMonitor.emit(False)

    @pyqtSlot()
    def openPrintJobControlPanel(self):
        Logger.log("d", "Opening print job control panel...")
        QDesktopServices.openUrl(QUrl("http://" + self._address + "/print_jobs"))

    @pyqtSlot()
    def openPrinterControlPanel(self):
        Logger.log("d", "Opening printer control panel...")
        QDesktopServices.openUrl(QUrl("http://" + self._address + "/printers"))

    @pyqtProperty("QVariantList", notify=printJobsChanged)
    def printJobs(self):
        return self._print_jobs

    @pyqtProperty("QVariantList", notify=printJobsChanged)
    def queuedPrintJobs(self):
        return [print_job for print_job in self._print_jobs if print_job.assignedPrinter is None]

    @pyqtProperty("QVariantList", notify=printJobsChanged)
    def activePrintJobs(self):
        return [print_job for print_job in self._print_jobs if print_job.assignedPrinter is not None]

    @pyqtProperty("QVariantList", notify=clusterPrintersChanged)
    def connectedPrintersTypeCount(self):
        printer_count = {}
        for printer in self._printers:
            if printer.type in printer_count:
                printer_count[printer.type] += 1
            else:
                printer_count[printer.type] = 1
        result = []
        for machine_type in printer_count:
            result.append({"machine_type": machine_type, "count": printer_count[machine_type]})
        return result

    @pyqtSlot(int, result=str)
    def formatDuration(self, seconds):
        return Duration(seconds).getDisplayString(DurationFormat.Format.Short)

    def _update(self):
        if not super()._update():
            return
        self.get("printers/", onFinished=self._onGetPrintersDataFinished)
        self.get("print_jobs/", onFinished=self._onGetPrintJobsFinished)

    def _onGetPrintJobsFinished(self, reply: QNetworkReply):
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status_code == 200:
            try:
                result = json.loads(bytes(reply.readAll()).decode("utf-8"))
            except json.decoder.JSONDecodeError:
                Logger.log("w", "Received an invalid print jobs message: Not valid JSON.")
                return
            print_jobs_seen = []
            for print_job_data in result:
                print_job = None
                for job in self._print_jobs:
                    if job.key == print_job_data["uuid"]:
                        print_job = job
                        break

                if print_job is None:
                    print_job = PrintJobOutputModel(output_controller = None,
                                                    key = print_job_data["uuid"],
                                                    name = print_job_data["name"])
                print_job.updateTimeTotal(print_job_data["time_total"])
                print_job.updateTimeElapsed(print_job_data["time_elapsed"])
                print_job.updateState(print_job_data["status"])
                print_job.updateOwner(print_job_data["owner"])
                printer = None
                if print_job.state != "queued":
                    # Print job should be assigned to a printer.
                    printer = self._getPrinterByKey(print_job_data["printer_uuid"])
                else:  # Status is queued
                    # The job can "reserve" a printer if some changes are required.
                    printer = self._getPrinterByKey(print_job_data["assigned_to"])

                if printer:
                    printer.updateActivePrintJob(print_job)

                print_jobs_seen.append(print_job)
            for old_job in self._print_jobs:
                if old_job not in print_jobs_seen and old_job.assignedPrinter:
                    # Print job needs to be removed.
                    old_job.assignedPrinter.updateActivePrintJob(None)

            self._print_jobs = print_jobs_seen
            self.printJobsChanged.emit()

    def _onGetPrintersDataFinished(self, reply: QNetworkReply):
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status_code == 200:
            try:
                result = json.loads(bytes(reply.readAll()).decode("utf-8"))
            except json.decoder.JSONDecodeError:
                Logger.log("w", "Received an invalid printers state message: Not valid JSON.")
                return
            printer_list_changed = False
            # TODO: Ensure that printers that have been removed are also removed locally.
            for printer_data in result:
                uuid = printer_data["uuid"]

                printer = None
                for device in self._printers:
                    if device.key == uuid:
                        printer = device
                        break

                if printer is None:
                    printer = PrinterOutputModel(output_controller=None, number_of_extruders=self._number_of_extruders)
                    self._printers.append(printer)
                    printer_list_changed = True

                printer.updateName(printer_data["friendly_name"])
                printer.updateKey(uuid)
                printer.updateType(printer_data["machine_variant"])
                if not printer_data["enabled"]:
                    printer.updateState("disabled")
                else:
                    printer.updateState(printer_data["status"])

                for index in range(0, self._number_of_extruders):
                    extruder = printer.extruders[index]
                    extruder_data = printer_data["configuration"][index]
                    try:
                        hotend_id = extruder_data["print_core_id"]
                    except KeyError:
                        hotend_id = ""
                    extruder.updateHotendID(hotend_id)

                    material_data = extruder_data["material"]
                    if extruder.activeMaterial is None or extruder.activeMaterial.guid != material_data["guid"]:
                        containers = ContainerRegistry.getInstance().findInstanceContainers(type="material",
                                                                                            GUID=material_data["guid"])
                        if containers:
                            color = containers[0].getMetaDataEntry("color_code")
                            brand = containers[0].getMetaDataEntry("brand")
                            material_type = containers[0].getMetaDataEntry("material")
                            name = containers[0].getName()
                        else:
                            Logger.log("w", "Unable to find material with guid {guid}. Using data as provided by cluster".format(guid = material_data["guid"]))
                            # Unknown material.
                            color = material_data["color"]
                            brand = material_data["brand"]
                            material_type = material_data["material"]
                            name = "Unknown"

                        material = MaterialOutputModel(guid = material_data["guid"],
                                                       type = material_type,
                                                       brand = brand,
                                                       color = color,
                                                       name = name)
                        extruder.updateActiveMaterial(material)

            if printer_list_changed:
                self.printersChanged.emit()
        else:
            Logger.log("w",
                       "Got status code {status_code} while trying to get printer data".format(status_code=status_code))