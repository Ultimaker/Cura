# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.PluginRegistry import PluginRegistry
from cura.API.Interface.Settings import Settings

##  The Interface class serves as a common root for the specific API
#   methods for each interface element.
#
#   Usage:
#       ``from cura.API import CuraAPI
#       api = CuraAPI()
#       api.interface.settings.addContextMenuItem()
#       api.interface.viewport.addOverlay() # Not implemented, just a hypothetical
#       api.interface.toolbar.getToolButtonCount() # Not implemented, just a hypothetical
#       # etc.``

class Interface:

    # For now we use the same API version to be consistent.
    VERSION = PluginRegistry.APIVersion

    # API methods specific to the settings portion of the UI
    settings = Settings()
