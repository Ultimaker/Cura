# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Logger import Logger

from UM.Settings.ContainerRegistry import ContainerRegistry

from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice
from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel
from cura.PrinterOutput.PrintJobOutputModel import PrintJobOutputModel
from cura.PrinterOutput.MaterialOutputModel import MaterialOutputModel

from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import pyqtSlot, QUrl

import json
import os


class ClusterUM3OutputDevice(NetworkedPrinterOutputDevice):
    def __init__(self, device_id, address, properties, parent = None):
        super().__init__(device_id = device_id, address = address, properties=properties, parent = parent)
        self._api_prefix = "/cluster-api/v1/"

        self._number_of_extruders = 2

        self._print_jobs = []

        self._monitor_view_qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ClusterMonitorItem.qml")
        self._control_view_qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ClusterControlItem.qml")

    @pyqtSlot()
    def openPrintJobControlPanel(self):
        Logger.log("d", "Opening print job control panel...")
        QDesktopServices.openUrl(QUrl("http://" + self._address + "/print_jobs"))

    @pyqtSlot()
    def openPrinterControlPanel(self):
        Logger.log("d", "Opening printer control panel...")
        QDesktopServices.openUrl(QUrl("http://" + self._address + "/printers"))

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
                if print_job.state == "printing":
                    # Print job should be assigned to a printer.
                    printer = self._getPrinterByKey(print_job_data["printer_uuid"])
                    if printer:
                        printer.updateActivePrintJob(print_job)

                print_jobs_seen.append(print_job)
            for old_job in self._print_jobs:
                if old_job not in print_jobs_seen:
                    # Print job needs to be removed.
                    old_job.assignedPrinter.updateActivePrintJob(None)

            self._print_jobs = print_jobs_seen

    def _onGetPrintersDataFinished(self, reply: QNetworkReply):
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status_code == 200:
            try:
                result = json.loads(bytes(reply.readAll()).decode("utf-8"))
            except json.decoder.JSONDecodeError:
                Logger.log("w", "Received an invalid printers state message: Not valid JSON.")
                return

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

                printer.updateName(printer_data["friendly_name"])
                printer.updateKey(uuid)

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

        else:
            Logger.log("w",
                       "Got status code {status_code} while trying to get printer data".format(status_code=status_code))