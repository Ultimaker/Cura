# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from collections import namedtuple
import re
from typing import Any, Dict, List

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

        naming_regex = re.compile("^(.+)\(([0-9]+)\)$")

        NodeInfo = namedtuple("NodeInfo", ["index_to_node", "nodes_to_rename", "is_group"])
        name_to_node_info_dict = {}  # type: Dict[str, NodeInfo]

        group_name_template = catalog.i18nc("@label", "Group #{group_nr}")
        group_name_prefix = group_name_template.split("#")[0]

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

            is_group = bool(node.callDecoration("isGroup"))
            force_rename = False
            if not is_group:
                # Handle names for individual nodes
                name = node.getName()

                name_match = naming_regex.fullmatch(name)
                if name_match is None:
                    original_name = name
                    name_index = 0
                else:
                    original_name = name_match.groups()[0]
                    name_index = int(name_match.groups()[1])

            else:
                # Handle names for grouped nodes
                original_name = group_name_prefix

                current_name = node.getName()
                if current_name.startswith(group_name_prefix):
                    name_index = int(current_name.split("#")[-1])
                else:
                    # Force rename this group because this node has not been named as a group yet, probably because
                    # it's a newly created group.
                    name_index = 0
                    force_rename = True

            if original_name not in name_to_node_info_dict:
                # Keep track of 2 things:
                #  - known indices for nodes which doesn't need to be renamed
                #  - a list of nodes that need to be renamed. When renaming then, we should avoid using the known indices.
                name_to_node_info_dict[original_name] = NodeInfo(index_to_node = {},
                                                                 nodes_to_rename = [],
                                                                 is_group = is_group)
            node_info_dict = name_to_node_info_dict[original_name]
            if not force_rename and name_index not in node_info_dict.index_to_node:
                node_info_dict.index_to_node[name_index] = node
            else:
                node_info_dict.nodes_to_rename.append(node)

        # Go through all names and rename the nodes that need to be renamed.
        node_rename_list = []  # type: List[Dict[str, Any]]
        for name, node_info_dict in name_to_node_info_dict.items():
            # First add the ones that do not need to be renamed.
            for node in node_info_dict.index_to_node.values():
                node_rename_list.append({"node": node})

            # Generate new names for the nodes that need to be renamed
            current_index = 0
            for node in node_info_dict.nodes_to_rename:
                current_index += 1
                while current_index in node_info_dict.index_to_node:
                    current_index += 1

                if not node_info_dict.is_group:
                    new_group_name = "{0}({1})".format(name, current_index)
                else:
                    new_group_name = "{0}#{1}".format(name, current_index)
                node_rename_list.append({"node": node,
                                         "new_name": new_group_name})

        for node_info in node_rename_list:
            node = node_info["node"]
            new_name = node_info.get("new_name")

            if hasattr(node, "isOutsideBuildArea"):
                is_outside_build_area = node.isOutsideBuildArea()  # type: ignore
            else:
                is_outside_build_area = False

            node_build_plate_number = node.callDecoration("getBuildPlateNumber")

            from UM.Logger import Logger

            if new_name is not None:
                old_name = node.getName()
                node.setName(new_name)
                Logger.log("d", "Node [%s] renamed to [%s]", old_name, new_name)

            nodes.append({
                "name": node.getName(),
                "selected": Selection.isSelected(node),
                "outside_build_area": is_outside_build_area,
                "buildplate_number": node_build_plate_number,
                "node": node
            })

        nodes = sorted(nodes, key=lambda n: n["name"])
        self.setItems(nodes)

        self.itemsChanged.emit()
