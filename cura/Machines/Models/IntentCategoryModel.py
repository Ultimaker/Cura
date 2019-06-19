#Copyright (c) 2019 Ultimaker B.V.
#Cura is released under the terms of the LGPLv3 or higher.

from UM.Qt.ListModel import ListModel
from cura.Settings.IntentManager import IntentManager

class IntentCategoryModel(ListModel):
    def __init__(self, intent_category: str):
        self._intent_category = intent_category

    def update(self):
        available_intents = IntentManager.getInstance().currentAvailableIntents()
        result = filter(lambda intent: intent.getMetaDataEntry("intent_category") == self._intent_category, available_intents)
        super().update(result)