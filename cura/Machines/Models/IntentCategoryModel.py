#Copyright (c) 2019 Ultimaker B.V.
#Cura is released under the terms of the LGPLv3 or higher.

import collections
from PyQt6.QtCore import Qt, QTimer
from typing import TYPE_CHECKING, Optional, Dict

from cura.Machines.Models.IntentModel import IntentModel
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

    _translations = collections.OrderedDict()  # type: "collections.OrderedDict[str,Dict[str,Optional[str]]]"

    @classmethod
    def _get_translations(cls):
        """Translations to user-visible string. Ordered by weight.

        TODO: Create a solution for this name and weight to be used dynamically.
        """
        if len(cls._translations) == 0:
            cls._translations["default"] = {
                "name": catalog.i18nc("@label", "Balanced"),
                "description": catalog.i18nc("@text",
                                             "The balanced profile is designed to strike a balance between productivity, surface quality, mechanical properties and dimensional accuracy.")
            }
            cls._translations["visual"] = {
                "name": catalog.i18nc("@label", "Visual"),
                "description": catalog.i18nc("@text", "The visual profile is designed to print visual prototypes and models with the intent of high visual and surface quality.")
            }
            cls._translations["engineering"] = {
                "name": catalog.i18nc("@label", "Engineering"),
                "description": catalog.i18nc("@text", "The engineering profile is designed to print functional prototypes and end-use parts with the intent of better accuracy and for closer tolerances.")
            }
            cls._translations["quick"] = {
                "name": catalog.i18nc("@label", "Draft"),
                "description": catalog.i18nc("@text", "The draft profile is designed to print initial prototypes and concept validation with the intent of significant print time reduction.")
            }
            cls._translations["annealing"] = {
                "name": catalog.i18nc("@label", "Annealing"),
                "description": catalog.i18nc("@text",
                                             "The annealing profile requires post-processing in an oven after the print is finished. This profile retains the dimensional accuracy of the printed part after annealing and improves strength, stiffness, and thermal resistance.")

            }
            cls._translations["solid"] = {
                "name": catalog.i18nc("@label", "Solid"),
                "description": catalog.i18nc("@text",
                                             "A highly dense and strong part but at a slower print time. Great for functional parts.")
            }
        return cls._translations

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
                weight = list(IntentCategoryModel._get_translations().keys()).index(category)
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

        display_strings = IntentCategoryModel._get_translations().get(category, {})
        return display_strings.get(key, default)
