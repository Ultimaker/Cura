# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os #To walk over material files.
import os.path #To filter on material files.
from typing import TYPE_CHECKING

from UM.Job import Job #The interface we're implementing.
from UM.Logger import Logger
from UM.Resources import Resources

from cura.CuraApplication import CuraApplication

if TYPE_CHECKING:
    from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice

##  Asynchronous job to send material profiles to the printer.
#
#   This way it won't freeze up the interface while sending those materials.
class SendMaterialJob(Job):
    def __init__(self, device: "NetworkedPrinterDevice"):
        super().__init__()
        self.device = device

    def run(self):
        for file_path in Resources.getAllResourcesOfType(CuraApplication.ResourceTypes.MaterialInstanceContainer):
            if not file_path.startswith(Resources.getDataStoragePath() + os.sep):
                continue
            _, file_name = os.path.split(file_path)
            Logger.log("d", "Syncing material profile with printer: {file_name}".format(file_name = file_name))

            parts = []
            with open(file_path, "rb") as f:
                parts.append(self.device._createFormPart("name=\"file\"; filename=\"{file_name}\"".format(file_name = file_name), f.read()))
            parts.append(self.device._createFormPart("name=\"filename\"", file_name.encode("utf-8"), "text/plain"))

            without_extension, _ = os.path.splitext(file_path)
            signature_file_path = without_extension + ".sig"
            if os.path.exists(signature_file_path):
                _, signature_file_name = os.path.split(signature_file_path)
                with open(signature_file_path, "rb") as f:
                    parts.append(self.device._createFormPart("name=\"signature_file\"; filename=\"{file_name}\"".format(file_name = signature_file_name), f.read()))

            self.device.postFormWithParts(target = "/materials", parts = parts)