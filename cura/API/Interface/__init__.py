# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import TYPE_CHECKING

from cura.API.Interface.Settings import Settings

if TYPE_CHECKING:
    from cura.CuraApplication import CuraApplication


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

    def __init__(self, application: "CuraApplication") -> None:
        # API methods specific to the settings portion of the UI
        self.settings = Settings(application)
