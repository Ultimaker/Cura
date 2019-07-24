# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional, List, Dict, Any

from PyQt5.QtCore import Qt, QObject, pyqtProperty, pyqtSignal

from UM.Qt.ListModel import ListModel
from UM.Settings.ContainerRegistry import ContainerRegistry

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
        application = cura.CuraApplication.CuraApplication.getInstance()
        intent_manager = application.getIntentManager()
        global_stack = application.getGlobalContainerStack()
        if not global_stack:
            self.setItems(new_items)
            return
        quality_groups = intent_manager.getQualityGroups(global_stack)

        for quality_tuple, quality_group in quality_groups.items():
            new_items.append({"name": quality_group.name, "intent_category": quality_tuple[0], "quality_type": quality_tuple[1]})

        self.setItems(new_items)
