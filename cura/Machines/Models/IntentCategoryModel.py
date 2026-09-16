#Copyright (c) 2019 Ultimaker B.V.
#Cura is released under the terms of the LGPLv3 or higher.

from PyQt6.QtCore import Qt, QTimer
from typing import TYPE_CHECKING, Optional, Dict

from cura.Machines.Models.IntentModel import IntentModel
from cura.Machines.Models.IntentTranslations import IntentTranslations
from cura.Settings.IntentManager import IntentManager
from UM.Qt.ListModel import ListModel
from UM.Settings.ContainerRegistry import ContainerRegistry #To update the list if anything changes.
from PyQt6.QtCore import pyqtSignal
import cura.CuraApplication
if TYPE_CHECKING:
    from UM.Settings.ContainerRegistry import ContainerInterface

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


class IntentCategoryModel(ListModel):
    """Lists the intent categories that are available for the current printer configuration. """

    NameRole = Qt.ItemDataRole.UserRole + 1
    IntentCategoryRole = Qt.ItemDataRole.UserRole + 2
    WeightRole = Qt.ItemDataRole.UserRole + 3
    QualitiesRole = Qt.ItemDataRole.UserRole + 4
    DescriptionRole = Qt.ItemDataRole.UserRole + 5

    modelUpdated = pyqtSignal()

    def __init__(self, intent_category: str) -> None:
        """Creates a new model for a certain intent category.

        :param intent_category: category to list the intent profiles for.
        """

        super().__init__()
        self._intent_category = intent_category

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.IntentCategoryRole, "intent_category")
        self.addRoleName(self.WeightRole, "weight")
        self.addRoleName(self.QualitiesRole, "qualities")
        self.addRoleName(self.DescriptionRole, "description")

        application = cura.CuraApplication.CuraApplication.getInstance()

        ContainerRegistry.getInstance().containerAdded.connect(self._onContainerChange)
        ContainerRegistry.getInstance().containerRemoved.connect(self._onContainerChange)
        machine_manager = cura.CuraApplication.CuraApplication.getInstance().getMachineManager()
        machine_manager.activeMaterialChanged.connect(self.update)
        machine_manager.activeVariantChanged.connect(self.update)
        machine_manager.extruderChanged.connect(self.update)

        extruder_manager = application.getExtruderManager()
        extruder_manager.extrudersChanged.connect(self.update)

        self._update_timer = QTimer()
        self._update_timer.setInterval(500)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._update)

        self.update()

    def _onContainerChange(self, container: "ContainerInterface") -> None:
        """Updates the list of intents if an intent profile was added or removed."""

        if container.getMetaDataEntry("type") == "intent":
            self.update()

    def update(self):
        self._update_timer.start()

    def _update(self) -> None:
        """Updates the list of intents."""

        available_categories = IntentManager.getInstance().currentAvailableIntentCategories()
        result = []
        for category in available_categories:
            qualities = IntentModel()
            qualities.setIntentCategory(category)
            try:
                weight = IntentTranslations.getInstance().index(category)
            except ValueError:
                weight = 99
            result.append({
                "name": IntentCategoryModel.translation(category, "name", category.title()),
                "description": IntentCategoryModel.translation(category, "description", None),
                "intent_category": category,
                "weight": weight,
                "qualities": qualities
            })
        result.sort(key = lambda k: k["weight"])
        self.setItems(result)

    @staticmethod
    def translation(category: str, key: str, default: Optional[str] = None):
        """Get a display value for a category.for categories and keys"""

        try:
            return IntentTranslations.getInstance().getTranslation(category)[key]
        except KeyError:
            return default
