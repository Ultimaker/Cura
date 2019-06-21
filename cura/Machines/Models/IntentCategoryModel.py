#Copyright (c) 2019 Ultimaker B.V.
#Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import Qt
import collections

from cura.Settings.IntentManager import IntentManager
from UM.Qt.ListModel import ListModel

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

##  Lists the intent categories that are available for the current printer
#   configuration.
class IntentCategoryModel(ListModel):
    NameRole = Qt.UserRole + 1
    IntentCategoryRole = Qt.UserRole + 2
    WeightRole = Qt.UserRole + 3

    #Translations to user-visible string. Ordered by weight.
    #TODO: Create a solution for this name and weight to be used dynamically.
    name_translation = collections.OrderedDict()
    name_translation["default"] = catalog.i18nc("@label", "Default")
    name_translation["engineering"] = catalog.i18nc("@label", "Engineering")
    name_translation["smooth"] = catalog.i18nc("@label", "Smooth")

    ##  Creates a new model for a certain intent category.
    #   \param The category to list the intent profiles for.
    def __init__(self, intent_category: str):
        super().__init__()
        self._intent_category = intent_category

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.IntentCategoryRole, "intent_category")
        self.addRoleName(self.WeightRole, "weight")

    ##  Updates the list of intents.
    def update(self):
        available_categories = IntentManager.getInstance().currentAvailableIntentCategories()
        result = []
        for category in available_categories:
            result.append({
                "name": self.name_translation.get(category, catalog.i18nc("@label", "Unknown")),
                "intent_category": category,
                "weight": list(self.name_translation.items()).index(category)
            })
        super().update(result)