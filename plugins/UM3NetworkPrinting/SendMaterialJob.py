# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import json #To understand the list of materials from the printer reply.
import os #To walk over material files.
import os.path #To filter on material files.
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest #To listen to the reply from the printer.
from typing import Any, Dict, Set, TYPE_CHECKING
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
    def __init__(self, device: "ClusterUM3OutputDevice") -> None:
        super().__init__()
        self.device = device #type: ClusterUM3OutputDevice

    def run(self) -> None:
        self.device.get("materials/", on_finished = self.sendMissingMaterials)

    def sendMissingMaterials(self, reply: QNetworkReply) -> None:
        if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) != 200: #Got an error from the HTTP request.
            Logger.log("e", "Couldn't request current material storage on printer. Not syncing materials.")
            return

        remote_materials_list = reply.readAll().data().decode("utf-8")
        try:
            remote_materials_list = json.loads(remote_materials_list)
        except json.JSONDecodeError:
            Logger.log("e", "Request material storage on printer: I didn't understand the printer's answer.")
            return
        try:
            remote_materials_by_guid = {material["guid"]: material for material in remote_materials_list} #Index by GUID.
        except KeyError:
            Logger.log("e", "Request material storage on printer: Printer's answer was missing GUIDs.")
            return

        container_registry = ContainerRegistry.getInstance()
        local_materials_list = filter(lambda material: ("GUID" in material and "version" in material and "id" in material), container_registry.findContainersMetadata(type = "material"))
        local_materials_by_guid = {material["GUID"]: material for material in local_materials_list if material["id"] == material["base_file"]}
        for material in local_materials_list: #For each GUID get the material with the highest version number.
            try:
                if int(material["version"]) > local_materials_by_guid[material["GUID"]]["version"]:
                    local_materials_by_guid[material["GUID"]] = material
            except ValueError:
                Logger.log("e", "Material {material_id} has invalid version number {number}.".format(material_id = material["id"], number = material["version"]))
                continue

        materials_to_send = set() #type: Set[Dict[str, Any]]
        for guid, material in local_materials_by_guid.items():
            if guid not in remote_materials_by_guid:
                materials_to_send.add(material["id"])
                continue
            try:
                if int(material["version"]) > remote_materials_by_guid[guid]["version"]:
                    materials_to_send.add(material["id"])
                    continue
            except KeyError:
                Logger.log("e", "Current material storage on printer was an invalid reply (missing version).")
                return

        for file_path in Resources.getAllResourcesOfType(CuraApplication.ResourceTypes.MaterialInstanceContainer):
            try:
                mime_type = MimeTypeDatabase.getMimeTypeForFile(file_path)
            except MimeTypeDatabase.MimeTypeNotFoundError:
                continue #Not the sort of file we'd like to send then.
            _, file_name = os.path.split(file_path)
            material_id = urllib.parse.unquote_plus(mime_type.stripExtension(file_name))
            if material_id not in materials_to_send:
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
            self.device.postFormWithParts(target = "materials/", parts = parts, on_finished = self.sendingFinished)

    def sendingFinished(self, reply: QNetworkReply):
        if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) != 200:
            Logger.log("e", "Received error code from printer when syncing material: {code}".format(code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)))
            Logger.log("e", reply.readAll().data().decode("utf-8"))