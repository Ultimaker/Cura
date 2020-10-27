import collections
from typing import Dict, Optional

from UM.i18n import i18nCatalog
from typing import Dict, Optional
catalog = i18nCatalog("cura")


intent_translations = collections.OrderedDict()  # type: collections.OrderedDict[str, Dict[str, Optional[str]]]
intent_translations["default"] = {
    "name": catalog.i18nc("@label", "Default")
}
intent_translations["visual"] = {
    "name": catalog.i18nc("@label", "Visual"),
    "description": catalog.i18nc("@text", "The visual profile is designed to print visual prototypes and models with the intent of high visual and surface quality.")
}
intent_translations["engineering"] = {
    "name": catalog.i18nc("@label", "Engineering"),
    "description": catalog.i18nc("@text", "The engineering profile is designed to print functional prototypes and end-use parts with the intent of better accuracy and for closer tolerances.")
}
intent_translations["quick"] = {
    "name": catalog.i18nc("@label", "Draft"),
    "description": catalog.i18nc("@text", "The draft profile is designed to print initial prototypes and concept validation with the intent of significant print time reduction.")
}
intent_translations["no_support"] = {
    "name": catalog.i18nc("@label", "No Support"),
    "description": catalog.i18nc("@text", "This profile is designed to print without support.")
}
intent_translations["metal_support"] = {
    "name": catalog.i18nc("@label", "Metal Support"),
                "description": catalog.i18nc("@text", "This profile is designed to print with breakaway metal support.")
}
intent_translations["evap_support"] = {
    "name": catalog.i18nc("@label", "Evap Support"),
    "description": catalog.i18nc("@text", "This profile is designed to print evaporative support material.")
}

