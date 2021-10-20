# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import Qt, QTimer

import cura.CuraApplication  # Imported this way to prevent circular dependencies.
from UM.Logger import Logger
from UM.Qt.ListModel import ListModel
from cura.Machines.ContainerTree import ContainerTree
from cura.Machines.Models.MachineModelUtils import fetchLayerHeight


class QualityProfilesDropDownMenuModel(ListModel):
    """QML Model for all built-in quality profiles. This model is used for the drop-down quality menu."""

    NameRole = Qt.UserRole + 1
    QualityTypeRole = Qt.UserRole + 2
    LayerHeightRole = Qt.UserRole + 3
    LayerHeightUnitRole = Qt.UserRole + 4
    AvailableRole = Qt.UserRole + 5
    QualityGroupRole = Qt.UserRole + 6
    QualityChangesGroupRole = Qt.UserRole + 7
    IsExperimentalRole = Qt.UserRole + 8

    def __init__(self, parent = None):
        super().__init__(parent)

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.QualityTypeRole, "quality_type")
        self.addRoleName(self.LayerHeightRole, "layer_height")
        self.addRoleName(self.LayerHeightUnitRole, "layer_height_unit")
        self.addRoleName(self.AvailableRole, "available") #Whether the quality profile is available in our current nozzle + material.
        self.addRoleName(self.QualityGroupRole, "quality_group")
        self.addRoleName(self.QualityChangesGroupRole, "quality_changes_group")
        self.addRoleName(self.IsExperimentalRole, "is_experimental")

        application = cura.CuraApplication.CuraApplication.getInstance()
        machine_manager = application.getMachineManager()

        application.globalContainerStackChanged.connect(self._onChange)
        machine_manager.activeQualityGroupChanged.connect(self._onChange)
        machine_manager.activeMaterialChanged.connect(self._onChange)
        machine_manager.activeVariantChanged.connect(self._onChange)

        self._layer_height_unit = ""  # This is cached

        self._update_timer = QTimer()  # type: QTimer
        self._update_timer.setInterval(100)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._update)

        self._onChange()

    def _onChange(self) -> None:
        self._update_timer.start()

    def _update(self):
        Logger.log("d", "Updating {model_class_name}.".format(model_class_name = self.__class__.__name__))

        # CURA-6836
        # LabelBar is a repeater that creates labels for quality layer heights. Because of an optimization in
        # UM.ListModel, the model will not remove all items and recreate new ones every time there's an update.
        # Because LabelBar uses Repeater with Labels anchoring to "undefined" in certain cases, the anchoring will be
        # kept the same as before.
        self.setItems([])

        global_stack = cura.CuraApplication.CuraApplication.getInstance().getGlobalContainerStack()
        if global_stack is None:
            self.setItems([])
            Logger.log("d", "No active GlobalStack, set quality profile model as empty.")
            return

        if not self._layer_height_unit:
            unit = global_stack.definition.getProperty("layer_height", "unit")
            if not unit:
                unit = ""
            self._layer_height_unit = unit

        # Check for material compatibility
        if not cura.CuraApplication.CuraApplication.getInstance().getMachineManager().activeMaterialsCompatible():
            Logger.log("d", "No active material compatibility, set quality profile model as empty.")
            self.setItems([])
            return

        quality_group_dict = ContainerTree.getInstance().getCurrentQualityGroups()

        item_list = []
        for quality_group in quality_group_dict.values():
            layer_height = fetchLayerHeight(quality_group)

            item = {"name": quality_group.name,
                    "quality_type": quality_group.quality_type,
                    "layer_height": layer_height,
                    "layer_height_unit": self._layer_height_unit,
                    "available": quality_group.is_available,
                    "quality_group": quality_group,
                    "is_experimental": quality_group.is_experimental}

            item_list.append(item)

        # Sort items based on layer_height
        item_list = sorted(item_list, key = lambda x: x["layer_height"])

        self.setItems(item_list)
