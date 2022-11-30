from dataclasses import dataclass
from typing import List

from UM import i18nCatalog

catalog = i18nCatalog("cura")


@dataclass
class ActiveQuality:
    """ Represents the active intent+profile combination, contains all information needed to display active quality. """
    intent_category: str = ""       # Name of the base intent. For example "visual" or "engineering".
    intent_name: str = ""           # Name of the base intent formatted for display. For Example "Visual" or "Engineering"
    profile: str = ""               # Name of the base profile. For example "Fine" or "Fast"
    custom_profile: str = ""        # Name of the custom profile, this is based on profile. For example "MyCoolCustomProfile"
    layer_height: float = None      # Layer height of quality in mm. For example 0.4
    is_experimental: bool = False   # If the quality experimental.

    def getMainStringParts(self) -> List[str]:
        string_parts = []

        if self.custom_profile is not None:
            string_parts.append(self.custom_profile)
        else:
            string_parts.append(self.profile)
            if self.intent_category != "default":
                string_parts.append(self.intent_name)

        return string_parts

    def getTailStringParts(self) -> List[str]:
        string_parts = []

        if self.custom_profile is not None:
            string_parts.append(self.profile)
            if self.intent_category != "default":
                string_parts.append(self.intent_name)

        if self.layer_height:
            string_parts.append(f"{self.layer_height}mm")

        if self.is_experimental:
            string_parts.append(catalog.i18nc("@label", "Experimental"))

        return string_parts

    def getStringParts(self) -> List[str]:
        return self.getMainStringParts() + self.getTailStringParts()
