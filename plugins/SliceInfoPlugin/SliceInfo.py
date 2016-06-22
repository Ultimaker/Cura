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

import collections
import json
import os.path
import copy
import platform
import math
import urllib.request
import urllib.parse

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
            self.send_slice_info_message = Message(catalog.i18nc("@info", "Cura automatically sends slice info. You can disable this in preferences"), lifetime = 0, dismissable = False)
            self.send_slice_info_message.addAction("Dismiss", catalog.i18nc("@action:button", "Dismiss"), None, "")
            self.send_slice_info_message.actionTriggered.connect(self.messageActionTriggered)
            self.send_slice_info_message.show()

    def messageActionTriggered(self, message_id, action_id):
        self.send_slice_info_message.hide()
        Preferences.getInstance().setValue("info/asked_send_slice_info", True)

    def _onWriteStarted(self, output_device):
        if not Preferences.getInstance().getValue("info/send_slice_info"):
            Logger.log("d", "'info/send_slice_info' is turned off.")
            return # Do nothing, user does not want to send data

        global_container_stack = Application.getInstance().getGlobalContainerStack()

        # Get total material used (in mm^3)
        print_information = Application.getInstance().getPrintInformation()
        material_radius = 0.5 * global_container_stack.getProperty("material_diameter", "value")
        material_used = math.pi * material_radius * material_radius * print_information.materialAmount #Volume of material used

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
            "printtime": str(print_information.currentPrintTime),
            "filament": material_used,
            "language": Preferences.getInstance().getValue("general/language"),
            "materials_profiles ": {}
        }
        for container in global_container_stack.getContainers():
            submitted_data["settings_%s" %(container.getId())] = container.serialize() # This can be anything, eg. INI, JSON, etc.

        # Convert data to bytes
        submitted_data = urllib.parse.urlencode(submitted_data)
        binary_data = submitted_data.encode("utf-8")

        # Submit data
        try:
            f = urllib.request.urlopen(self.info_url, data = binary_data, timeout = 1)
            Logger.log("i", "Sent anonymous slice info to %s", self.info_url)
            f.close()
        except Exception as e:
            Logger.logException("e", e)
