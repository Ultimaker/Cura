# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QObject
from typing import Any, Dict, Optional

##  Data struct to group several quality changes instance containers together.
#
#   Each group represents one "custom profile" as the user sees it, which
#   contains an instance container for the global stack and one instance
#   container per extruder.
class QualityChangesGroup(QObject):
    def __init__(self, name: str, quality_type: str, intent_category: str, parent = None) -> None:
        super().__init__(parent)
        self.name = name
        self.quality_type = quality_type
        self.intent_category = intent_category
        self.is_available = False
        self.metadata_for_global = {}    # type: Dict[str, Any]
        self.metadata_per_extruder = {}  # type: Dict[int, Dict[str, Any]]

    def __str__(self) -> str:
        return "{class_name}[{name}, available = {is_available}]".format(class_name = self.__class__.__name__, name = self.name, is_available = self.is_available)
