# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import os
from typing import TYPE_CHECKING, Optional, List, Dict, Any

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

        self._pages = []  # type: List[Dict[str, Any]]

    # Convenience function to get QUrl path to pages that's located in "resources/qml/WelcomePages".
    def _getBuiltinWelcomePagePath(self, page_filename: str) -> "QUrl":
        from cura.CuraApplication import CuraApplication
        return QUrl.fromLocalFile(Resources.getPath(CuraApplication.ResourceTypes.QmlFiles,
                                                    os.path.join("WelcomePages", page_filename)))

    def initialize(self) -> None:
        # Add default welcome pages
        self._pages.append({"id": "welcome",
                            "page_url": self._getBuiltinWelcomePagePath("WelcomeContent.qml"),
                            })
        self._pages.append({"id": "user_agreement",
                            "page_url": self._getBuiltinWelcomePagePath("UserAgreementContent.qml"),
                            })
        self._pages.append({"id": "whats_new",
                            "page_url": self._getBuiltinWelcomePagePath("WhatsNewContent.qml"),
                            })
        self._pages.append({"id": "data_collections",
                            "page_url": self._getBuiltinWelcomePagePath("DataCollectionsContent.qml"),
                            })
        self._pages.append({"id": "add_network_or_local_printer",
                            "page_url": self._getBuiltinWelcomePagePath("AddNetworkOrLocalPrinterContent.qml"),
                            })
        self._pages.append({"id": "add_printer_by_ip",
                            "page_url": self._getBuiltinWelcomePagePath("AddPrinterByIpContent.qml"),
                            })
        self._pages.append({"id": "machine_actions",
                            "page_url": self._getBuiltinWelcomePagePath("FirstStartMachineActionsContent.qml"),
                            })
        self._pages.append({"id": "cloud",
                            "page_url": self._getBuiltinWelcomePagePath("CloudContent.qml"),
                            })

        self.setItems(self._pages)

    def addPage(self) -> None:
        pass


__all__ = ["WelcomePagesModel"]
