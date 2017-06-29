# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from cura.CuraApplication import CuraApplication

from UM.Extension import Extension
from UM.Application import Application
from UM.Preferences import Preferences
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Message import Message
from UM.i18n import i18nCatalog
from UM.Logger import Logger

from UM.Qt.Duration import DurationFormat

from .SliceInfoJob import SliceInfoJob

import platform
import math
import urllib.request
import urllib.parse
import json

catalog = i18nCatalog("cura")


##      This Extension runs in the background and sends several bits of information to the Ultimaker servers.
#       The data is only sent when the user in question gave permission to do so. All data is anonymous and
#       no model files are being sent (Just a SHA256 hash of the model).
class SliceInfo(Extension):
    info_url = "https://stats.youmagine.com/curastats/slice"

    def __init__(self):
        super().__init__()
        Application.getInstance().getOutputDeviceManager().writeStarted.connect(self._onWriteStarted)
        Preferences.getInstance().addPreference("info/send_slice_info", True)
        Preferences.getInstance().addPreference("info/asked_send_slice_info", False)

        if not Preferences.getInstance().getValue("info/asked_send_slice_info"):
            self.send_slice_info_message = Message(catalog.i18nc("@info", "Cura collects anonymised slicing statistics. You can disable this in preferences"), lifetime = 0, dismissable = False)
            self.send_slice_info_message.addAction("Dismiss", catalog.i18nc("@action:button", "Dismiss"), None, "")
            self.send_slice_info_message.actionTriggered.connect(self.messageActionTriggered)
            self.send_slice_info_message.show()

    def messageActionTriggered(self, message_id, action_id):
        self.send_slice_info_message.hide()
        Preferences.getInstance().setValue("info/asked_send_slice_info", True)

    def _onWriteStarted(self, output_device):
        try:
            if not Preferences.getInstance().getValue("info/send_slice_info"):
                Logger.log("d", "'info/send_slice_info' is turned off.")
                return # Do nothing, user does not want to send data

            # Listing all files placed on the buildplate
            modelhashes = []
            for node in DepthFirstIterator(CuraApplication.getInstance().getController().getScene().getRoot()):
                if node.callDecoration("isSliceable"):
                    modelhashes.append(node.getMeshData().getHash())

            # Creating md5sums and formatting them as discussed on JIRA
            modelhash_formatted = ",".join(modelhashes)

            global_container_stack = Application.getInstance().getGlobalContainerStack()

            # Get total material used (in mm^3)
            print_information = Application.getInstance().getPrintInformation()
            material_radius = 0.5 * global_container_stack.getProperty("material_diameter", "value")

            # Send material per extruder
            material_used = [str(math.pi * material_radius * material_radius * material_length) for material_length in print_information.materialLengths]
            material_used = ",".join(material_used)

            containers = { "": global_container_stack.serialize() }
            for container in global_container_stack.getContainers():
                container_id = container.getId()
                try:
                    container_serialized = container.serialize()
                except NotImplementedError:
                    Logger.log("w", "Container %s could not be serialized!", container_id)
                    continue
                if container_serialized:
                    containers[container_id] = container_serialized
                else:
                    Logger.log("i", "No data found in %s to be serialized!", container_id)

            # Bundle the collected data
            submitted_data = {
                "processor": platform.processor(),
                "machine": platform.machine(),
                "platform": platform.platform(),
                "settings": json.dumps(containers), # bundle of containers with their serialized contents
                "version": Application.getInstance().getVersion(),
                "modelhash": modelhash_formatted,
                "printtime": print_information.currentPrintTime.getDisplayString(DurationFormat.Format.ISO8601),
                "filament": material_used,
                "language": Preferences.getInstance().getValue("general/language"),
            }

            # Convert data to bytes
            submitted_data = urllib.parse.urlencode(submitted_data)
            binary_data = submitted_data.encode("utf-8")

            # Sending slice info non-blocking
            reportJob = SliceInfoJob(self.info_url, binary_data)
            reportJob.start()
        except Exception as e:
            # We really can't afford to have a mistake here, as this would break the sending of g-code to a device
            # (Either saving or directly to a printer). The functionality of the slice data is not *that* important.
            Logger.log("e", "Exception raised while sending slice info: %s" %(repr(e))) # But we should be notified about these problems of course.
