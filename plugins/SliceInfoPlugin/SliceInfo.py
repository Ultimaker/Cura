# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Extension import Extension
from UM.Application import Application
from UM.Preferences import Preferences
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode
from UM.Message import Message
from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.Platform import Platform
from UM.Qt.Duration import DurationFormat
from UM.Job import Job

import platform
import math
import urllib.request
import urllib.parse
import ssl

catalog = i18nCatalog("cura")

class SliceInfoJob(Job):
    data = None
    url = None

    def __init__(self, url, data):
        super().__init__()
        self.url = url
        self.data = data

    def run(self):
        if not self.url or not self.data:
            Logger.log("e", "URL or DATA for sending slice info was not set!")
            return

        # Submit data
        kwoptions = {"data" : self.data,
                     "timeout" : 5
                     }

        if Platform.isOSX():
            kwoptions["context"] = ssl._create_unverified_context()

        try:
            f = urllib.request.urlopen(self.url, **kwoptions)
            Logger.log("i", "Sent anonymous slice info to %s", self.url)
            f.close()
        except urllib.error.HTTPError as http_exception:
            Logger.log("e", "An HTTP error occurred while trying to send slice information: %s" % http_exception)
        except Exception as e: # We don't want any exception to cause problems
            Logger.log("e", "An exception occurred while trying to send slice information: %s" % e)

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

            global_container_stack = Application.getInstance().getGlobalContainerStack()

            # Get total material used (in mm^3)
            print_information = Application.getInstance().getPrintInformation()
            material_radius = 0.5 * global_container_stack.getProperty("material_diameter", "value")

            # TODO: Send material per extruder instead of mashing it on a pile
            material_used = math.pi * material_radius * material_radius * sum(print_information.materialLengths) #Volume of all materials used

            # Get model information (bounding boxes, hashes and transformation matrix)
            models_info = []
            for node in DepthFirstIterator(Application.getInstance().getController().getScene().getRoot()):
                if type(node) is SceneNode and node.getMeshData() and node.getMeshData().getVertices() is not None:
                    if not getattr(node, "_outside_buildarea", False):
                        model_info = {}
                        model_info["hash"] = node.getMeshData().getHash()
                        model_info["bounding_box"] = {}
                        model_info["bounding_box"]["minimum"] = {}
                        model_info["bounding_box"]["minimum"]["x"] = node.getBoundingBox().minimum.x
                        model_info["bounding_box"]["minimum"]["y"] = node.getBoundingBox().minimum.y
                        model_info["bounding_box"]["minimum"]["z"] = node.getBoundingBox().minimum.z

                        model_info["bounding_box"]["maximum"] = {}
                        model_info["bounding_box"]["maximum"]["x"] = node.getBoundingBox().maximum.x
                        model_info["bounding_box"]["maximum"]["y"] = node.getBoundingBox().maximum.y
                        model_info["bounding_box"]["maximum"]["z"] = node.getBoundingBox().maximum.z
                        model_info["transformation"] = str(node.getWorldTransformation().getData())

                        models_info.append(model_info)

            # Bundle the collected data
            submitted_data = {
                "processor": platform.processor(),
                "machine": platform.machine(),
                "platform": platform.platform(),
                "settings": global_container_stack.serialize(), # global_container with references on used containers
                "version": Application.getInstance().getVersion(),
                "modelhash": "None",
                "printtime": print_information.currentPrintTime.getDisplayString(DurationFormat.Format.ISO8601),
                "filament": material_used,
                "language": Preferences.getInstance().getValue("general/language"),
            }
            for container in global_container_stack.getContainers():
                container_id = container.getId()
                try:
                    container_serialized = container.serialize()
                except NotImplementedError:
                    Logger.log("w", "Container %s could not be serialized!", container_id)
                    continue

                if container_serialized:
                    submitted_data["settings_%s" %(container_id)] = container_serialized # This can be anything, eg. INI, JSON, etc.
                else:
                    Logger.log("i", "No data found in %s to be serialized!", container_id)

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