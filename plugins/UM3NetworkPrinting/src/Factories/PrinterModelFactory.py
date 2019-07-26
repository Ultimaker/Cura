from typing import List, Any, Dict

from PyQt5.QtCore import QUrl

from cura.PrinterOutput.Models.PrinterOutputModel import PrinterOutputModel
from cura.PrinterOutput.PrinterOutputController import PrinterOutputController
from plugins.UM3NetworkPrinting.src.Models.ConfigurationChangeModel import ConfigurationChangeModel


class PrinterModelFactory:

    CAMERA_URL_FORMAT = "http://{ip_address}:8080/?action=stream"

    # Create a printer output model from some data.
    @classmethod
    def createPrinter(cls, output_controller: PrinterOutputController, ip_address: str, extruder_count: int = 2
                      ) -> PrinterOutputModel:
        printer = PrinterOutputModel(output_controller=output_controller, number_of_extruders=extruder_count)
        printer.setCameraUrl(QUrl(cls.CAMERA_URL_FORMAT.format(ip_address=ip_address)))
        return printer

    # Create a list of configuration change models.
    @classmethod
    def createConfigurationChanges(cls, data: List[Dict[str, Any]]) -> List[ConfigurationChangeModel]:
        return [ConfigurationChangeModel(
            type_of_change=change.get("type_of_change"),
            index=change.get("index"),
            target_name=change.get("target_name"),
            origin_name=change.get("origin_name")
        ) for change in data]
