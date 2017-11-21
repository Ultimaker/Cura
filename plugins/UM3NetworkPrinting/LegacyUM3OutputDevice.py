from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice
from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel
from cura.PrinterOutput.PrintJobOutputModel import PrintJobOutputModel
from cura.PrinterOutput.MaterialOutputModel import MaterialOutputModel

from UM.Logger import Logger
from UM.Settings.ContainerRegistry import ContainerRegistry

from PyQt5.QtNetwork import QNetworkRequest

import json


class LegacyUM3OutputDevice(NetworkedPrinterOutputDevice):
    def __init__(self, device_id, address: str, properties, parent = None):
        super().__init__(device_id = device_id, address = address, properties = properties, parent = parent)
        self._api_prefix = "/api/v1/"
        self._number_of_extruders = 2

    def _update(self):
        if not super()._update():
            return
        self._get("printer", onFinished=self._onGetPrinterDataFinished)
        self._get("print_job", onFinished=self._onGetPrintJobFinished)

    def _onGetPrintJobFinished(self, reply):
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)

        if not self._printers:
            return  # Ignore the data for now, we don't have info about a printer yet.
        printer = self._printers[0]

        if status_code == 200:
            try:
                result = json.loads(bytes(reply.readAll()).decode("utf-8"))
            except json.decoder.JSONDecodeError:
                Logger.log("w", "Received an invalid print job state message: Not valid JSON.")
                return
            if printer.activePrintJob is None:
                print_job = PrintJobOutputModel(output_controller=None)
                printer.updateActivePrintJob(print_job)
            else:
                print_job = printer.activePrintJob
            print_job.updateState(result["state"])
            print_job.updateTimeElapsed(result["time_elapsed"])
            print_job.updateTimeTotal(result["time_total"])
            print_job.updateName(result["name"])
        elif status_code == 404:
            # No job found, so delete the active print job (if any!)
            printer.updateActivePrintJob(None)
        else:
            Logger.log("w",
                       "Got status code {status_code} while trying to get printer data".format(status_code=status_code))

    def _onGetPrinterDataFinished(self, reply):
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status_code == 200:
            try:
                result = json.loads(bytes(reply.readAll()).decode("utf-8"))
            except json.decoder.JSONDecodeError:
                Logger.log("w", "Received an invalid printer state message: Not valid JSON.")
                return

            if not self._printers:
                self._printers = [PrinterOutputModel(output_controller=None, number_of_extruders=self._number_of_extruders)]

            # LegacyUM3 always has a single printer.
            printer = self._printers[0]
            printer.updateBedTemperature(result["bed"]["temperature"]["current"])
            printer.updateTargetBedTemperature(result["bed"]["temperature"]["target"])
            printer.updatePrinterState(result["status"])

            for index in range(0, self._number_of_extruders):
                temperatures = result["heads"][0]["extruders"][index]["hotend"]["temperature"]
                extruder = printer.extruders[index]
                extruder.updateTargetHotendTemperature(temperatures["target"])
                extruder.updateHotendTemperature(temperatures["current"])

                material_guid = result["heads"][0]["extruders"][index]["active_material"]["guid"]

                if extruder.activeMaterial is None or extruder.activeMaterial.guid != material_guid:
                    # Find matching material (as we need to set brand, type & color)
                    containers = ContainerRegistry.getInstance().findInstanceContainers(type="material",
                                                                                        GUID=material_guid)
                    if containers:
                        color = containers[0].getMetaDataEntry("color_code")
                        brand = containers[0].getMetaDataEntry("brand")
                        material_type = containers[0].getMetaDataEntry("material")
                    else:
                        # Unknown material.
                        color = "#00000000"
                        brand = "Unknown"
                        material_type = "Unknown"
                    material = MaterialOutputModel(guid=material_guid, type=material_type,
                                                   brand=brand, color=color)
                    extruder.updateActiveMaterial(material)

                try:
                    hotend_id = result["heads"][0]["extruders"][index]["hotend"]["id"]
                except KeyError:
                    hotend_id = ""
                printer.extruders[index].updateHotendID(hotend_id)

        else:
            Logger.log("w",
                       "Got status code {status_code} while trying to get printer data".format(status_code = status_code))
