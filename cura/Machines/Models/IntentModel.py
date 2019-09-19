# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional, List, Dict, Any

from PyQt5.QtCore import Qt, QObject, pyqtProperty, pyqtSignal

from UM.Qt.ListModel import ListModel
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.SettingFunction import SettingFunction

from cura.Machines.ContainerTree import ContainerTree
from cura.Settings.ExtruderManager import ExtruderManager
from cura.Settings.IntentManager import IntentManager
import cura.CuraApplication


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

        container_tree = ContainerTree.getInstance()
        machine_node = container_tree.machines[global_stack.definition.getId()]

        # We can't just look at the active extruder, since it is possible for only one extruder to have an intent
        # and the other extruders have no intent (eg, default). It is not possible for one extruder to have intent A and
        # the other to have B.
        # So we will use the first extruder that we find that has an intent that is not default as the "active" extruder

        active_extruder = None
        for extruder in global_stack.extruderList:
            if extruder.intent.getMetaDataEntry("intent_category", "default") == "default":
                if active_extruder is None:
                    active_extruder = extruder  # If there is no extruder found and the intent is default, use that.
            else:  # We found an intent, use that extruder as "active"
                active_extruder = extruder

        if not active_extruder:
            return
        active_variant_name = active_extruder.variant.getMetaDataEntry("name")
        active_variant_node = machine_node.variants[active_variant_name]
        active_material_node = active_variant_node.materials[active_extruder.material.getMetaDataEntry("base_file")]

        layer_heights_added = []
        for quality_id, quality_node in active_material_node.qualities.items():
            if quality_node.quality_type not in quality_groups:  # Don't add the empty quality type (or anything else that would crash, defensively).
                continue
            quality_group = quality_groups[quality_node.quality_type]
            layer_height = self._fetchLayerHeight(quality_group)

            for intent_id, intent_node in quality_node.intents.items():
                if intent_node.intent_category != self._intent_category:
                    continue
                layer_heights_added.append(layer_height)
                new_items.append({"name": quality_group.name,
                                  "quality_type": quality_group.quality_type,
                                  "layer_height": layer_height,
                                  "available": quality_group.is_available,
                                  "intent_category": self._intent_category
                                  })

        # Now that we added all intents that we found something for, ensure that we set add ticks (and layer_heights)
        # for all groups that we don't have anything for (and set it to not available)
        for quality_tuple, quality_group in quality_groups.items():
            # Add the intents that are of the correct category
            if quality_tuple[0] != self._intent_category:
                layer_height = self._fetchLayerHeight(quality_group)
                if layer_height not in layer_heights_added:
                    new_items.append({"name": "Unavailable",
                                      "quality_type": "",
                                      "layer_height": layer_height,
                                      "intent_category": self._intent_category,
                                      "available": False})
                    layer_heights_added.append(layer_height)

        new_items = sorted(new_items, key=lambda x: x["layer_height"])
        self.setItems(new_items)

    #TODO: Copied this from QualityProfilesDropdownMenuModel for the moment. This code duplication should be fixed.
    def _fetchLayerHeight(self, quality_group) -> float:
        global_stack = cura.CuraApplication.CuraApplication.getInstance().getMachineManager().activeMachine
        if not self._layer_height_unit:
            unit = global_stack.definition.getProperty("layer_height", "unit")
            if not unit:
                unit = ""
            self._layer_height_unit = unit

        default_layer_height = global_stack.definition.getProperty("layer_height", "value")

        # Get layer_height from the quality profile for the GlobalStack
        if quality_group.node_for_global is None:
            return float(default_layer_height)
        container = quality_group.node_for_global.container

        layer_height = default_layer_height
        if container and container.hasProperty("layer_height", "value"):
            layer_height = container.getProperty("layer_height", "value")
        else:
            # Look for layer_height in the GlobalStack from material -> definition
            container = global_stack.definition
            if container and container.hasProperty("layer_height", "value"):
                layer_height = container.getProperty("layer_height", "value")

        if isinstance(layer_height, SettingFunction):
            layer_height = layer_height(global_stack)

        return float(layer_height)

    def __repr__(self):
        return str(self.items)
