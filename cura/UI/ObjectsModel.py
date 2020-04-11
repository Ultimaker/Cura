# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from UM.Logger import Logger
import re
from typing import Any, Dict, List, Optional, Union

from PyQt5.QtCore import QTimer, Qt

from UM.Application import Application
from UM.Qt.ListModel import ListModel
from UM.Scene.Camera import Camera
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Selection import Selection
from UM.i18n import i18nCatalog

catalog = i18nCatalog("cura")


# Simple convenience class to keep stuff together. Since we're still stuck on python 3.5, we can't use the full
# typed named tuple, so we have to do it like this.
# Once we are at python 3.6, feel free to change this to a named tuple.
class _NodeInfo:
    def __init__(self, index_to_node: Optional[Dict[int, SceneNode]] = None, nodes_to_rename: Optional[List[SceneNode]] = None, is_group: bool = False) -> None:
        if index_to_node is None:
            index_to_node = {}
        if nodes_to_rename is None:
            nodes_to_rename = []
        self.index_to_node = index_to_node  # type: Dict[int, SceneNode]
        self.nodes_to_rename = nodes_to_rename  # type: List[SceneNode]
        self.is_group = is_group  # type: bool


##  Keep track of all objects in the project
class ObjectsModel(ListModel):
    NameRole = Qt.UserRole + 1
    SelectedRole = Qt.UserRole + 2
    OutsideAreaRole = Qt.UserRole + 3
    BuilplateNumberRole = Qt.UserRole + 4
    NodeRole = Qt.UserRole + 5
    PerObjectSettingsCountRole = Qt.UserRole + 6
    MeshTypeRole = Qt.UserRole + 7
    ExtruderNumberRole = Qt.UserRole + 8

    def __init__(self, parent = None) -> None:
        super().__init__(parent)

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.SelectedRole, "selected")
        self.addRoleName(self.OutsideAreaRole, "outside_build_area")
        self.addRoleName(self.BuilplateNumberRole, "buildplate_number")
        self.addRoleName(self.ExtruderNumberRole, "extruder_number")
        self.addRoleName(self.PerObjectSettingsCountRole, "per_object_settings_count")
        self.addRoleName(self.MeshTypeRole, "mesh_type")
        self.addRoleName(self.NodeRole, "node")

        Application.getInstance().getController().getScene().sceneChanged.connect(self._updateSceneDelayed)
        Application.getInstance().getPreferences().preferenceChanged.connect(self._updateDelayed)
        Selection.selectionChanged.connect(self._updateDelayed)

        self._update_timer = QTimer()
        self._update_timer.setInterval(200)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._update)

        self._build_plate_number = -1

        self._group_name_template = catalog.i18nc("@label", "Group #{group_nr}")
        self._group_name_prefix = self._group_name_template.split("#")[0]

        self._naming_regex = re.compile("^(.+)\(([0-9]+)\)$")

    def setActiveBuildPlate(self, nr: int) -> None:
        if self._build_plate_number != nr:
            self._build_plate_number = nr
            self._update()

    def _updateSceneDelayed(self, source) -> None:
        if not isinstance(source, Camera):
            self._update_timer.start()

    def _updateDelayed(self, *args) -> None:
        self._update_timer.start()

    def _shouldNodeBeHandled(self, node: SceneNode) -> bool:
        is_group = bool(node.callDecoration("isGroup"))
        if not node.callDecoration("isSliceable") and not is_group:
            return False

        parent = node.getParent()
        if parent and parent.callDecoration("isGroup"):
            return False  # Grouped nodes don't need resetting as their parent (the group) is resetted)

        node_build_plate_number = node.callDecoration("getBuildPlateNumber")
        if Application.getInstance().getPreferences().getValue("view/filter_current_build_plate") and node_build_plate_number != self._build_plate_number:
            return False

        return True

    def _renameNodes(self, node_info_dict: Dict[str, _NodeInfo]) -> List[SceneNode]:
        # Go through all names and find out the names for all nodes that need to be renamed.
        all_nodes = []  # type: List[SceneNode]
        for name, node_info in node_info_dict.items():
            # First add the ones that do not need to be renamed.
            for node in node_info.index_to_node.values():
                all_nodes.append(node)

            # Generate new names for the nodes that need to be renamed
            current_index = 0
            for node in node_info.nodes_to_rename:
                current_index += 1
                while current_index in node_info.index_to_node:
                    current_index += 1

                if not node_info.is_group:
                    new_group_name = "{0}({1})".format(name, current_index)
                else:
                    new_group_name = "{0}#{1}".format(name, current_index)

                old_name = node.getName()
                node.setName(new_group_name)
                Logger.log("d", "Node [%s] renamed to [%s]", old_name, new_group_name)
                all_nodes.append(node)
        return all_nodes

    def _update(self, *args) -> None:
        nodes = []  # type: List[Dict[str, Union[str, int, bool, SceneNode]]]
        name_to_node_info_dict = {}  # type: Dict[str, _NodeInfo]
        for node in DepthFirstIterator(Application.getInstance().getController().getScene().getRoot()):  # type: ignore
            if not self._shouldNodeBeHandled(node):
                continue

            is_group = bool(node.callDecoration("isGroup"))

            force_rename = False
            if not is_group:
                # Handle names for individual nodes
                name = node.getName()

                name_match = self._naming_regex.fullmatch(name)
                if name_match is None:
                    original_name = name
                    name_index = 0
                else:
                    original_name = name_match.groups()[0]
                    name_index = int(name_match.groups()[1])
            else:
                # Handle names for grouped nodes
                original_name = self._group_name_prefix

                current_name = node.getName()
                if current_name.startswith(self._group_name_prefix):
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
                name_to_node_info_dict[original_name] = _NodeInfo(is_group = is_group)
            node_info = name_to_node_info_dict[original_name]
            if not force_rename and name_index not in node_info.index_to_node:
                node_info.index_to_node[name_index] = node
            else:
                node_info.nodes_to_rename.append(node)

        all_nodes = self._renameNodes(name_to_node_info_dict)

        for node in all_nodes:
            if hasattr(node, "isOutsideBuildArea"):
                is_outside_build_area = node.isOutsideBuildArea()  # type: ignore
            else:
                is_outside_build_area = False

            node_build_plate_number = node.callDecoration("getBuildPlateNumber")

            node_mesh_type = ""
            per_object_settings_count = 0

            per_object_stack = node.callDecoration("getStack")
            if per_object_stack:
                per_object_settings_count = per_object_stack.getTop().getNumInstances()

                for mesh_type in ["anti_overhang_mesh", "infill_mesh", "cutting_mesh", "support_mesh"]:
                    if per_object_stack.getProperty(mesh_type, "value"):
                        node_mesh_type = mesh_type
                        per_object_settings_count -= 1 # do not count this mesh type setting
                        break

            extruder_number = int(node.callDecoration("getActiveExtruderPosition"))
            if node_mesh_type == "anti_overhang_mesh":
                # for anti overhang meshes, the extruder nr is irrelevant
                extruder_number = -1

            nodes.append({
                "name": node.getName(),
                "selected": Selection.isSelected(node),
                "outside_build_area": is_outside_build_area,
                "buildplate_number": node_build_plate_number,
                "extruder_number": extruder_number,
                "per_object_settings_count": per_object_settings_count,
                "mesh_type": node_mesh_type,
                "node": node
            })

        nodes = sorted(nodes, key=lambda n: n["name"])
        self.setItems(nodes)
