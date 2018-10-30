from typing import Optional

from PyQt5.QtCore import QObject



class CuraPackage(QObject):

    def __init__(self, parent: Optional["QObject"] = None) -> None:
        super().__init__(parent = parent)

        self._id = ""
        self._name = ""
        self._type = ""
        self._version = ""
        self._author_id = ""
        self._author_name = ""
        self._author_email = ""
        self._description = ""

        # Remote data
        self._icon_url = ""
        self._image_urls = ""

