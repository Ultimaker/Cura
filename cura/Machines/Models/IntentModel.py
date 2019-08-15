# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional, List, Dict, Any

from PyQt5.QtCore import Qt, QObject, pyqtProperty, pyqtSignal

from UM.Qt.ListModel import ListModel
from UM.Settings.ContainerRegistry import ContainerRegistry

from cura.Machines.ContainerTree import ContainerTree
from cura.Settings.IntentManager import IntentManager
import cura.CuraApplication


class IntentModel(ListModel):
    NameRole = Qt.UserRole + 1
    QualityTypeRole = Qt.UserRole + 2

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.QualityTypeRole, "quality_type")

        self._intent_category = "engineering"

        ContainerRegistry.getInstance().containerAdded.connect(self._onChanged)
        ContainerRegistry.getInstance().containerRemoved.connect(self._onChanged)

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
        definition_id = global_stack.definition.getId()
        variant_names = [extruder.variant.getName() for extruder in global_stack.extruders.values()]
        material_bases = [extruder.material.getMetaDataEntry("base_file") for extruder in global_stack.extruders.values()]
        extruder_enabled = [extruder.isEnabled for extruder in global_stack.extruders.values()]
        quality_groups = ContainerTree.getInstance().machines[definition_id].getQualityGroups(variant_names, material_bases, extruder_enabled)

        for intent_category, quality_type in IntentManager.getInstance().getCurrentAvailableIntents():
            if intent_category == self._intent_category:
                new_items.append({"name": quality_groups[quality_type].name, "quality_type": quality_type})
        if self._intent_category == "default": #For Default we always list all quality types. We can't filter on available profiles since the empty intent is not a specific quality type.
            for quality_type in quality_groups.keys():
                new_items.append({"name": quality_groups[quality_type].name, "quality_type": quality_type})

        self.setItems(new_items)
