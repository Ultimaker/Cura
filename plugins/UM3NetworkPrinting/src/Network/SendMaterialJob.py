# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import os
from typing import Dict, TYPE_CHECKING, Set, List
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest

from UM.Job import Job
from UM.Logger import Logger
from cura.CuraApplication import CuraApplication

from ..Models.Http.ClusterMaterial import ClusterMaterial
from ..Models.LocalMaterial import LocalMaterial
from ..Messages.MaterialSyncMessage import MaterialSyncMessage

if TYPE_CHECKING:
    from .LocalClusterOutputDevice import LocalClusterOutputDevice


##  Asynchronous job to send material profiles to the printer.
#
#   This way it won't freeze up the interface while sending those materials.
class SendMaterialJob(Job):

    def __init__(self, device: "LocalClusterOutputDevice") -> None:
        super().__init__()
        self.device = device  # type: LocalClusterOutputDevice

    ##  Send the request to the printer and register a callback
    def run(self) -> None:
        self.device.getMaterials(on_finished = self._onGetMaterials)

    ##  Callback for when the remote materials were returned.
    def _onGetMaterials(self, materials: List[ClusterMaterial]) -> None:
        remote_materials_by_guid = {material.guid: material for material in materials}
        self._sendMissingMaterials(remote_materials_by_guid)

    ##  Determine which materials should be updated and send them to the printer.
    #   \param remote_materials_by_guid The remote materials by GUID.
    def _sendMissingMaterials(self, remote_materials_by_guid: Dict[str, ClusterMaterial]) -> None:
        local_materials_by_guid = self._getLocalMaterials()
        if len(local_materials_by_guid) == 0:
            Logger.log("d", "There are no local materials to synchronize with the printer.")
            return
        material_ids_to_send = self._determineMaterialsToSend(local_materials_by_guid, remote_materials_by_guid)
        if len(material_ids_to_send) == 0:
            Logger.log("d", "There are no remote materials to update.")
            return
        self._sendMaterials(material_ids_to_send)

    ##  From the local and remote materials, determine which ones should be synchronized.
    #   Makes a Set of id's containing only the id's of the materials that are not on the printer yet or the ones that
    #   are newer in Cura.
    #   \param local_materials The local materials by GUID.
    #   \param remote_materials The remote materials by GUID.
    @staticmethod
    def _determineMaterialsToSend(local_materials: Dict[str, LocalMaterial],
                                  remote_materials: Dict[str, ClusterMaterial]) -> Set[str]:
        return {
            local_material.id
            for guid, local_material in local_materials.items()
            if guid not in remote_materials.keys() or local_material.version > remote_materials[guid].version
        }

    ##  Send the materials to the printer.
    #   The given materials will be loaded from disk en sent to to printer.
    #   The given id's will be matched with filenames of the locally stored materials.
    #   \param materials_to_send A set with id's of materials that must be sent.
    def _sendMaterials(self, materials_to_send: Set[str]) -> None:
        container_registry = CuraApplication.getInstance().getContainerRegistry()
        material_manager = CuraApplication.getInstance().getMaterialManager()
        material_group_dict = material_manager.getAllMaterialGroups()

        for root_material_id in material_group_dict:
            if root_material_id not in materials_to_send:
                # If the material does not have to be sent we skip it.
                continue

            file_path = container_registry.getContainerFilePathById(root_material_id)
            if not file_path:
                Logger.log("w", "Cannot get file path for material container [%s]", root_material_id)
                continue

            file_name = os.path.basename(file_path)
            self._sendMaterialFile(file_path, file_name, root_material_id)

    ##  Send a single material file to the printer.
    #   Also add the material signature file if that is available.
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

        # FIXME: move form posting to API client
        self.device.postFormWithParts(target = "/cluster-api/v1/materials/", parts = parts,
                                      on_finished = self._sendingFinished)

    ##  Check a reply from an upload to the printer and log an error when the call failed
    def _sendingFinished(self, reply: QNetworkReply) -> None:
        if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) != 200:
            Logger.log("w", "Error while syncing material: %s", reply.errorString())
            return
        body = reply.readAll().data().decode('utf8')
        if "not added" in body:
            # For some reason the cluster returns a 200 sometimes even when syncing failed.
            return
        # Inform the user that materials have been synced. This message only shows itself when not already visible.
        # Because of the guards above it is not shown when syncing failed (which is not always an actual problem).
        MaterialSyncMessage(self.device).show()

    ##  Retrieves a list of local materials
    #   Only the new newest version of the local materials is returned
    #   \return a dictionary of LocalMaterial objects by GUID
    @staticmethod
    def _getLocalMaterials() -> Dict[str, LocalMaterial]:
        result = {}  # type: Dict[str, LocalMaterial]
        material_manager = CuraApplication.getInstance().getMaterialManager()
        material_group_dict = material_manager.getAllMaterialGroups()

        # Find the latest version of all material containers in the registry.
        for root_material_id, material_group in material_group_dict.items():
            material_metadata = material_group.root_material_node.getMetadata()

            try:
                # material version must be an int
                material_metadata["version"] = int(material_metadata["version"])

                # Create a new local material
                local_material = LocalMaterial(**material_metadata)
                local_material.id = root_material_id

                if local_material.GUID not in result or \
                        local_material.GUID not in result or \
                        local_material.version > result[local_material.GUID].version:
                    result[local_material.GUID] = local_material

            except KeyError:
                Logger.logException("w", "Local material {} has missing values.".format(material_metadata["id"]))
            except ValueError:
                Logger.logException("w", "Local material {} has invalid values.".format(material_metadata["id"]))
            except TypeError:
                Logger.logException("w", "Local material {} has invalid values.".format(material_metadata["id"]))

        return result
