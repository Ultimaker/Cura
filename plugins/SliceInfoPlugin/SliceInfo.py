# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import json
import os
import platform
import time
from typing import cast, Optional, Set

from PyQt5.QtCore import pyqtSlot, QObject

from UM.Extension import Extension
from UM.Application import Application
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Message import Message
from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.PluginRegistry import PluginRegistry
from UM.Qt.Duration import DurationFormat

from .SliceInfoJob import SliceInfoJob


catalog = i18nCatalog("cura")


##      This Extension runs in the background and sends several bits of information to the Ultimaker servers.
#       The data is only sent when the user in question gave permission to do so. All data is anonymous and
#       no model files are being sent (Just a SHA256 hash of the model).
class SliceInfo(QObject, Extension):
    info_url = "https://stats.ultimaker.com/api/cura"

    def __init__(self, parent = None):
        QObject.__init__(self, parent)
        Extension.__init__(self)

        self._application = Application.getInstance()

        self._application.getOutputDeviceManager().writeStarted.connect(self._onWriteStarted)
        self._application.getPreferences().addPreference("info/send_slice_info", True)
        self._application.getPreferences().addPreference("info/asked_send_slice_info", False)

        self._more_info_dialog = None
        self._example_data_content = None

        self._application.initializationFinished.connect(self._onAppInitialized)

    def _onAppInitialized(self):
        # DO NOT read any preferences values in the constructor because at the time plugins are created, no version
        # upgrade has been performed yet because version upgrades are plugins too!
        if self._more_info_dialog is None:
            self._more_info_dialog = self._createDialog("MoreInfoWindow.qml")

    ##  Perform action based on user input.
    #   Note that clicking "Disable" won't actually disable the data sending, but rather take the user to preferences where they can disable it.
    def messageActionTriggered(self, message_id, action_id):
        Application.getInstance().getPreferences().setValue("info/asked_send_slice_info", True)
        if action_id == "MoreInfo":
            self.showMoreInfoDialog()
        self.send_slice_info_message.hide()

    def showMoreInfoDialog(self):
        if self._more_info_dialog is None:
            self._more_info_dialog = self._createDialog("MoreInfoWindow.qml")
        self._more_info_dialog.show()

    def _createDialog(self, qml_name):
        Logger.log("d", "Creating dialog [%s]", qml_name)
        file_path = os.path.join(PluginRegistry.getInstance().getPluginPath(self.getPluginId()), qml_name)
        dialog = Application.getInstance().createQmlComponent(file_path, {"manager": self})
        return dialog

    @pyqtSlot(result = str)
    def getExampleData(self) -> Optional[str]:
        if self._example_data_content is None:
            plugin_path = PluginRegistry.getInstance().getPluginPath(self.getPluginId())
            if not plugin_path:
                Logger.log("e", "Could not get plugin path!", self.getPluginId())
                return None
            file_path = os.path.join(plugin_path, "example_data.html")
            if file_path:
                with open(file_path, "r", encoding = "utf-8") as f:
                    self._example_data_content = f.read()
        return self._example_data_content

    @pyqtSlot(bool)
    def setSendSliceInfo(self, enabled: bool):
        Application.getInstance().getPreferences().setValue("info/send_slice_info", enabled)

    def _getUserModifiedSettingKeys(self) -> list:
        from cura.CuraApplication import CuraApplication
        application = cast(CuraApplication, Application.getInstance())
        machine_manager = application.getMachineManager()
        global_stack = machine_manager.activeMachine

        user_modified_setting_keys = set()  # type: Set[str]

        for stack in [global_stack] + list(global_stack.extruders.values()):
            # Get all settings in user_changes and quality_changes
            all_keys = stack.userChanges.getAllKeys() | stack.qualityChanges.getAllKeys()
            user_modified_setting_keys |= all_keys

        return list(sorted(user_modified_setting_keys))

    def _onWriteStarted(self, output_device):
        try:
            if not Application.getInstance().getPreferences().getValue("info/send_slice_info"):
                Logger.log("d", "'info/send_slice_info' is turned off.")
                return  # Do nothing, user does not want to send data

            from cura.CuraApplication import CuraApplication
            application = cast(CuraApplication, Application.getInstance())
            machine_manager = application.getMachineManager()
            print_information = application.getPrintInformation()

            global_stack = machine_manager.activeMachine

            data = dict()  # The data that we're going to submit.
            data["time_stamp"] = time.time()
            data["schema_version"] = 0
            data["cura_version"] = application.getVersion()

            active_mode = Application.getInstance().getPreferences().getValue("cura/active_mode")
            if active_mode == 0:
                data["active_mode"] = "recommended"
            else:
                data["active_mode"] = "custom"

            data["camera_view"] = application.getPreferences().getValue("general/camera_perspective_mode")
            if data["camera_view"] == "orthographic":
                data["camera_view"] = "orthogonal" #The database still only recognises the old name "orthogonal".

            definition_changes = global_stack.definitionChanges
            machine_settings_changed_by_user = False
            if definition_changes.getId() != "empty":
                # Now a definition_changes container will always be created for a stack,
                # so we also need to check if there is any instance in the definition_changes container
                if definition_changes.getAllKeys():
                    machine_settings_changed_by_user = True

            data["machine_settings_changed_by_user"] = machine_settings_changed_by_user
            data["language"] = Application.getInstance().getPreferences().getValue("general/language")
            data["os"] = {"type": platform.system(), "version": platform.version()}

            data["active_machine"] = {"definition_id": global_stack.definition.getId(),
                                      "manufacturer": global_stack.definition.getMetaDataEntry("manufacturer", "")}

            # add extruder specific data to slice info
            data["extruders"] = []
            extruders = list(global_stack.extruders.values())
            extruders = sorted(extruders, key = lambda extruder: extruder.getMetaDataEntry("position"))

            for extruder in extruders:
                extruder_dict = dict()
                extruder_dict["active"] = machine_manager.activeStack == extruder
                extruder_dict["material"] = {"GUID": extruder.material.getMetaData().get("GUID", ""),
                                             "type": extruder.material.getMetaData().get("material", ""),
                                             "brand": extruder.material.getMetaData().get("brand", "")
                                             }
                extruder_position = int(extruder.getMetaDataEntry("position", "0"))
                if len(print_information.materialLengths) > extruder_position:
                    extruder_dict["material_used"] = print_information.materialLengths[extruder_position]
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

            data["intent_category"] = global_stack.getIntentCategory()
            data["quality_profile"] = global_stack.quality.getMetaData().get("quality_type")

            data["user_modified_setting_keys"] = self._getUserModifiedSettingKeys()

            data["models"] = []
            # Listing all files placed on the build plate
            for node in DepthFirstIterator(application.getController().getScene().getRoot()):
                if node.callDecoration("isSliceable"):
                    model = dict()
                    model["hash"] = node.getMeshData().getHash()
                    bounding_box = node.getBoundingBox()
                    if not bounding_box:
                        continue
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
                        model_settings["support_extruder_nr"] = int(model_stack.getExtruderPositionValueWithDefault("support_extruder_nr"))

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

            print_times = print_information.printTimes()
            data["print_times"] = {"travel": int(print_times["travel"].getDisplayString(DurationFormat.Format.Seconds)),
                                   "support": int(print_times["support"].getDisplayString(DurationFormat.Format.Seconds)),
                                   "infill": int(print_times["infill"].getDisplayString(DurationFormat.Format.Seconds)),
                                   "total": int(print_information.currentPrintTime.getDisplayString(DurationFormat.Format.Seconds))}

            print_settings = dict()
            print_settings["layer_height"] = global_stack.getProperty("layer_height", "value")

            # Support settings
            print_settings["support_enabled"] = global_stack.getProperty("support_enable", "value")
            print_settings["support_extruder_nr"] = int(global_stack.getExtruderPositionValueWithDefault("support_extruder_nr"))

            # Platform adhesion settings
            print_settings["adhesion_type"] = global_stack.getProperty("adhesion_type", "value")

            # Shell settings
            print_settings["wall_line_count"] = global_stack.getProperty("wall_line_count", "value")
            print_settings["retraction_enable"] = global_stack.getProperty("retraction_enable", "value")

            # Prime tower settings
            print_settings["prime_tower_enable"] = global_stack.getProperty("prime_tower_enable", "value")

            # Infill settings
            print_settings["infill_sparse_density"] = global_stack.getProperty("infill_sparse_density", "value")
            print_settings["infill_pattern"] = global_stack.getProperty("infill_pattern", "value")
            print_settings["gradual_infill_steps"] = global_stack.getProperty("gradual_infill_steps", "value")

            print_settings["print_sequence"] = global_stack.getProperty("print_sequence", "value")

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
