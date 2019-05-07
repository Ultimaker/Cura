# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from collections import defaultdict
from typing import Dict

from PyQt5.QtCore import QTimer, Qt

from UM.Application import Application
from UM.Qt.ListModel import ListModel
from UM.Scene.Camera import Camera
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Selection import Selection
from UM.i18n import i18nCatalog

catalog = i18nCatalog("cura")


##  Keep track of all objects in the project
class ObjectsModel(ListModel):
    NameRole = Qt.UserRole + 1
    SelectedRole = Qt.UserRole + 2
    OutsideAreaRole = Qt.UserRole + 3
    BuilplateNumberRole = Qt.UserRole + 4
    NodeRole = Qt.UserRole + 5

    def __init__(self, parent = None) -> None:
        super().__init__(parent)

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.SelectedRole, "selected")
        self.addRoleName(self.OutsideAreaRole, "outside_build_area")
        self.addRoleName(self.BuilplateNumberRole, "buildplate_number")
        self.addRoleName(self.NodeRole, "node")

        Application.getInstance().getController().getScene().sceneChanged.connect(self._updateSceneDelayed)
        Application.getInstance().getPreferences().preferenceChanged.connect(self._updateDelayed)

        self._update_timer = QTimer()
        self._update_timer.setInterval(200)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._update)

        self._build_plate_number = -1

    def setActiveBuildPlate(self, nr: int) -> None:
        if self._build_plate_number != nr:
            self._build_plate_number = nr
            self._update()

    def _updateSceneDelayed(self, source) -> None:
        if not isinstance(source, Camera):
            self._update_timer.start()

    def _updateDelayed(self, *args) -> None:
        self._update_timer.start()

    def _update(self, *args) -> None:
        nodes = []
        filter_current_build_plate = Application.getInstance().getPreferences().getValue("view/filter_current_build_plate")
        active_build_plate_number = self._build_plate_number
        group_nr = 1
        name_count_dict = defaultdict(int)  # type: Dict[str, int]

        for node in DepthFirstIterator(Application.getInstance().getController().getScene().getRoot()):  # type: ignore
            if not isinstance(node, SceneNode):
                continue
            if (not node.getMeshData() and not node.callDecoration("getLayerData")) and not node.callDecoration("isGroup"):
                continue

            parent = node.getParent()
            if parent and parent.callDecoration("isGroup"):
                continue  # Grouped nodes don't need resetting as their parent (the group) is resetted)
            if not node.callDecoration("isSliceable") and not node.callDecoration("isGroup"):
                continue
            node_build_plate_number = node.callDecoration("getBuildPlateNumber")
            if filter_current_build_plate and node_build_plate_number != active_build_plate_number:
                continue

            if not node.callDecoration("isGroup"):
                name = node.getName()
                
            else:
                name = catalog.i18nc("@label", "Group #{group_nr}").format(group_nr = str(group_nr))
                group_nr += 1

            if hasattr(node, "isOutsideBuildArea"):
                is_outside_build_area = node.isOutsideBuildArea()  # type: ignore
            else:
                is_outside_build_area = False
                
            # Check if we already have an instance of the object based on name
            name_count_dict[name] += 1
            name_count = name_count_dict[name]

            if name_count > 1:
                name = "{0}({1})".format(name, name_count-1)
                node.setName(name)

            nodes.append({
                "name": name,
                "selected": Selection.isSelected(node),
                "outside_build_area": is_outside_build_area,
                "buildplate_number": node_build_plate_number,
                "node": node
            })
       
        nodes = sorted(nodes, key=lambda n: n["name"])
        self.setItems(nodes)

        self.itemsChanged.emit()
