# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import numpy
from string import Formatter
import traceback

from UM.Job import Job
from UM.Application import Application
from UM.Logger import Logger

from UM.Scene.SceneNode import SceneNode
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator

from cura.OneAtATimeIterator import OneAtATimeIterator

##  Formatter class that handles token expansion in start/end gcod
class GcodeStartEndFormatter(Formatter):
    def get_value(self, key, args, kwargs): # [CodeStyle: get_value is an overridden function from the Formatter class]
        if isinstance(key, str):
            try:
                return kwargs[key]
            except KeyError:
                Logger.log("w", "Unable to replace '%s' placeholder in start/end gcode", key)
                return "{" + key + "}"
        else:
            Logger.log("w", "Incorrectly formatted placeholder '%s' in start/end gcode", key)
            return "{" + str(key) + "}"

##  Job class that handles sending the current scene data to CuraEngine
class StartSliceJob(Job):
    def __init__(self, profile, socket):
        super().__init__()

        self._scene = Application.getInstance().getController().getScene()
        self._profile = profile
        self._socket = socket

    def run(self):
        self._scene.acquireLock()

        for node in DepthFirstIterator(self._scene.getRoot()):
            if node.callDecoration("getLayerData"):
                node.getParent().removeChild(node)
                break

        object_groups = []
        if self._profile.getSettingValue("print_sequence") == "one_at_a_time":
            for node in OneAtATimeIterator(self._scene.getRoot()):
                temp_list = []

                if getattr(node, "_outside_buildarea", False):
                    continue

                children = node.getAllChildren()
                children.append(node)
                for child_node in children:
                    if type(child_node) is SceneNode and child_node.getMeshData() and child_node.getMeshData().getVertices() is not None:
                        temp_list.append(child_node)

                if temp_list:
                    object_groups.append(temp_list)
                Job.yieldThread()
            if len(object_groups) == 0:
                Logger.log("w", "No objects suitable for one at a time found, or no correct order found")
        else:
            temp_list = []
            for node in DepthFirstIterator(self._scene.getRoot()):
                if type(node) is SceneNode and node.getMeshData() and node.getMeshData().getVertices() is not None:
                    if not getattr(node, "_outside_buildarea", False):
                        temp_list.append(node)
                Job.yieldThread()

            if temp_list:
                object_groups.append(temp_list)

        self._scene.releaseLock()

        if not object_groups:
            return

        self._sendSettings(self._profile)

        slice_message = self._socket.createMessage("cura.proto.Slice")

        for group in object_groups:
            group_message = slice_message.addRepeatedMessage("object_lists")
            if group[0].getParent().callDecoration("isGroup"):
                self._handlePerObjectSettings(group[0].getParent(), group_message)
            for current_object in group:
                mesh_data = current_object.getMeshData().getTransformed(current_object.getWorldTransformation())

                obj = group_message.addRepeatedMessage("objects")
                obj.id = id(current_object)

                verts = numpy.array(mesh_data.getVertices())
                verts[:,[1,2]] = verts[:,[2,1]]
                verts[:,1] *= -1

                obj.vertices = verts

                self._handlePerObjectSettings(current_object, obj)

                Job.yieldThread()

        Logger.log("d", "Sending data to engine for slicing.")
        self._socket.sendMessage(slice_message)
        Logger.log("d", "Sending data to engine is completed")
        self.setResult(True)

    def _expandGcodeTokens(self, key, value, settings):
        try:
            # any setting can be used as a token
            fmt = GcodeStartEndFormatter()
            return str(fmt.format(value, **settings)).encode("utf-8")
        except:
            Logger.log("w", "Unabled to do token replacement on start/end gcode %s", traceback.format_exc())
            return str(value).encode("utf-8")

    def _sendSettings(self, profile):
        msg = self._socket.createMessage("cura.proto.SettingList");
        settings = profile.getAllSettingValues(include_machine = True)
        start_gcode = settings["machine_start_gcode"]
        settings["material_bed_temp_prepend"] = "{material_bed_temperature}" not in start_gcode
        settings["material_print_temp_prepend"] = "{material_print_temperature}" not in start_gcode
        for key, value in settings.items():
            s = msg.addRepeatedMessage("settings")
            s.name = key
            if key == "machine_start_gcode" or key == "machine_end_gcode":
                s.value = self._expandGcodeTokens(key, value, settings)
            else:
                s.value = str(value).encode("utf-8")

        self._socket.sendMessage(msg)

    def _handlePerObjectSettings(self, node, message):
        profile = node.callDecoration("getProfile")
        if profile:
            for key, value in profile.getAllSettingValues().items():
                setting = message.addRepeatedMessage("settings")
                setting.name = key
                setting.value = str(value).encode()

                Job.yieldThread()

        object_settings = node.callDecoration("getAllSettingValues")
        if not object_settings:
            return
        for key, value in object_settings.items():
            setting = message.addRepeatedMessage("settings")
            setting.name = key
            setting.value = str(value).encode()

            Job.yieldThread()
