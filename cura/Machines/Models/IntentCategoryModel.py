#Copyright (c) 2019 Ultimaker B.V.
#Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import Qt
import collections
from typing import TYPE_CHECKING

from cura.Machines.Models.IntentModel import IntentModel
from cura.Settings.IntentManager import IntentManager
from UM.Qt.ListModel import ListModel
from UM.Settings.ContainerRegistry import ContainerRegistry #To update the list if anything changes.
from PyQt5.QtCore import pyqtProperty, pyqtSignal
import cura.CuraApplication
if TYPE_CHECKING:
    from UM.Settings.ContainerRegistry import ContainerInterface

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


##  Lists the intent categories that are available for the current printer
#   configuration.
class IntentCategoryModel(ListModel):
    NameRole = Qt.UserRole + 1
    IntentCategoryRole = Qt.UserRole + 2
    WeightRole = Qt.UserRole + 3
    QualitiesRole = Qt.UserRole + 4

    #Translations to user-visible string. Ordered by weight.
    #TODO: Create a solution for this name and weight to be used dynamically.
    name_translation = collections.OrderedDict() #type: "collections.OrderedDict[str,str]"
    name_translation["default"] = catalog.i18nc("@label", "Default")
    name_translation["engineering"] = catalog.i18nc("@label", "Engineering")
    name_translation["smooth"] = catalog.i18nc("@label", "Smooth")

    modelUpdated = pyqtSignal()

    ##  Creates a new model for a certain intent category.
    #   \param The category to list the intent profiles for.
    def __init__(self, intent_category: str) -> None:
        super().__init__()
        self._intent_category = intent_category

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.IntentCategoryRole, "intent_category")
        self.addRoleName(self.WeightRole, "weight")
        self.addRoleName(self.QualitiesRole, "qualities")

        application = cura.CuraApplication.CuraApplication.getInstance()

        ContainerRegistry.getInstance().containerAdded.connect(self._onContainerChange)
        ContainerRegistry.getInstance().containerRemoved.connect(self._onContainerChange)
        machine_manager = cura.CuraApplication.CuraApplication.getInstance().getMachineManager()
        machine_manager.activeMaterialChanged.connect(self.update)
        machine_manager.activeVariantChanged.connect(self.update)
        machine_manager.extruderChanged.connect(self.update)

        extruder_manager = application.getExtruderManager()
        extruder_manager.extrudersChanged.connect(self.update)

        self.update()

    ##  Updates the list of intents if an intent profile was added or removed.
    def _onContainerChange(self, container: "ContainerInterface") -> None:
        if container.getMetaDataEntry("type") == "intent":
            self.update()

    ##  Updates the list of intents.
    def update(self) -> None:
        available_categories = IntentManager.getInstance().currentAvailableIntentCategories()
        result = []
        for category in available_categories:
            qualities = IntentModel()
            qualities.setIntentCategory(category)
            result.append({
                "name": self.name_translation.get(category, catalog.i18nc("@label", "Unknown")),
                "intent_category": category,
                "weight": list(self.name_translation.keys()).index(category),
                "qualities": qualities
            })
        result.sort(key = lambda k: k["weight"])
        self.setItems(result)
