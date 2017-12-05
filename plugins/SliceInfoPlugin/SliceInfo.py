# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

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
    info_url = "https://stats.ultimaker.com/api/cura"

    def __init__(self):
        super().__init__()
        Application.getInstance().getOutputDeviceManager().writeStarted.connect(self._onWriteStarted)
        Preferences.getInstance().addPreference("info/send_slice_info", True)
        Preferences.getInstance().addPreference("info/asked_send_slice_info", False)

        if not Preferences.getInstance().getValue("info/asked_send_slice_info") and Preferences.getInstance().getValue("info/send_slice_info"):
            self.send_slice_info_message = Message(catalog.i18nc("@info", "Cura collects anonymised slicing statistics. You can disable this in the preferences."),
                                                   lifetime = 0,
                                                   dismissable = False,
                                                   title = catalog.i18nc("@info:title", "Collecting Data"))

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

            active_mode = Preferences.getInstance().getValue("cura/active_mode")
            if active_mode == 0:
                data["active_mode"] = "recommended"
            else:
                data["active_mode"] = "custom"

            definition_changes = global_container_stack.definitionChanges
            machine_settings_changed_by_user = False
            if definition_changes.getId() != "empty":
                # Now a definition_changes container will always be created for a stack,
                # so we also need to check if there is any instance in the definition_changes container
                if definition_changes.getAllKeys():
                    machine_settings_changed_by_user = True

            data["machine_settings_changed_by_user"] = machine_settings_changed_by_user
            data["language"] = Preferences.getInstance().getValue("general/language")
            data["os"] = {"type": platform.system(), "version": platform.version()}

            data["active_machine"] = {"definition_id": global_container_stack.definition.getId(), "manufacturer": global_container_stack.definition.getMetaData().get("manufacturer","")}

            # add extruder specific data to slice info
            data["extruders"] = []
            extruders = list(ExtruderManager.getInstance().getMachineExtruders(global_container_stack.getId()))
            extruders = sorted(extruders, key = lambda extruder: extruder.getMetaDataEntry("position"))

            for extruder in extruders:
                extruder_dict = dict()
                extruder_dict["active"] = ExtruderManager.getInstance().getActiveExtruderStack() == extruder
                extruder_dict["material"] = {"GUID": extruder.material.getMetaData().get("GUID", ""),
                                             "type": extruder.material.getMetaData().get("material", ""),
                                             "brand": extruder.material.getMetaData().get("brand", "")
                                             }
                extruder_dict["material_used"] = print_information.materialLengths[int(extruder.getMetaDataEntry("position", "0"))]
                extruder_dict["variant"] = extruder.variant.getName()
                extruder_dict["nozzle_size"] = extruder.getProperty("machine_nozzle_size", "value")

                extruder_settings = dict()
                extruder_settings["wall_line_count"] = extruder.getProperty("wall_line_count", "value")
                extruder_settings["retraction_enable"] = extruder.getProperty("retraction_enable", "value")
                extruder_settings["infill_sparse_density"] = extruder.getProperty("infill_sparse_density", "value")
                extruder_settings["infill_pattern"] = extruder.getProperty("infill_pattern", "value")
                extruder_settings["gradual_infill_steps"] = extruder.getProperty("gradual_infill_steps", "value")
                extruder_settings["default_material_print_temperature"] = extruder.getProperty("default_material_print_temperature", "value")
                extruder_settings["material_print_temperature"] = extruder.getProperty("material_print_temperature", "value")
                extruder_dict["extruder_settings"] = extruder_settings
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
                    model["transformation"] = {"data": str(node.getWorldTransformation().getData()).replace("\n", "")}
                    extruder_position = node.callDecoration("getActiveExtruderPosition")
                    model["extruder"] = 0 if extruder_position is None else int(extruder_position)

                    model_settings = dict()
                    model_stack = node.callDecoration("getStack")
                    if model_stack:
                        model_settings["support_enabled"] = model_stack.getProperty("support_enable", "value")
                        model_settings["support_extruder_nr"] = int(model_stack.getProperty("support_extruder_nr", "value"))

                        # Mesh modifiers;
                        model_settings["infill_mesh"] = model_stack.getProperty("infill_mesh", "value")
                        model_settings["cutting_mesh"] = model_stack.getProperty("cutting_mesh", "value")
                        model_settings["support_mesh"] = model_stack.getProperty("support_mesh", "value")
                        model_settings["anti_overhang_mesh"] = model_stack.getProperty("anti_overhang_mesh", "value")

                        model_settings["wall_line_count"] = model_stack.getProperty("wall_line_count", "value")
                        model_settings["retraction_enable"] = model_stack.getProperty("retraction_enable", "value")

                        # Infill settings
                        model_settings["infill_sparse_density"] = model_stack.getProperty("infill_sparse_density", "value")
                        model_settings["infill_pattern"] = model_stack.getProperty("infill_pattern", "value")
                        model_settings["gradual_infill_steps"] = model_stack.getProperty("gradual_infill_steps", "value")

                    model["model_settings"] = model_settings

                    data["models"].append(model)

            print_times = print_information._print_time_message_values
            data["print_times"] = {"travel": int(print_times["travel"].getDisplayString(DurationFormat.Format.Seconds)),
                                   "support": int(print_times["support"].getDisplayString(DurationFormat.Format.Seconds)),
                                   "infill": int(print_times["infill"].getDisplayString(DurationFormat.Format.Seconds)),
                                   "total": int(print_information.currentPrintTime.getDisplayString(DurationFormat.Format.Seconds))}

            print_settings = dict()
            print_settings["layer_height"] = global_container_stack.getProperty("layer_height", "value")

            # Support settings
            print_settings["support_enabled"] = global_container_stack.getProperty("support_enable", "value")
            print_settings["support_extruder_nr"] = int(global_container_stack.getProperty("support_extruder_nr", "value"))

            # Platform adhesion settings
            print_settings["adhesion_type"] = global_container_stack.getProperty("adhesion_type", "value")

            # Shell settings
            print_settings["wall_line_count"] = global_container_stack.getProperty("wall_line_count", "value")
            print_settings["retraction_enable"] = global_container_stack.getProperty("retraction_enable", "value")

            # Prime tower settings
            print_settings["prime_tower_enable"] = global_container_stack.getProperty("prime_tower_enable", "value")

            # Infill settings
            print_settings["infill_sparse_density"] = global_container_stack.getProperty("infill_sparse_density", "value")
            print_settings["infill_pattern"] = global_container_stack.getProperty("infill_pattern", "value")
            print_settings["gradual_infill_steps"] = global_container_stack.getProperty("gradual_infill_steps", "value")

            print_settings["print_sequence"] = global_container_stack.getProperty("print_sequence", "value")

            data["print_settings"] = print_settings

            # Send the name of the output device type that is used.
            data["output_to"] = type(output_device).__name__

            # Convert data to bytes
            binary_data = json.dumps(data).encode("utf-8")

            # Sending slice info non-blocking
            reportJob = SliceInfoJob(self.info_url, binary_data)
            reportJob.start()
        except Exception:
            # We really can't afford to have a mistake here, as this would break the sending of g-code to a device
            # (Either saving or directly to a printer). The functionality of the slice data is not *that* important.
            Logger.logException("e", "Exception raised while sending slice info.") # But we should be notified about these problems of course.
