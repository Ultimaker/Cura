# Copyright (c) 2023 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

import collections
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, QObject, QUrl

import cura
from UM import i18nCatalog
from UM.Logger import Logger
from UM.Qt.ListModel import ListModel
from UM.Resources import Resources
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.Interfaces import ContainerInterface

from cura.Machines.Models.IntentCategoryModel import IntentCategoryModel
from cura.Settings.IntentManager import IntentManager

catalog = i18nCatalog("cura")


class IntentSelectionModel(ListModel):
    NameRole = Qt.ItemDataRole.UserRole + 1
    IntentCategoryRole = Qt.ItemDataRole.UserRole + 2
    WeightRole = Qt.ItemDataRole.UserRole + 3
    DescriptionRole = Qt.ItemDataRole.UserRole + 4
    IconRole = Qt.ItemDataRole.UserRole + 5
    CustomIconRole = Qt.ItemDataRole.UserRole + 6

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.IntentCategoryRole, "intent_category")
        self.addRoleName(self.WeightRole, "weight")
        self.addRoleName(self.DescriptionRole, "description")
        self.addRoleName(self.IconRole, "icon")
        self.addRoleName(self.CustomIconRole, "custom_icon")

        application = cura.CuraApplication.CuraApplication.getInstance()

        ContainerRegistry.getInstance().containerAdded.connect(self._onContainerChange)
        ContainerRegistry.getInstance().containerRemoved.connect(self._onContainerChange)
        machine_manager = cura.CuraApplication.CuraApplication.getInstance().getMachineManager()
        machine_manager.activeMaterialChanged.connect(self._update)
        machine_manager.activeVariantChanged.connect(self._update)
        machine_manager.extruderChanged.connect(self._update)

        extruder_manager = application.getExtruderManager()
        extruder_manager.extrudersChanged.connect(self._update)

        self._update_timer: QTimer = QTimer()
        self._update_timer.setInterval(100)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._update)

        self._onChange()

    _default_intent_categories = ["default", "visual", "engineering", "quick", "annealing", "solid"]
    _icons = {"default": "GearCheck", "visual": "Visual", "engineering": "Nut", "quick": "SpeedOMeter",
              "annealing": "Anneal", "solid": "Hammer"}

    def _onContainerChange(self, container: ContainerInterface) -> None:
        """Updates the list of intents if an intent profile was added or removed."""

        if container.getMetaDataEntry("type") == "intent":
            self._update()

    def _onChange(self) -> None:
        self._update_timer.start()

    def _update(self) -> None:
        Logger.log("d", "Updating {model_class_name}.".format(model_class_name = self.__class__.__name__))
        cura_application = cura.CuraApplication.CuraApplication.getInstance()
        global_stack = cura_application.getGlobalContainerStack()
        if global_stack is None:
            self.setItems([])
            Logger.log("d", "No active GlobalStack, set quality profile model as empty.")
            return

        # Check for material compatibility
        if not cura_application.getMachineManager().activeMaterialsCompatible():
            Logger.log("d", "No active material compatibility, set quality profile model as empty.")
            self.setItems([])
            return

        available_categories = IntentManager.getInstance().currentAvailableIntentCategories()

        result = []
        for category in available_categories:

            if category in self._default_intent_categories:
                result.append({
                    "name": IntentCategoryModel.translation(category, "name", category.title()),
                    "description": IntentCategoryModel.translation(category, "description", None),
                    "icon": self._icons[category],
                    "custom_icon": None,
                    "intent_category": category,
                    "weight": self._default_intent_categories.index(category),
                })
            else:
                # There can be multiple intents with the same category, use one of these
                # intent-metadata's for the icon/description defintions for the intent



                intent_metadata = cura_application.getContainerRegistry().findContainersMetadata(type="intent",
                                                                                                 definition=global_stack.findInstanceContainerDefinitionId(global_stack.definition),
                                                                                                 intent_category=category)[0]

                intent_name = intent_metadata.get("name", category.title())
                icon = intent_metadata.get("icon", None)
                description = intent_metadata.get("description", None)

                if icon is not None and icon != '':
                    try:
                        icon = QUrl.fromLocalFile(
                            Resources.getPath(cura.CuraApplication.CuraApplication.ResourceTypes.ImageFiles, icon))
                    except (FileNotFoundError, NotADirectoryError, PermissionError):
                        Logger.log("e", f"Icon file for intent {intent_name} not found.")
                        icon = None

                result.append({
                    "name": intent_name,
                    "description": description,
                    "custom_icon": icon,
                    "icon": None,
                    "intent_category": category,
                    "weight": 5,
                })

        result.sort(key=lambda k: k["weight"])

        self.setItems(result)


