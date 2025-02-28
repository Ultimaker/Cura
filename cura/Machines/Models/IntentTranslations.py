# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import collections
from typing import Dict, Optional

from UM.i18n import i18nCatalog
from typing import Dict, Optional
catalog = i18nCatalog("cura")


intent_translations = collections.OrderedDict()  # type: collections.OrderedDict[str, Dict[str, Optional[str]]]
intent_translations["default"] = {
    "name": catalog.i18nc("@label", "Balanced"),
    "description": catalog.i18nc("@text",
                                 "The balanced profile is designed to strike a balance between productivity, surface quality, mechanical properties and dimensional accuracy.")
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
intent_translations["annealing"] = {
    "name": catalog.i18nc("@label", "Annealing"),
    "description": catalog.i18nc("@text", "The annealing profile requires post-processing in an oven after the print is finished. This profile retains the dimensional accuracy of the printed part after annealing and improves strength, stiffness, and thermal resistance.")
}
intent_translations["solid"] = {
    "name": catalog.i18nc("@label", "Solid"),
    "description": catalog.i18nc("@text",
                                 "A highly dense and strong part but at a slower print time. Great for functional parts.")
}
