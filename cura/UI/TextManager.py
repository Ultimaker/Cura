# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import collections
from typing import Optional

from PyQt5.QtCore import QObject, pyqtSlot

from UM.Resources import Resources
from UM.Version import Version


#
# This manager provides means to load texts to QML.
#
class TextManager(QObject):

    def __init__(self, parent: Optional["QObject"] = None) -> None:
        super().__init__(parent)

        self._change_log_text = ""

    @pyqtSlot(result = str)
    def getChangeLogText(self) -> str:
        if not self._change_log_text:
            self._change_log_text = self._loadChangeLogText()
        return self._change_log_text

    def _loadChangeLogText(self) -> str:
        # Load change log texts and organize them with a dict
        file_path = Resources.getPath(Resources.Texts, "change_log.txt")
        change_logs_dict = {}
        with open(file_path, "r", encoding = "utf-8") as f:
            open_version = None
            open_header = ""  # Initialise to an empty header in case there is no "*" in the first line of the changelog
            for line in f:
                line = line.replace("\n", "")
                if "[" in line and "]" in line:
                    line = line.replace("[", "")
                    line = line.replace("]", "")
                    open_version = Version(line)
                    open_header = ""
                    change_logs_dict[open_version] = collections.OrderedDict()
                elif line.startswith("*"):
                    open_header = line.replace("*", "")
                    change_logs_dict[open_version][open_header] = []
                elif line != "":
                    if open_header not in change_logs_dict[open_version]:
                        change_logs_dict[open_version][open_header] = []
                    change_logs_dict[open_version][open_header].append(line)

        # Format changelog text
        content = ""
        for version in change_logs_dict:
            content += "<h1>" + str(version) + "</h1><br>"
            content += ""
            for change in change_logs_dict[version]:
                if str(change) != "":
                    content += "<b>" + str(change) + "</b><br>"
                for line in change_logs_dict[version][change]:
                    content += str(line) + "<br>"
                content += "<br>"

        return content
