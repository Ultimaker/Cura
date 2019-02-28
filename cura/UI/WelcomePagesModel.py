

import os
from typing import TYPE_CHECKING, Optional

from PyQt5.QtCore import QUrl, Qt

from UM.Qt.ListModel import ListModel
from UM.Resources import Resources

if TYPE_CHECKING:
    from PyQt5.QtCore import QObject


class WelcomePagesModel(ListModel):

    IdRole = Qt.UserRole + 1  # Page ID
    PageUrlRole = Qt.UserRole + 2  # URL to the page's QML file
    NextPageIdRole = Qt.UserRole + 3  # The next page ID it should go to

    def __init__(self, parent: Optional["QObject"] = None) -> None:
        super().__init__(parent)

        self.addRoleName(self.IdRole, "id")
        self.addRoleName(self.PageUrlRole, "page_url")
        self.addRoleName(self.NextPageIdRole, "next_page_id")

        self._pages = []

    def initialize(self) -> None:
        from cura.CuraApplication import CuraApplication
        # Add default welcome pages
        self._pages.append({"id": "welcome",
                            "page_url": QUrl.fromLocalFile(Resources.getPath(CuraApplication.ResourceTypes.QmlFiles,
                                                                             os.path.join("WelcomePages",
                                                                                          "WelcomeContent.qml"))),
                            })
        self._pages.append({"id": "user_agreement",
                            "page_url": QUrl.fromLocalFile(Resources.getPath(CuraApplication.ResourceTypes.QmlFiles,
                                                                             os.path.join("WelcomePages",
                                                                                          "UserAgreementContent.qml"))),
                            })
        self._pages.append({"id": "whats_new",
                            "page_url": QUrl.fromLocalFile(Resources.getPath(CuraApplication.ResourceTypes.QmlFiles,
                                                                             os.path.join("WelcomePages",
                                                                                          "WhatsNewContent.qml"))),
                            })
        self._pages.append({"id": "data_collections",
                            "page_url": QUrl.fromLocalFile(Resources.getPath(CuraApplication.ResourceTypes.QmlFiles,
                                                                             os.path.join("WelcomePages",
                                                                                          "DataCollectionsContent.qml"))),
                            })

        self.setItems(self._pages)

    def addPage(self):
        pass


__all__ = ["WelcomePagesModel"]
