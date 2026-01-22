# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Logger import Logger

from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from UM.Application import Application


def getMetaData() -> Dict[str, Any]:
    return {
        "tool": {
            "visible": False
        }
    }


def register(app: "Application") -> Dict[str, Any]:
    try:
        from .NavlibClient import NavlibClient
        client = NavlibClient(app.getController().getScene(), app.getRenderer())

        # Check for Linux-specific initialization failure
        if hasattr(client, "_platform_system") and client._platform_system == "Linux":
            if not hasattr(client, "_linux_spacenav_client") or \
               client._linux_spacenav_client is None or \
               not client._linux_spacenav_client.available:
                Logger.warning("Failed to initialize LinuxSpacenavClient. 3Dconnexion plugin will be disabled on Linux.")
                return {}  # Disable plugin on Linux due to internal init failure

        # If pynavlib failed on non-Linux, it would likely raise an import error or similar,
        # caught by the BaseException below.
        # If on Linux and the above check passed, or on other platforms and NavlibClient init was successful.
        return {"tool": client}

    except BaseException as exception:
        Logger.warning(f"Unable to load or initialize 3Dconnexion client: {exception}")
        return {}
