# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os
from typing import Optional, TYPE_CHECKING

from PyQt6.QtCore import pyqtProperty, pyqtSlot

from UM.Decorators import deprecated
from UM.Logger import Logger

from cura.UI.WelcomePagesModel import WelcomePagesModel

if TYPE_CHECKING:
    from PyQt6.QtCore import QObject
    from cura.CuraApplication import CuraApplication


class WhatsNewPagesModel(WelcomePagesModel):
    """
    This Qt ListModel is more or less the same the WelcomePagesModel, except that this model is only for showing the
    "what's new" page. This is also used in the "Help" menu to show the changes log.
    """

    @deprecated("Argument 'application' is unused and will be removed", since="5.14.0")
    def __init__(self, application: "CuraApplication" = None, parent: Optional["QObject"] = None) -> None:
        super().__init__(application, parent)
        self.initialize()

    def initialize(self) -> None:
        self._pages = []
        try:
            self._pages.append({"id": "whats_new",
                                "page_url": self._getBuiltinWelcomePagePath("WhatsNewContent.qml"),
                                "next_page_button_text": self._catalog.i18nc("@action:button", "Skip"),
                                "next_page_id": "changelog"
                                })
        except FileNotFoundError:
            Logger.warning("Unable to find what's new page")
        try:
            self._pages.append({"id": "changelog",
                                "page_url": self._getBuiltinWelcomePagePath("ChangelogContent.qml"),
                                "next_page_button_text": self._catalog.i18nc("@action:button", "Close"),
                                })
        except FileNotFoundError:
            Logger.warning("Unable to find changelog page")
        self.setItems(self._pages)
