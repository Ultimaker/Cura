# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Extension import Extension
from UM.Application import Application
from UM.Preferences import Preferences
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode
from UM.Message import Message
from UM.i18n import i18nCatalog

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
            return # Do nothing, user does not want to send data
        settings = Application.getInstance().getMachineManager().getWorkingProfile()

        # Load all machine definitions and put them in machine_settings dict
        #setting_file_name = Application.getInstance().getActiveMachineInstance().getMachineSettings()._json_file
        machine_settings = {}
        #with open(setting_file_name, "rt", -1, "utf-8") as f:
        #    data = json.load(f, object_pairs_hook = collections.OrderedDict)
        #machine_settings[os.path.basename(setting_file_name)] = copy.deepcopy(data)
        active_machine_definition= Application.getInstance().getMachineManager().getActiveMachineInstance().getMachineDefinition()
        data = active_machine_definition._json_data
        # Loop through inherited json files
        setting_file_name = active_machine_definition._path
        while True:
            if "inherits" in data:
                inherited_setting_file_name = os.path.dirname(setting_file_name) + "/" + data["inherits"]
                with open(inherited_setting_file_name, "rt", -1, "utf-8") as f:
                    data = json.load(f, object_pairs_hook = collections.OrderedDict)
                machine_settings[os.path.basename(inherited_setting_file_name)] = copy.deepcopy(data)
            else:
                break


        profile_values = settings.getChangedSettings() # TODO: @UnusedVariable

        # Get total material used (in mm^3)
        print_information = Application.getInstance().getPrintInformation()
        material_radius = 0.5 * settings.getSettingValue("material_diameter")
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
            "machine_settings": json.dumps(machine_settings),
            "version": Application.getInstance().getVersion(),
            "modelhash": "None",
            "printtime": str(print_information.currentPrintTime),
            "filament": material_used,
            "language": Preferences.getInstance().getValue("general/language"),
            "materials_profiles ": {}
        }

        # Convert data to bytes
        submitted_data = urllib.parse.urlencode(submitted_data)
        binary_data = submitted_data.encode("utf-8")

        # Submit data
        try:
            f = urllib.request.urlopen("https://stats.youmagine.com/curastats/slice", data = binary_data, timeout = 1)
        except Exception as e:
            print("Exception occured", e)

        f.close()
