# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import time
import numpy

from UM.Job import Job
from UM.Application import Application
from UM.Logger import Logger

from UM.Scene.SceneNode import SceneNode
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator

from cura.OneAtATimeIterator import OneAtATimeIterator

from . import Cura_pb2

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

                object_groups.append(temp_list)
                Job.yieldThread()
        else:
            temp_list = []
            for node in DepthFirstIterator(self._scene.getRoot()):
                if type(node) is SceneNode and node.getMeshData() and node.getMeshData().getVertices() is not None:
                    if not getattr(node, "_outside_buildarea", False):
                        temp_list.append(node)
                Job.yieldThread()
            object_groups.append(temp_list)

        self._scene.releaseLock()

        if not object_groups:
            return

        self._sendSettings(self._profile)

        slice_message = Cura_pb2.Slice()

        for group in object_groups:
            group_message = slice_message.object_lists.add()
            for object in group:
                print(object)
                mesh_data = object.getMeshData().getTransformed(object.getWorldTransformation())

                obj = group_message.objects.add()
                obj.id = id(object)

                verts = numpy.array(mesh_data.getVertices())
                verts[:,[1,2]] = verts[:,[2,1]]
                verts[:,1] *= -1
                obj.vertices = verts.tostring()

                self._handlePerObjectSettings(object, obj)

                Job.yieldThread()

            # Hack to add per-object settings also to the "MeshGroup" in CuraEngine
            # We really should come up with a better solution for this.
            self._handlePerObjectSettings(group[0], group_message)

        Logger.log("d", "Sending data to engine for slicing.")
        self._socket.sendMessage(slice_message)

        self.setResult(True)

    def _sendSettings(self, profile):
        msg = Cura_pb2.SettingList()
        for key, value in profile.getAllSettingValues(include_machine = True).items():
            s = msg.settings.add()
            s.name = key
            s.value = str(value).encode("utf-8")

        self._socket.sendMessage(msg)

    def _handlePerObjectSettings(self, node, message):
        profile = node.callDecoration("getProfile")
        if profile:
            for key, value in profile.getChangedSettingValues().items():
                setting = message.settings.add()
                setting.name = key
                setting.value = str(value).encode()

                Job.yieldThread()

        object_settings = node.callDecoration("getAllSettingValues")
        if not object_settings:
            return

        for key, value in object_settings.items():
            setting = message.settings.add()
            setting.name = key
            setting.value = str(value).encode()

            Job.yieldThread()
