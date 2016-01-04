# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import Qt, pyqtSlot, QUrl

from UM.Application import Application
from UM.Qt.ListModel import ListModel
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator
from UM.Scene.SceneNode import SceneNode
from UM.Settings.SettingOverrideDecorator import SettingOverrideDecorator
from UM.Settings.ProfileOverrideDecorator import ProfileOverrideDecorator

from . import SettingOverrideModel

class PerObjectSettingsModel(ListModel):
    IdRole = Qt.UserRole + 1
    XRole = Qt.UserRole + 2
    YRole = Qt.UserRole + 3
    MaterialRole = Qt.UserRole + 4
    ProfileRole = Qt.UserRole + 5
    SettingsRole = Qt.UserRole + 6

    def __init__(self, parent = None):
        super().__init__(parent)
        self._scene = Application.getInstance().getController().getScene()
        self._root = self._scene.getRoot()
        self._root.transformationChanged.connect(self._updatePositions)
        self._root.childrenChanged.connect(self._updateNodes)
        self._updateNodes(None)

        self.addRoleName(self.IdRole,"id")
        self.addRoleName(self.XRole,"x")
        self.addRoleName(self.YRole,"y")
        self.addRoleName(self.MaterialRole, "material")
        self.addRoleName(self.ProfileRole, "profile")
        self.addRoleName(self.SettingsRole, "settings")

    @pyqtSlot("quint64", str)
    def setObjectProfile(self, object_id, profile_name):
        self.setProperty(self.find("id", object_id), "profile", profile_name)

        profile = None
        if profile_name != "global":
            profile = Application.getInstance().getMachineManager().findProfile(profile_name)

        node = self._scene.findObject(object_id)
        if profile:
            if not node.getDecorator(ProfileOverrideDecorator):
                node.addDecorator(ProfileOverrideDecorator())
            node.callDecoration("setProfile", profile)
        else:
            if node.getDecorator(ProfileOverrideDecorator):
                node.removeDecorator(ProfileOverrideDecorator)

    @pyqtSlot("quint64", str)
    def addSettingOverride(self, object_id, key):
        machine = Application.getInstance().getMachineManager().getActiveMachineInstance()
        if not machine:
            return

        node = self._scene.findObject(object_id)
        if not node.getDecorator(SettingOverrideDecorator):
            node.addDecorator(SettingOverrideDecorator())

        node.callDecoration("addSetting", key)

    @pyqtSlot("quint64", str)
    def removeSettingOverride(self, object_id, key):
        node = self._scene.findObject(object_id)
        node.callDecoration("removeSetting", key)

        if len(node.callDecoration("getAllSettings")) == 0:
            node.removeDecorator(SettingOverrideDecorator)

    def _updatePositions(self, source):
        camera =  Application.getInstance().getController().getScene().getActiveCamera()
        for node in BreadthFirstIterator(self._root):
            if type(node) is not SceneNode or not node.getMeshData():
                continue

            projected_position = camera.project(node.getWorldPosition())

            index = self.find("id", id(node))
            self.setProperty(index, "x", float(projected_position[0]))
            self.setProperty(index, "y", float(projected_position[1]))

    def _updateNodes(self, source):
        self.clear()
        camera =  Application.getInstance().getController().getScene().getActiveCamera()
        for node in BreadthFirstIterator(self._root):
            if type(node) is not SceneNode or not node.getMeshData() or not node.isSelectable():
                continue

            projected_position = camera.project(node.getWorldPosition())

            node_profile = node.callDecoration("getProfile")
            if not node_profile:
                node_profile = "global"
            else:
                node_profile = node_profile.getName()

            self.appendItem({
                "id": id(node),
                "x": float(projected_position[0]),
                "y": float(projected_position[1]),
                "material": "",
                "profile": node_profile,
                "settings": SettingOverrideModel.SettingOverrideModel(node)
            })
