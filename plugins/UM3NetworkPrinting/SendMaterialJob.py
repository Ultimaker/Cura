# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import json #To understand the list of materials from the printer reply.
import os #To walk over material files.
import os.path #To filter on material files.
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest #To listen to the reply from the printer.
from typing import TYPE_CHECKING
import urllib.parse #For getting material IDs from their file names.

from UM.Job import Job #The interface we're implementing.
from UM.Logger import Logger
from UM.MimeTypeDatabase import MimeTypeDatabase #To strip the extensions of the material profile files.
from UM.Resources import Resources
from UM.Settings.ContainerRegistry import ContainerRegistry #To find the GUIDs of materials.

from cura.CuraApplication import CuraApplication #For the resource types.

if TYPE_CHECKING:
    from .ClusterUM3OutputDevice import ClusterUM3OutputDevice

##  Asynchronous job to send material profiles to the printer.
#
#   This way it won't freeze up the interface while sending those materials.
class SendMaterialJob(Job):
    def __init__(self, device: "ClusterUM3OutputDevice"):
        super().__init__()
        self.device = device #type: ClusterUM3OutputDevice

    def run(self) -> None:
        self.device.get("materials/", onFinished = self.sendMissingMaterials)

    def sendMissingMaterials(self, reply: QNetworkReply) -> None:
        if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) != 200: #Got an error from the HTTP request.
            Logger.log("e", "Couldn't request current material storage on printer. Not syncing materials.")
            return

        remote_materials_list = reply.readAll().data().decode("utf-8")
        try:
            remote_materials_list = json.loads(remote_materials_list)
        except json.JSONDecodeError:
            Logger.log("e", "Current material storage on printer was a corrupted reply.")
            return
        try:
            remote_materials_by_guid = {material["guid"]: material for material in remote_materials_list} #Index by GUID.
        except KeyError:
            Logger.log("e", "Current material storage on printer was an invalid reply (missing GUIDs).")
            return

        container_registry = ContainerRegistry.getInstance()
        for file_path in Resources.getAllResourcesOfType(CuraApplication.ResourceTypes.MaterialInstanceContainer):
            if not file_path.startswith(Resources.getDataStoragePath() + os.sep): #No built-in profiles.
                continue
            mime_type = MimeTypeDatabase.getMimeTypeForFile(file_path)
            _, file_name = os.path.split(file_path)
            material_id = urllib.parse.unquote_plus(mime_type.stripExtension(file_name))
            material_metadata = container_registry.findContainersMetadata(id = material_id)
            if len(material_metadata) == 0: #This profile is not loaded. It's probably corrupt and deactivated. Don't send it.
                continue
            material_metadata = material_metadata[0]
            if "GUID" not in material_metadata or "version" not in material_metadata: #Missing metadata? Faulty profile.
                continue
            material_guid = material_metadata["GUID"]
            material_version = material_metadata["version"]
            if material_guid in remote_materials_by_guid:
                if "version" not in remote_materials_by_guid:
                    Logger.log("e", "Current material storage on printer was an invalid reply (missing version).")
                    return
                if remote_materials_by_guid[material_guid]["version"] >= material_version: #Printer already knows this material and is up to date.
                    continue
            parts = []
            with open(file_path, "rb") as f:
                parts.append(self.device._createFormPart("name=\"file\"; filename=\"{file_name}\"".format(file_name = file_name), f.read()))
            signature_file_path = file_path + ".sig"
            if os.path.exists(signature_file_path):
                _, signature_file_name = os.path.split(signature_file_path)
                with open(signature_file_path, "rb") as f:
                    parts.append(self.device._createFormPart("name=\"signature_file\"; filename=\"{file_name}\"".format(file_name = signature_file_name), f.read()))

            Logger.log("d", "Syncing material {material_id} with cluster.".format(material_id = material_id))
            self.device.postFormWithParts(target = "materials/", parts = parts, onFinished = self.sendingFinished)

    def sendingFinished(self, reply: QNetworkReply):
        if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) != 200:
            Logger.log("e", "Received error code from printer when syncing material: {code}".format(code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)))
            Logger.log("e", reply.readAll().data().decode("utf-8"))