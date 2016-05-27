# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import Qt, pyqtSlot, QUrl

from UM.Application import Application
from UM.Qt.ListModel import ListModel
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator
from UM.Scene.SceneNode import SceneNode
#from UM.Settings.SettingOverrideDecorator import SettingOverrideDecorator
#from UM.Settings.ProfileOverrideDecorator import ProfileOverrideDecorator

from . import SettingOverrideModel

class PerObjectSettingsModel(ListModel):
    IdRole = Qt.UserRole + 1  # ID of the node

    def __init__(self, parent = None):
        super().__init__(parent)
        self._scene = Application.getInstance().getController().getScene()
        self._root = self._scene.getRoot()
        self.addRoleName(self.IdRole,"id")

        self._updateModel()

    @pyqtSlot("quint64", str)
    def setObjectProfile(self, object_id, profile_name):
        self.setProperty(self.find("id", object_id), "profile", profile_name)

        profile = None
        '''if profile_name != "global":
            profile = Application.getInstance().getMachineManager().findProfile(profile_name)

        node = self._scene.findObject(object_id)
        if profile:
            if not node.getDecorator(ProfileOverrideDecorator):
                node.addDecorator(ProfileOverrideDecorator())
            node.callDecoration("setProfile", profile)
        else:
            if node.getDecorator(ProfileOverrideDecorator):
                node.removeDecorator(ProfileOverrideDecorator)'''

    @pyqtSlot("quint64", str)
    def addOverride(self, object_id, key):
        machine = Application.getInstance().getMachineManager().getActiveMachineInstance()
        if not machine:
            return

        node = self._scene.findObject(object_id)
        #if not node.getDecorator(SettingOverrideDecorator):
        #    node.addDecorator(SettingOverrideDecorator())

        node.callDecoration("addSetting", key)

    @pyqtSlot("quint64", str)
    def removerOverride(self, object_id, key):
        node = self._scene.findObject(object_id)
        node.callDecoration("removeSetting", key)

        #if len(node.callDecoration("getAllSettings")) == 0:
        #    node.removeDecorator(SettingOverrideDecorator)

    def _updateModel(self):
        self.clear()

        for node in BreadthFirstIterator(self._root):
            if type(node) is not SceneNode or not node.isSelectable():
                continue

            node_stack = node.callDecoration("getStack")

            if not node_stack:
                self.appendItem({
                    "id": id(node)
                })
