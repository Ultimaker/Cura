# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Set, TYPE_CHECKING

from UM.Settings.ContainerRegistry import ContainerRegistry #To get the material profiles we need to send.
from UM.Job import Job #The interface we're implementing.
from UM.Logger import Logger

if TYPE_CHECKING:
    from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice

##  Asynchronous job to send material profiles to the printer.
#
#   This way it won't freeze up the interface while sending those materials.
class SendMaterialJob(Job):
    def __init__(self, material_ids: Set[str], device: "NetworkedPrinterDevice"):
        super().__init__()
        self.material_ids = material_ids
        self.device = device

    def run(self):
        container_registry = ContainerRegistry.getInstance()
        for material_id in self.material_ids:
            Logger.log("d", "Syncing material profile with printer: {material_id}".format(material_id = material_id))

            parts = []
            material = container_registry.findContainers(id = material_id)[0]
            serialized_material = material.serialize().encode("utf-8")
            parts.append(self.device._createFormPart("name=\"file\"; filename=\"{file_name}.xml.fdm_material\"".format(file_name = material_id), serialized_material))
            parts.append(self.device._createFormPart("name=\"filename\"", (material_id + ".xml.fdm_material").encode("utf-8"), "text/plain"))

            self.device.postFormWithParts(target = "/materials", parts = parts)