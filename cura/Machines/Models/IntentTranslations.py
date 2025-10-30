import collections
import warnings
import json
from typing import Dict, Optional

from UM.Decorators import singleton, deprecated
from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.Resources import Resources
from typing import Dict, Optional
catalog = i18nCatalog("cura")


@singleton
class IntentTranslations:
    def __init__(self):
        from cura.CuraApplication import CuraApplication
        intents_definition_path = Resources.getPath(CuraApplication.ResourceTypes.IntentInstanceContainer, "intents.def.json")
        self._intent_translations: collections.OrderedDict[str, Dict[str, str]] = collections.OrderedDict()

        with open(intents_definition_path, "r") as file:
            intents_data = json.load(file)
            for intent_id in intents_data:
                intent_definition = intents_data[intent_id]
                self._intent_translations[intent_id] = {
                    "name": catalog.i18nc("@label", intent_definition["label"]),
                    "description": catalog.i18nc("@text", intent_definition["description"])
                }

    def index(self, intent_id: str) -> int:
        """
        Get the index of the given intent key in the list
        :warning: There is no checking for presence, so this will throw a ValueError if the id is not present
        """
        return list(self._intent_translations.keys()).index(intent_id)

    def getTranslation(self, intent_id: str) -> Dict[str, str]:
        """
        Get the translation of the given intent key
        :return If found, a dictionary containing the name and description of the intent
        :warning: There is no checking for presence, so this will throw a KeyError if the id is not present
        """
        return self._intent_translations[intent_id]

    def getLabel(self, intent_id: str) -> str:
        """
        Get the translated name of the given intent key
        :warning: There is no checking for presence, so this will throw a KeyError if the id is not present
        """
        return self.getTranslation(intent_id)["name"]

    def getDescription(self, intent_id: str) -> str:
        """
        Get the translated description of the given intent key
        :warning: There is no checking for presence, so this will throw a KeyError if the id is not present
        """
        return self.getTranslation(intent_id)["description"]

    @deprecated("This method only exists to provide the old intent_translations list, it should not be used anywhere else", "5.12")
    def getTranslations(self) -> collections.OrderedDict[str, Dict[str, str]]:
        return self._intent_translations


def __getattr__(name):
    if name == "intent_translations":
        warning = ("IntentTranslations.intent_translations is deprecated since 5.12, please use the IntentTranslations "
                   "singleton instead. Note that the intents translations will not work as long as this old behavior "
                   "is used within a plugin")
        Logger.log("w_once", warning)
        warnings.warn(warning, DeprecationWarning, stacklevel=2)

        return IntentTranslations.getInstance().getTranslations()

    return None