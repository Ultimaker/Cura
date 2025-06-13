# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional, Set, Dict, List, Any

from PyQt6.QtCore import Qt, QObject, QTimer

import cura.CuraApplication
from UM.Logger import Logger
from UM.Qt.ListModel import ListModel
from UM.Settings.ContainerStack import ContainerStack
from cura.Machines.ContainerTree import ContainerTree
from cura.Machines.Models.MachineModelUtils import fetchLayerHeight
from cura.Machines.MaterialNode import MaterialNode
from cura.Machines.QualityGroup import QualityGroup
from cura.Settings.IntentManager import IntentManager


class ActiveIntentQualitiesModel(ListModel):
    NameRole = Qt.ItemDataRole.UserRole + 1
    DisplayTextRole = Qt.ItemDataRole.UserRole + 2
    QualityTypeRole = Qt.ItemDataRole.UserRole + 3
    LayerHeightRole = Qt.ItemDataRole.UserRole + 4
    IntentCategeoryRole = Qt.ItemDataRole.UserRole + 5

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.QualityTypeRole, "quality_type")
        self.addRoleName(self.LayerHeightRole, "layer_height")
        self.addRoleName(self.DisplayTextRole, "display_text")
        self.addRoleName(self.IntentCategeoryRole, "intent_category")

        self._intent_category = ""

        IntentManager.intentCategoryChangedSignal.connect(self._update)
        machine_manager = cura.CuraApplication.CuraApplication.getInstance().getMachineManager()
        machine_manager.activeQualityGroupChanged.connect(self._update)
        machine_manager.globalContainerChanged.connect(self._updateDelayed)
        machine_manager.extruderChanged.connect(self._updateDelayed)  # We also need to update if an extruder gets disabled

        self._update_timer = QTimer()
        self._update_timer.setInterval(100)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._update)

        self._update()

    def _updateDelayed(self):
        self._update_timer.start()

    def _onChanged(self, container: ContainerStack) -> None:
        if container.getMetaDataEntry("type") == "intent":
            self._updateDelayed()

    def _update(self):
        active_extruder_stack = cura.CuraApplication.CuraApplication.getInstance().getMachineManager().activeStack
        if active_extruder_stack:
            self._intent_category = active_extruder_stack.intent.getMetaDataEntry("intent_category", "")

        new_items: List[Dict[str, Any]] = []
        global_stack = cura.CuraApplication.CuraApplication.getInstance().getGlobalContainerStack()
        if not global_stack:
            self.setItems(new_items)
            return
        quality_groups = ContainerTree.getInstance().getCurrentQualityGroups()

        material_nodes = self._getActiveMaterials()

        added_quality_type_set: Set[str] = set()
        for material_node in material_nodes:
            intents = self._getIntentsForMaterial(material_node, quality_groups)
            for intent in intents:
                if intent["quality_type"] not in added_quality_type_set:
                    new_items.append(intent)
                    added_quality_type_set.add(intent["quality_type"])

        new_items = sorted(new_items, key=lambda x: x["layer_height"])
        self.setItems(new_items)

    def _getActiveMaterials(self) -> Set["MaterialNode"]:
        """Get the active materials for all extruders. No duplicates will be returned"""

        global_stack = cura.CuraApplication.CuraApplication.getInstance().getGlobalContainerStack()
        if global_stack is None:
            return set()

        container_tree = ContainerTree.getInstance()
        machine_node = container_tree.machines[global_stack.definition.getId()]
        nodes: Set[MaterialNode] = set()

        for extruder in global_stack.extruderList:
            active_variant_name = extruder.variant.getMetaDataEntry("name")
            if active_variant_name not in machine_node.variants:
                Logger.log("w", "Could not find the variant %s", active_variant_name)
                continue
            active_variant_node = machine_node.variants[active_variant_name]
            active_material_node = active_variant_node.materials.get(extruder.material.getMetaDataEntry("base_file"))
            if active_material_node is None:
                Logger.log("w", "Could not find the material %s", extruder.material.getMetaDataEntry("base_file"))
                continue
            nodes.add(active_material_node)

        return nodes

    def _getIntentsForMaterial(self, active_material_node: "MaterialNode", quality_groups: Dict[str, "QualityGroup"]) -> List[Dict[str, Any]]:
        extruder_intents: List[Dict[str, Any]] = []

        for quality_id, quality_node in active_material_node.qualities.items():
            if quality_node.quality_type not in quality_groups:  # Don't add the empty quality type (or anything else that would crash, defensively).
                continue
            quality_group = quality_groups[quality_node.quality_type]

            if not quality_group.is_available:
                continue

            layer_height = fetchLayerHeight(quality_group)

            for intent_id, intent_node in quality_node.intents.items():
                if intent_node.intent_category != self._intent_category:
                    continue

                extruder_intents.append({"name": quality_group.name,
                                         "display_text": f"<b>{quality_group.name}</b> - {layer_height}mm",
                                         "quality_type": quality_group.quality_type,
                                         "layer_height": layer_height,
                                         "intent_category": self._intent_category
                                         })
        return extruder_intents


