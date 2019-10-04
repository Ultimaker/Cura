# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional, Dict, Any, Set, List

from PyQt5.QtCore import Qt, QObject, pyqtProperty, pyqtSignal

import cura.CuraApplication
from UM.Qt.ListModel import ListModel
from UM.Settings.ContainerRegistry import ContainerRegistry
from cura.Machines.ContainerTree import ContainerTree
from cura.Machines.MaterialNode import MaterialNode
from cura.Machines.Models.MachineModelUtils import fetch_layer_height
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

        machine_manager = cura.CuraApplication.CuraApplication.getInstance().getMachineManager()
        machine_manager.globalContainerChanged.connect(self._update)
        machine_manager.extruderChanged.connect(self._update)  # We also need to update if an extruder gets disabled
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

    def _onChanged(self, container):
        if container.getMetaDataEntry("type") == "intent":
            self._update()

    def _update(self) -> None:
        new_items = []  # type: List[Dict[str, Any]]
        global_stack = cura.CuraApplication.CuraApplication.getInstance().getGlobalContainerStack()
        if not global_stack:
            self.setItems(new_items)
            return
        quality_groups = ContainerTree.getInstance().getCurrentQualityGroups()

        material_nodes = self._get_active_materials()

        layer_heights_added = []

        for material_node in material_nodes:
            intents = self._get_intents_for_material(material_node, quality_groups)
            for intent in intents:
                if intent["layer_height"] not in layer_heights_added:
                    new_items.append(intent)
                    layer_heights_added.append(intent["layer_height"])

        # Now that we added all intents that we found something for, ensure that we set add ticks (and layer_heights)
        # for all groups that we don't have anything for (and set it to not available)
        for quality_tuple, quality_group in quality_groups.items():
            # Add the intents that are of the correct category
            if quality_tuple[0] != self._intent_category:
                layer_height = fetch_layer_height(quality_group)
                if layer_height not in layer_heights_added:
                    new_items.append({"name": "Unavailable",
                                      "quality_type": "",
                                      "layer_height": layer_height,
                                      "intent_category": self._intent_category,
                                      "available": False})
                    layer_heights_added.append(layer_height)

        new_items = sorted(new_items, key=lambda x: x["layer_height"])
        self.setItems(new_items)

    ##  Get the active materials for all extruders. No duplicates will be returned
    def _get_active_materials(self) -> Set[MaterialNode]:
        global_stack = cura.CuraApplication.CuraApplication.getInstance().getGlobalContainerStack()
        container_tree = ContainerTree.getInstance()
        machine_node = container_tree.machines[global_stack.definition.getId()]
        nodes = set()  # type: Set[MaterialNode]

        for extruder in global_stack.extruderList:
            active_variant_name = extruder.variant.getMetaDataEntry("name")
            active_variant_node = machine_node.variants[active_variant_name]
            active_material_node = active_variant_node.materials[extruder.material.getMetaDataEntry("base_file")]
            nodes.add(active_material_node)

        return nodes

    def _get_intents_for_material(self, active_material_node: MaterialNode, quality_groups: Dict[str, QualityGroup]) -> List[Dict[str, Any]]:
        extruder_intents = []  # type: List[Dict[str, Any]]

        for quality_id, quality_node in active_material_node.qualities.items():
            if quality_node.quality_type not in quality_groups:  # Don't add the empty quality type (or anything else that would crash, defensively).
                continue
            quality_group = quality_groups[quality_node.quality_type]
            layer_height = fetch_layer_height(quality_group)

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
