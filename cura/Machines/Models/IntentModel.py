# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional, Dict, Any, Set, List

from PyQt5.QtCore import Qt, QObject, pyqtProperty, pyqtSignal, QTimer

import cura.CuraApplication
from UM.Qt.ListModel import ListModel
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Logger import Logger
from cura.Machines.ContainerTree import ContainerTree
from cura.Machines.MaterialNode import MaterialNode
from cura.Machines.Models.MachineModelUtils import fetchLayerHeight
from cura.Machines.QualityGroup import QualityGroup


class IntentModel(ListModel):
    NameRole = Qt.UserRole + 1
    QualityTypeRole = Qt.UserRole + 2
    LayerHeightRole = Qt.UserRole + 3
    AvailableRole = Qt.UserRole + 4
    IntentRole = Qt.UserRole + 5

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.QualityTypeRole, "quality_type")
        self.addRoleName(self.LayerHeightRole, "layer_height")
        self.addRoleName(self.AvailableRole, "available")
        self.addRoleName(self.IntentRole, "intent_category")

        self._intent_category = "engineering"

        self._update_timer = QTimer()
        self._update_timer.setInterval(100)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._update)

        machine_manager = cura.CuraApplication.CuraApplication.getInstance().getMachineManager()
        machine_manager.globalContainerChanged.connect(self._updateDelayed)
        machine_manager.extruderChanged.connect(self._updateDelayed)  # We also need to update if an extruder gets disabled
        ContainerRegistry.getInstance().containerAdded.connect(self._onChanged)
        ContainerRegistry.getInstance().containerRemoved.connect(self._onChanged)
        self._layer_height_unit = ""  # This is cached
        self._update()

    intentCategoryChanged = pyqtSignal()

    def setIntentCategory(self, new_category: str) -> None:
        if self._intent_category != new_category:
            self._intent_category = new_category
            self.intentCategoryChanged.emit()
            self._update()

    @pyqtProperty(str, fset = setIntentCategory, notify = intentCategoryChanged)
    def intentCategory(self) -> str:
        return self._intent_category

    def _updateDelayed(self):
        self._update_timer.start()

    def _onChanged(self, container):
        if container.getMetaDataEntry("type") == "intent":
            self._updateDelayed()

    def _update(self) -> None:
        new_items = []  # type: List[Dict[str, Any]]
        global_stack = cura.CuraApplication.CuraApplication.getInstance().getGlobalContainerStack()
        if not global_stack:
            self.setItems(new_items)
            return
        quality_groups = ContainerTree.getInstance().getCurrentQualityGroups()

        material_nodes = self._getActiveMaterials()

        added_quality_type_set = set()  # type: Set[str]
        for material_node in material_nodes:
            intents = self._getIntentsForMaterial(material_node, quality_groups)
            for intent in intents:
                if intent["quality_type"] not in added_quality_type_set:
                    new_items.append(intent)
                    added_quality_type_set.add(intent["quality_type"])

        # Now that we added all intents that we found something for, ensure that we set add ticks (and layer_heights)
        # for all groups that we don't have anything for (and set it to not available)
        for quality_type, quality_group in quality_groups.items():
            # Add the intents that are of the correct category
            if quality_type not in added_quality_type_set:
                layer_height = fetchLayerHeight(quality_group)
                new_items.append({"name": "Unavailable",
                                  "quality_type": quality_type,
                                  "layer_height": layer_height,
                                  "intent_category": self._intent_category,
                                  "available": False})
                added_quality_type_set.add(quality_type)

        new_items = sorted(new_items, key = lambda x: x["layer_height"])
        self.setItems(new_items)

    ##  Get the active materials for all extruders. No duplicates will be returned
    def _getActiveMaterials(self) -> Set["MaterialNode"]:
        global_stack = cura.CuraApplication.CuraApplication.getInstance().getGlobalContainerStack()
        if global_stack is None:
            return set()

        container_tree = ContainerTree.getInstance()
        machine_node = container_tree.machines[global_stack.definition.getId()]
        nodes = set()  # type: Set[MaterialNode]

        for extruder in global_stack.extruderList:
            active_variant_name = extruder.variant.getMetaDataEntry("name")
            if active_variant_name not in machine_node.variants:
                Logger.log("w", "Could not find the variant %s", active_variant_name)
                continue
            active_variant_node = machine_node.variants[active_variant_name]
            active_material_node = active_variant_node.materials[extruder.material.getMetaDataEntry("base_file")]
            nodes.add(active_material_node)

        return nodes

    def _getIntentsForMaterial(self, active_material_node: "MaterialNode", quality_groups: Dict[str, "QualityGroup"]) -> List[Dict[str, Any]]:
        extruder_intents = []  # type: List[Dict[str, Any]]

        for quality_id, quality_node in active_material_node.qualities.items():
            if quality_node.quality_type not in quality_groups:  # Don't add the empty quality type (or anything else that would crash, defensively).
                continue
            quality_group = quality_groups[quality_node.quality_type]
            layer_height = fetchLayerHeight(quality_group)

            for intent_id, intent_node in quality_node.intents.items():
                if intent_node.intent_category != self._intent_category:
                    continue
                extruder_intents.append({"name": quality_group.name,
                                         "quality_type": quality_group.quality_type,
                                         "layer_height": layer_height,
                                         "available": quality_group.is_available,
                                         "intent_category": self._intent_category
                                         })
        return extruder_intents

    def __repr__(self):
        return str(self.items)
