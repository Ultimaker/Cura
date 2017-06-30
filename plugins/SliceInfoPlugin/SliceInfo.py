# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from cura.CuraApplication import CuraApplication
from cura.Settings.ExtruderManager import ExtruderManager

from UM.Extension import Extension
from UM.Application import Application
from UM.Preferences import Preferences
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Message import Message
from UM.i18n import i18nCatalog
from UM.Logger import Logger

import time

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
                return  # Do nothing, user does not want to send data

            global_container_stack = Application.getInstance().getGlobalContainerStack()
            print_information = Application.getInstance().getPrintInformation()

            data = dict()  # The data that we're going to submit.
            data["time_stamp"] = time.time()
            data["schema_version"] = 0
            data["cura_version"] = Application.getInstance().getVersion()
            data["active_mode"] = "" # TODO
            data["language"] = Preferences.getInstance().getValue("general/language")
            data["os"] = {"type": platform.system(), "version": platform.version()}

            data["active_machine_type"] = {"definition_id": global_container_stack.definition.getId()}

            data["extruders"] = []
            extruders = list(ExtruderManager.getInstance().getMachineExtruders(global_container_stack.getId()))
            extruders = sorted(extruders, key = lambda extruder: extruder.getMetaDataEntry("position"))

            if not extruders:
                extruders = [global_container_stack]

            for extruder in extruders:
                extruder_dict = dict()
                extruder_dict["active"] = ExtruderManager.getInstance().getActiveExtruderStack() == extruder
                extruder_dict["material"] = extruder.material.getMetaData().get("GUID", "")
                extruder_dict["material_used"] = print_information.materialLengths[int(extruder.getMetaDataEntry("position", "0"))]
                extruder_dict["variant"] = extruder.variant.getName()
                extruder_dict["nozzle_size"] = extruder.getProperty("machine_nozzle_size", "value")
                data["extruders"].append(extruder_dict)

            data["quality_profile"] = global_container_stack.quality.getMetaData().get("quality_type")

            data["models"] = []
            # Listing all files placed on the build plate
            for node in DepthFirstIterator(CuraApplication.getInstance().getController().getScene().getRoot()):
                if node.callDecoration("isSliceable"):
                    model = dict()
                    model["hash"] = node.getMeshData().getHash()
                    bounding_box = node.getBoundingBox()
                    model["bounding_box"] = {"minimum": {"x": bounding_box.minimum.x,
                                                         "y": bounding_box.minimum.y,
                                                         "z": bounding_box.minimum.z},
                                             "maximum": {"x": bounding_box.maximum.x,
                                                         "y": bounding_box.maximum.y,
                                                         "z": bounding_box.maximum.z}}
                    model["transformation"] = {"data": str(node.getWorldTransformation().getData())}
                    extruder_position = node.callDecoration("getActiveExtruderPosition")
                    model["extruder"] = 0 if extruder_position is None else extruder_position


            print_times= print_information.printTimesPerFeature
            data["print_times"] = {"travel": print_times["travel"].getDisplayString(DurationFormat.Format.Seconds),
                                   "support": print_times["support"].getDisplayString(DurationFormat.Format.Seconds),
                                   "infill": print_times["infill"].getDisplayString(DurationFormat.Format.Seconds),
                                   "total": print_information.currentPrintTime.getDisplayString(DurationFormat.Format.Seconds)}

            print_settings = dict()
            print_settings["layer_height"] = global_container_stack.getProperty("layer_height", "value")
            print_settings["support_enabled"] = global_container_stack.getProperty("support_enable", "value")
            print_settings["infill_density"] = None  # TODO: This can be different per extruder & model
            print_settings["infill_type"] = None  # TODO: This can be different per extruder & model
            print_settings["print_sequence"] = global_container_stack.getProperty("print_sequence", "value")
            print_settings["platform_adhesion"] = global_container_stack.getProperty("platform_adhesion", "value")
            print_settings["retraction_enable"] = None #TODO; Can be different per extruder.
            print_settings["travel_speed"] = None  # TODO; Can be different per extruder
            print_settings["cool_fan_enabled"] = None  # TODO; Can be different per extruder
            print_settings["bottom_thickness"] = None  # TODO; Can be different per extruder & per mesh
            print_settings["bottom_thickness"] = None  # TODO; Can be different per extruder & per mesh
            data["print_settings"] = print_settings
            #print(data)
            '''

            # Convert data to bytes
            submitted_data = urllib.parse.urlencode(submitted_data)
            binary_data = submitted_data.encode("utf-8")

            # Sending slice info non-blocking
            reportJob = SliceInfoJob(self.info_url, binary_data)
            reportJob.start()'''
        except Exception as e:
            # We really can't afford to have a mistake here, as this would break the sending of g-code to a device
            # (Either saving or directly to a printer). The functionality of the slice data is not *that* important.
            Logger.log("e", "Exception raised while sending slice info: %s" %(repr(e))) # But we should be notified about these problems of course.
