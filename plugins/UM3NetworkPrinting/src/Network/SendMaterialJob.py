# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import os
from typing import Dict, TYPE_CHECKING, Set, List
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest

from UM.Job import Job
from UM.Logger import Logger
from cura.CuraApplication import CuraApplication
from cura.Utils.Threading import call_on_qt_thread

from ..Models.Http.ClusterMaterial import ClusterMaterial
from ..Models.LocalMaterial import LocalMaterial
from ..Messages.MaterialSyncMessage import MaterialSyncMessage

import time
import threading

if TYPE_CHECKING:
    from .LocalClusterOutputDevice import LocalClusterOutputDevice


class SendMaterialJob(Job):

    """Asynchronous job to send material profiles to the printer.

    This way it won't freeze up the interface while sending those materials.
    """
    def __init__(self, device: "LocalClusterOutputDevice") -> None:
        super().__init__()
        self.device = device  # type: LocalClusterOutputDevice

        self._send_material_thread = threading.Thread(target = self._sendMissingMaterials)
        self._send_material_thread.setDaemon(True)

        self._remote_materials = {}  # type: Dict[str, ClusterMaterial]

    def run(self) -> None:
        """Send the request to the printer and register a callback"""

        self.device.getMaterials(on_finished = self._onGetMaterials)

    def _onGetMaterials(self, materials: List[ClusterMaterial]) -> None:
        """Callback for when the remote materials were returned."""

        remote_materials_by_guid = {material.guid: material for material in materials}
        self._remote_materials = remote_materials_by_guid
        # It's not the nicest way to do it, but if we don't handle this in a thread
        # we are blocking the main interface (even though the original call was done in a job)
        # This should really be refactored so that calculating the list of materials that need to be sent
        # to the printer is done outside of the job (and running the job actually sends the materials)
        # TODO: Fix this hack that was introduced for 4.9.1
        self._send_material_thread.start()

    def _sendMissingMaterials(self) -> None:
        """Determine which materials should be updated and send them to the printer.

        :param remote_materials_by_guid: The remote materials by GUID.
        """
        local_materials_by_guid = self._getLocalMaterials()
        if len(local_materials_by_guid) == 0:
            Logger.log("d", "There are no local materials to synchronize with the printer.")
            return
        material_ids_to_send = self._determineMaterialsToSend(local_materials_by_guid, self._remote_materials)
        if len(material_ids_to_send) == 0:
            Logger.log("d", "There are no remote materials to update.")
            return
        self._sendMaterials(material_ids_to_send)

    @staticmethod
    def _determineMaterialsToSend(local_materials: Dict[str, LocalMaterial],
                                  remote_materials: Dict[str, ClusterMaterial]) -> Set[str]:
        """From the local and remote materials, determine which ones should be synchronized.

        Makes a Set of id's containing only the id's of the materials that are not on the printer yet or the ones that
        are newer in Cura.
        :param local_materials: The local materials by GUID.
        :param remote_materials: The remote materials by GUID.
        """

        return {
            local_material.id
            for guid, local_material in local_materials.items()
            if guid not in remote_materials.keys() or local_material.version > remote_materials[guid].version
        }

    def _sendMaterials(self, materials_to_send: Set[str]) -> None:
        """Send the materials to the printer.

        The given materials will be loaded from disk en sent to to printer.
        The given id's will be matched with filenames of the locally stored materials.
        :param materials_to_send: A set with id's of materials that must be sent.
        """

        container_registry = CuraApplication.getInstance().getContainerRegistry()
        all_materials = container_registry.findInstanceContainersMetadata(type = "material")
        all_base_files = {material["base_file"] for material in all_materials if "base_file" in material}  # Filters out uniques by making it a set. Don't include files without base file (i.e. empty material).
        if "empty_material" in all_base_files:
            all_base_files.remove("empty_material")  # Don't send the empty material.

        for root_material_id in all_base_files:
            if root_material_id not in materials_to_send:
                # If the material does not have to be sent we skip it.
                continue

            file_path = container_registry.getContainerFilePathById(root_material_id)
            if not file_path:
                Logger.log("w", "Cannot get file path for material container [%s]", root_material_id)
                continue

            file_name = os.path.basename(file_path)
            self._sendMaterialFile(file_path, file_name, root_material_id)
            time.sleep(1)  # Throttle the sending a bit.

    # This needs to be called on the QT thread since the onFinished needs to happen
    # in the same thread as where the network manager is located (aka; main thread)
    @call_on_qt_thread
    def _sendMaterialFile(self, file_path: str, file_name: str, material_id: str) -> None:
        """Send a single material file to the printer.

        Also add the material signature file if that is available.
        :param file_path: The path of the material file.
        :param file_name: The name of the material file.
        :param material_id: The ID of the material in the file.
        """
        parts = []

        # Add the material file.
        try:
            with open(file_path, "rb") as f:
                parts.append(self.device.createFormPart("name=\"file\"; filename=\"{file_name}\""
                                                        .format(file_name = file_name), f.read()))
        except FileNotFoundError:
            Logger.error("Unable to send material {material_id}, since it has been deleted in the meanwhile.".format(material_id = material_id))
            return
        except EnvironmentError as e:
            Logger.error(f"Unable to send material {material_id}. We can't open that file for reading: {str(e)}")
            return

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

    def _sendingFinished(self, reply: QNetworkReply) -> None:
        """Check a reply from an upload to the printer and log an error when the call failed"""

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

    @staticmethod
    def _getLocalMaterials() -> Dict[str, LocalMaterial]:
        """Retrieves a list of local materials

        Only the new newest version of the local materials is returned
        :return: a dictionary of LocalMaterial objects by GUID
        """

        result = {}  # type: Dict[str, LocalMaterial]
        all_materials = CuraApplication.getInstance().getContainerRegistry().findInstanceContainersMetadata(type = "material")
        all_base_files = [material for material in all_materials if material["id"] == material.get("base_file")]  # Don't send materials without base_file: The empty material doesn't need to be sent.

        # Find the latest version of all material containers in the registry.
        for material_metadata in all_base_files:
            try:
                # material version must be an int
                material_metadata["version"] = int(material_metadata["version"])

                # Create a new local material
                local_material = LocalMaterial(**material_metadata)
                local_material.id = material_metadata["id"]

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
