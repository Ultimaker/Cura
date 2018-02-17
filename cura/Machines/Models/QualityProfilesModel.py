# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import Qt

from UM.Application import Application
from UM.Logger import Logger
from UM.Qt.ListModel import ListModel
from cura.Machines.QualityManager import QualityGroup


#
# QML Model for all built-in quality profiles.
#
class QualityProfilesModel(ListModel):
    IdRole = Qt.UserRole + 1
    NameRole = Qt.UserRole + 2
    QualityTypeRole = Qt.UserRole + 3
    LayerHeightRole = Qt.UserRole + 4
    AvailableRole = Qt.UserRole + 5
    QualityGroupRole = Qt.UserRole + 6
    QualityChangesGroupRole = Qt.UserRole + 7

    def __init__(self, parent = None):
        super().__init__(parent)

        self.addRoleName(self.IdRole, "id")
        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.QualityTypeRole, "quality_type")
        self.addRoleName(self.LayerHeightRole, "layer_height")
        self.addRoleName(self.AvailableRole, "available")
        self.addRoleName(self.QualityGroupRole, "quality_group")
        self.addRoleName(self.QualityChangesGroupRole, "quality_changes_group")

        # connect signals
        Application.getInstance().globalContainerStackChanged.connect(self._update)
        Application.getInstance().getMachineManager().activeQualityGroupChanged.connect(self._update)

        self._quality_manager = Application.getInstance()._quality_manager

        self._layer_height_unit = ""  # This is cached

    def _update(self):
        Logger.log("d", "Updating quality profile model ...")

        active_global_stack = Application.getInstance().getMachineManager()._global_container_stack
        if active_global_stack is None:
            self.setItems([])
            Logger.log("d", "No active GlobalStack, set quality profile model as empty.")
            return

        quality_group_dict = self._quality_manager.getQualityGroups(active_global_stack)

        item_list = []
        for key in sorted(quality_group_dict):
            quality_group = quality_group_dict[key]

            layer_height = self._fetchLayerHeight(quality_group)

            item = {"id": "TODO",  # TODO: probably will be removed
                    "name": quality_group.name,
                    "quality_type": quality_group.quality_type,
                    "layer_height": layer_height + self._layer_height_unit,
                    "layer_height_without_unit": layer_height,
                    "available": quality_group.is_available,
                    "quality_group": quality_group}

            item_list.append(item)

        # Sort items based on layer_height
        item_list = sorted(item_list, key = lambda x: float(x["layer_height_without_unit"]))

        self.setItems(item_list)

    def _fetchLayerHeight(self, quality_group: "QualityGroup"):
        active_global_stack = Application.getInstance().getMachineManager()._global_container_stack
        if not self._layer_height_unit:
            unit = active_global_stack.definition.getProperty("layer_height", "unit")
            if not unit:
                unit = ""
            self._layer_height_unit = unit

        default_layer_height = active_global_stack.definition.getProperty("layer_height", "value")

        # Get layer_height from the quality profile for the GlobalStack
        container = quality_group.node_for_global.getContainer()

        layer_height = default_layer_height
        if container.hasProperty("layer_height", "value"):
            layer_height = str(container.getProperty("layer_height", "value"))
        else:
            # Look for layer_height in the GlobalStack from material -> definition
            for idx in range(4):
                container = active_global_stack.getContainer(idx)
                if container.hasProperty("layer_height", "value"):
                    layer_height = container.getProperty("layer_height", "value")
                    break
        return str(layer_height)
