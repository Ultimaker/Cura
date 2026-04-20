# Copyright (c) 2026 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os
from typing import Optional, Dict, List, Tuple

from PyQt6.QtCore import QObject, pyqtProperty, pyqtSlot

from UM.Logger import Logger
from UM.Resources import Resources


class WhatsNewSubPagesModel(QObject):
    """
    This model loads the sub-pages of the what's new screen according to the text/html pages available
    in the resources folder.
    """

    image_formats = [".png", ".jpg", ".jpeg", ".gif", ".svg"]
    text_formats = [".txt", ".htm", ".html"]
    image_key = "image"
    text_key = "text"

    def __init__(self, parent: Optional["QObject"] = None) -> None:
        super().__init__(parent)

        images, max_image = WhatsNewSubPagesModel._collectOrdinalFiles(Resources.Images, WhatsNewSubPagesModel.image_formats)
        texts, max_text = WhatsNewSubPagesModel._collectOrdinalFiles(Resources.Texts, WhatsNewSubPagesModel.text_formats)
        highest = max(max_image, max_text)

        self._subpages: List[Dict[str, Optional[str]]] = []
        for n in range(0, highest + 1):
            self._subpages.append({
                WhatsNewSubPagesModel.image_key: None if n not in images else images[n],
                WhatsNewSubPagesModel.text_key: None if n not in texts else self._loadText(texts[n])
            })
        if len(self._subpages) == 0:
            self._subpages.append({WhatsNewSubPagesModel.text_key: "~ There Is Nothing New Under The Sun ~"})

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
        result = self._getSubpageItem(page, WhatsNewSubPagesModel.image_key)
        return "file:///" + (result if result else Resources.getPath(Resources.Images, "cura-icon.png"))

    @pyqtSlot(int, result = str)
    def getSubpageText(self, page: int) -> str:
        result = self._getSubpageItem(page, WhatsNewSubPagesModel.text_key)
        return result if result else "* * *"
