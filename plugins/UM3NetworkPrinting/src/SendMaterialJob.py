# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import json
import os
import urllib.parse
from typing import Dict, TYPE_CHECKING, Set

from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest

from UM.Application import Application
from UM.Job import Job
from UM.Logger import Logger
from UM.MimeTypeDatabase import MimeTypeDatabase
from UM.Resources import Resources
from cura.CuraApplication import CuraApplication
# Absolute imports don't work in plugins
from .Models import ClusterMaterial, LocalMaterial

if TYPE_CHECKING:
    from .ClusterUM3OutputDevice import ClusterUM3OutputDevice


##  Asynchronous job to send material profiles to the printer.
#
#   This way it won't freeze up the interface while sending those materials.
class SendMaterialJob(Job):

    def __init__(self, device: "ClusterUM3OutputDevice") -> None:
        super().__init__()
        self.device = device  # type: ClusterUM3OutputDevice

    ##  Send the request to the printer and register a callback
    def run(self) -> None:
        self.device.get("materials/", on_finished = self._onGetRemoteMaterials)

    ##  Process the materials reply from the printer.
    #
    #   \param reply The reply from the printer, a json file.
    def _onGetRemoteMaterials(self, reply: QNetworkReply) -> None:

        # Got an error from the HTTP request. If we did not receive a 200 something happened.
        if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) != 200:
            Logger.log("e", "Error fetching materials from printer: %s", reply.errorString())
            return

        # Collect materials from the printer's reply and send the missing ones if needed.
        remote_materials_by_guid = self._parseReply(reply)
        if remote_materials_by_guid:
            self._sendMissingMaterials(remote_materials_by_guid)

    ##  Determine which materials should be updated and send them to the printer.
    #
    #   \param remote_materials_by_guid The remote materials by GUID.
    def _sendMissingMaterials(self, remote_materials_by_guid: Dict[str, ClusterMaterial]) -> None:

        # Collect local materials
        local_materials_by_guid = self._getLocalMaterials()
        if len(local_materials_by_guid) == 0:
            Logger.log("d", "There are no local materials to synchronize with the printer.")
            return

        # Find out what materials are new or updated and must be sent to the printer
        material_ids_to_send = self._determineMaterialsToSend(local_materials_by_guid, remote_materials_by_guid)
        if len(material_ids_to_send) == 0:
            Logger.log("d", "There are no remote materials to update.")
            return

        # Send materials to the printer
        self._sendMaterials(material_ids_to_send)

    ##  From the local and remote materials, determine which ones should be synchronized.
    #
    #   Makes a Set of id's containing only the id's of the materials that are not on the printer yet or the ones that
    #   are newer in Cura.
    #
    #   \param local_materials The local materials by GUID.
    #   \param remote_materials The remote materials by GUID.
    @staticmethod
    def _determineMaterialsToSend(local_materials: Dict[str, LocalMaterial],
                                  remote_materials: Dict[str, ClusterMaterial]) -> Set[str]:
        return {
            material.id
            for guid, material in local_materials.items()
            if guid not in remote_materials or material.version > remote_materials[guid].version
        }

    ##  Send the materials to the printer.
    #
    #   The given materials will be loaded from disk en sent to to printer.
    #   The given id's will be matched with filenames of the locally stored materials.
    #
    #   \param materials_to_send A set with id's of materials that must be sent.
    def _sendMaterials(self, materials_to_send: Set[str]) -> None:
        file_paths = Resources.getAllResourcesOfType(CuraApplication.ResourceTypes.MaterialInstanceContainer)

        # Find all local material files and send them if needed.
        for file_path in file_paths:
            try:
                mime_type = MimeTypeDatabase.getMimeTypeForFile(file_path)
            except MimeTypeDatabase.MimeTypeNotFoundError:
                continue

            file_name = os.path.basename(file_path)
            material_id = urllib.parse.unquote_plus(mime_type.stripExtension(file_name))
            if material_id not in materials_to_send:
                # If the material does not have to be sent we skip it.
                continue

            self._sendMaterialFile(file_path, file_name, material_id)

    ##  Send a single material file to the printer.
    #
    #   Also add the material signature file if that is available.
    #
    #   \param file_path The path of the material file.
    #   \param file_name The name of the material file.
    #   \param material_id The ID of the material in the file.
    def _sendMaterialFile(self, file_path: str, file_name: str, material_id: str) -> None:

        parts = []

        # Add the material file.
        with open(file_path, "rb") as f:
            parts.append(self.device.createFormPart("name=\"file\"; filename=\"{file_name}\""
                                                    .format(file_name = file_name), f.read()))

        # Add the material signature file if needed.
        signature_file_path = "{}.sig".format(file_path)
        if os.path.exists(signature_file_path):
            signature_file_name = os.path.basename(signature_file_path)
            with open(signature_file_path, "rb") as f:
                parts.append(self.device.createFormPart("name=\"signature_file\"; filename=\"{file_name}\""
                                                        .format(file_name = signature_file_name), f.read()))

        Logger.log("d", "Syncing material {material_id} with cluster.".format(material_id = material_id))
        self.device.postFormWithParts(target = "materials/", parts = parts, on_finished = self.sendingFinished)

    ##  Check a reply from an upload to the printer and log an error when the call failed
    @staticmethod
    def sendingFinished(reply: QNetworkReply) -> None:
        if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) != 200:
            Logger.log("e", "Received error code from printer when syncing material: {code}, {text}".format(
                code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute),
                text = reply.errorString()
            ))

    ##  Parse the reply from the printer
    #
    #   Parses the reply to a "/materials" request to the printer
    #
    #   \return a dictionary of ClusterMaterial objects by GUID
    #   \throw KeyError Raised when on of the materials does not include a valid guid
    @classmethod
    def _parseReply(cls, reply: QNetworkReply) -> Dict[str, ClusterMaterial]:
        try:
            remote_materials = json.loads(reply.readAll().data().decode("utf-8"))
            return {material["guid"]: ClusterMaterial(**material) for material in remote_materials}
        except UnicodeDecodeError:
            Logger.log("e", "Request material storage on printer: I didn't understand the printer's answer.")
        except json.JSONDecodeError:
            Logger.log("e", "Request material storage on printer: I didn't understand the printer's answer.")
        except ValueError:
            Logger.log("e", "Request material storage on printer: Printer's answer had an incorrect value.")
        except TypeError:
            Logger.log("e", "Request material storage on printer: Printer's answer was missing a required value.")

    ##  Retrieves a list of local materials
    #
    #   Only the new newest version of the local materials is returned
    #
    #   \return a dictionary of LocalMaterial objects by GUID
    def _getLocalMaterials(self) -> Dict[str, LocalMaterial]:
        result = {}  # type: Dict[str, LocalMaterial]
        container_registry = Application.getInstance().getContainerRegistry()
        material_containers = container_registry.findContainersMetadata(type = "material")

        # Find the latest version of all material containers in the registry.
        for material in material_containers:
            try:
                # material version must be an int
                material["version"] = int(material["version"])

                # Create a new local material
                local_material = LocalMaterial(**material)

                if local_material.GUID not in result or \
                        local_material.version > result.get(local_material.GUID).version:
                    result[local_material.GUID] = local_material

            except KeyError:
                Logger.logException("w", "Local material {} has missing values.".format(material["id"]))
            except ValueError:
                Logger.logException("w", "Local material {} has invalid values.".format(material["id"]))
            except TypeError:
                Logger.logException("w", "Local material {} has invalid values.".format(material["id"]))

        return result
