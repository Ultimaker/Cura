# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from .WelcomePagesModel import WelcomePagesModel


#
# This Qt ListModel is more or less the same the WelcomePagesModel, except that this model is only for showing the
# "what's new" page. This is also used in the "Help" menu to show the changes log.
#
class WhatsNewPagesModel(WelcomePagesModel):

    def initialize(self) -> None:
        self._pages = []
        self._pages.append({"id": "whats_new",
                            "page_url": self._getBuiltinWelcomePagePath("WhatsNewContent.qml"),
                            "next_page_button_text": self._catalog.i18nc("@action:button", "Close"),
                            })
        self.setItems(self._pages)


__all__ = ["WhatsNewPagesModel"]
