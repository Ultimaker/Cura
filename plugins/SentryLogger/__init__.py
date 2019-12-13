# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import TYPE_CHECKING, Dict, Any

from . import SentryLogger

if TYPE_CHECKING:
    from UM.Application import Application


def getMetaData() -> Dict[str, Any]:
    return {}


def register(app: "Application") -> Dict[str, Any]:
    return {"logger": SentryLogger.SentryLogger()}
