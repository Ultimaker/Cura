# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os
from typing import Optional, Dict, List, Tuple, TYPE_CHECKING

from PyQt6.QtCore import pyqtProperty, pyqtSlot

from UM.Logger import Logger
from UM.Resources import Resources

from cura.UI.WelcomePagesModel import WelcomePagesModel

if TYPE_CHECKING:
    from PyQt6.QtCore import QObject
    from cura.CuraApplication import CuraApplication


class WhatsNewPagesModel(WelcomePagesModel):
    """
    This Qt ListModel is more or less the same the WelcomePagesModel, except that this model is only for showing the
    "what's new" page. This is also used in the "Help" menu to show the changes log.
    """

    image_formats = [".png", ".jpg", ".jpeg", ".gif", ".svg"]
    text_formats = [".txt", ".htm", ".html"]
    image_key = "image"
    text_key = "text"

    def __init__(self, application: "CuraApplication", parent: Optional["QObject"] = None) -> None:
        super().__init__(application, parent)
        self._subpages: List[Dict[str, Optional[str]]] = []

    @staticmethod
    def _collectOrdinalFiles(resource_type: int, include: List[str]) -> Tuple[Dict[int, str], int]:
        result = {}  # type: Dict[int, str]
        highest = -1
        try:
            folder_path = Resources.getPath(resource_type, "whats_new")
            for _, _, files in os.walk(folder_path):
                for filename in files:
                    basename = os.path.basename(filename)
                    base, ext = os.path.splitext(basename)
                    if ext.lower() not in include or not base.isdigit():
                        continue
                    page_no = int(base)
                    highest = max(highest, page_no)
                    result[page_no] = os.path.join(folder_path, filename)
        except FileNotFoundError:
            Logger.logException("w", "Could not find 'whats_new' folder for resource-type {0}".format(resource_type))
        return result, highest

    @staticmethod
    def _loadText(filename: str) -> str:
        result = ""
        try:
            with open(filename, "r", encoding="utf-8") as file:
                result = file.read()
        except OSError:
            Logger.logException("w", "Could not open {0}".format(filename))
        return result

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

        images, max_image = WhatsNewPagesModel._collectOrdinalFiles(Resources.Images, WhatsNewPagesModel.image_formats)
        texts, max_text = WhatsNewPagesModel._collectOrdinalFiles(Resources.Texts, WhatsNewPagesModel.text_formats)
        highest = max(max_image, max_text)

        self._subpages = []
        for n in range(0, highest + 1):
            self._subpages.append({
                WhatsNewPagesModel.image_key: None if n not in images else images[n],
                WhatsNewPagesModel.text_key: None if n not in texts else self._loadText(texts[n])
            })
        if len(self._subpages) == 0:
            self._subpages.append({WhatsNewPagesModel.text_key: "~ There Is Nothing New Under The Sun ~"})

    def _getSubpageItem(self, page: int, item: str) -> Optional[str]:
        if 0 <= page < self.subpageCount and item in self._subpages[page]:
            return self._subpages[page][item]
        else:
            return None

    @pyqtProperty(int, constant = True)
    def subpageCount(self) -> int:
        return len(self._subpages)

    @pyqtSlot(int, result = str)
    def getSubpageImageSource(self, page: int) -> str:
        result = self._getSubpageItem(page, WhatsNewPagesModel.image_key)
        return "file:///" + (result if result else Resources.getPath(Resources.Images, "cura-icon.png"))

    @pyqtSlot(int, result = str)
    def getSubpageText(self, page: int) -> str:
        result = self._getSubpageItem(page, WhatsNewPagesModel.text_key)
        return result if result else "* * *"
