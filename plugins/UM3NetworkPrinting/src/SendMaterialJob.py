# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import json  # To understand the list of materials from the printer reply.
import os  # To walk over material files.
import os.path  # To filter on material files.
import urllib.parse  # For getting material IDs from their file names.
from typing import Dict, TYPE_CHECKING

from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest  # To listen to the reply from the printer.

from UM.Job import Job  # The interface we're implementing.
from UM.Logger import Logger
from UM.MimeTypeDatabase import MimeTypeDatabase  # To strip the extensions of the material profile files.
from UM.Resources import Resources
from UM.Settings.ContainerRegistry import ContainerRegistry  # To find the GUIDs of materials.
from cura.CuraApplication import CuraApplication  # For the resource types.
from plugins.UM3NetworkPrinting.src.Models import ClusterMaterial, LocalMaterial

if TYPE_CHECKING:
    from .ClusterUM3OutputDevice import ClusterUM3OutputDevice


##  Asynchronous job to send material profiles to the printer.
#
#   This way it won't freeze up the interface while sending those materials.
class SendMaterialJob(Job):
    def __init__(self, device: "ClusterUM3OutputDevice") -> None:
        super().__init__()
        self.device = device  # type: ClusterUM3OutputDevice

    def run(self) -> None:
        self.device.get("materials/", on_finished=self.sendMissingMaterials)

    def sendMissingMaterials(self, reply: QNetworkReply) -> None:
        if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) != 200:  # Got an error from the HTTP request.
            Logger.log("e", "Couldn't request current material storage on printer. Not syncing materials.")
            return

        # Collect materials from the printer's reply
        try:
            remote_materials_by_guid = self._parseReply(reply)
        except json.JSONDecodeError:
            Logger.log("e", "Request material storage on printer: I didn't understand the printer's answer.")
            return
        except KeyError:
            Logger.log("e", "Request material storage on printer: Printer's answer was missing GUIDs.")
            return

        # Collect local materials
        local_materials_by_guid = self._getLocalMaterials()

        # Find out what materials are new or updated annd must be sent to the printer
        materials_to_send = {
            material.id
            for guid, material in local_materials_by_guid.items()
            if guid not in remote_materials_by_guid or
               material.version > remote_materials_by_guid[guid].version
        }

        # Send materials to the printer
        self.sendMaterialsToPrinter(materials_to_send)

    def sendMaterialsToPrinter(self, materials_to_send):
        for file_path in Resources.getAllResourcesOfType(CuraApplication.ResourceTypes.MaterialInstanceContainer):
            try:
                mime_type = MimeTypeDatabase.getMimeTypeForFile(file_path)
            except MimeTypeDatabase.MimeTypeNotFoundError:
                continue  # Not the sort of file we'd like to send then.

            _, file_name = os.path.split(file_path)
            material_id = urllib.parse.unquote_plus(mime_type.stripExtension(file_name))

            if material_id not in materials_to_send:
                continue

            parts = []
            with open(file_path, "rb") as f:
                parts.append(
                    self.device._createFormPart("name=\"file\"; filename=\"{file_name}\"".format(file_name=file_name),
                                                f.read()))
            signature_file_path = file_path + ".sig"
            if os.path.exists(signature_file_path):
                _, signature_file_name = os.path.split(signature_file_path)
                with open(signature_file_path, "rb") as f:
                    parts.append(self.device._createFormPart(
                        "name=\"signature_file\"; filename=\"{file_name}\"".format(file_name=signature_file_name),
                        f.read()))

            Logger.log("d", "Syncing material {material_id} with cluster.".format(material_id=material_id))
            self.device.postFormWithParts(target="materials/", parts=parts, on_finished=self.sendingFinished)

    def sendingFinished(self, reply: QNetworkReply):
        if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) != 200:
            Logger.log("e", "Received error code from printer when syncing material: {code}".format(
                code=reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)))
            Logger.log("e", reply.readAll().data().decode("utf-8"))

    ##  Parse the reply from the printer
    #
    #   Parses the reply to a "/materials" request to the printer
    #
    #   \return a dictionary of ClustMaterial objects by GUID
    #   \throw json.JSONDecodeError Raised when the reply does not contain a valid json string
    #   \throw KeyErrror Raised when on of the materials does not include a valid guid
    @classmethod
    def _parseReply(cls, reply: QNetworkReply) -> Dict[str, ClusterMaterial]:
        remote_materials_list = json.loads(reply.readAll().data().decode("utf-8"))
        return {material["guid"]: ClusterMaterial(**material) for material in remote_materials_list}

    ##  Retrieves a list of local materials
    #
    #   Only the new newest version of the local materials is returned
    #
    #   \return a dictionary of LocalMaterial objects by GUID
    @classmethod
    def _getLocalMaterials(cls):
        result = {}
        for material in ContainerRegistry.getInstance().findContainersMetadata(type="material"):
            try:
                localMaterial = LocalMaterial(**material)

                if localMaterial.GUID not in result or localMaterial.version > result.get(localMaterial.GUID).version:
                    result[localMaterial.GUID] = localMaterial
            except (ValueError):
                Logger.log("e", "Material {material_id} has invalid version number {number}.".format(
                    material_id=material["id"], number=material["version"]))

        return result
