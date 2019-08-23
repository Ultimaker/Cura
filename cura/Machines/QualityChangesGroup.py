# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from .QualityGroup import QualityGroup

class QualityChangesGroup(QualityGroup):
    def __init__(self, name: str, quality_type: str, intent_category: str, parent = None) -> None:
        super().__init__(name, quality_type, parent)
        self.intent_category = intent_category

    def __str__(self) -> str:
        return "%s[<%s>, available = %s]" % (self.__class__.__name__, self.name, self.is_available)
