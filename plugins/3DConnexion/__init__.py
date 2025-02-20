# Copyright (c) 2025 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Logger import Logger

from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from UM.Application import Application


def getMetaData() -> Dict[str, Any]:
    return {}


def register(app: "Application") -> Dict[str, Any]:
    try:
        from .NavlibClient import NavlibClient
        return { "view_manipulator": NavlibClient(app.getController().getScene(), app.getRenderer()) }
    except BaseException as exception:
        Logger.warning(f"Unable to load 3DConnexion library: {exception}")
        return { }
