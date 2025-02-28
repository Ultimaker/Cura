# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import collections
from typing import Optional, Dict, List, cast

from PyQt6.QtCore import QObject, pyqtSlot

from UM.i18n import i18nCatalog
from UM.Resources import Resources
from UM.Version import Version

catalog = i18nCatalog("cura")

#
# This manager provides means to load texts to QML.
#
class TextManager(QObject):

    def __init__(self, parent: Optional["QObject"] = None) -> None:
        super().__init__(parent)

        self._change_log_text = ""

    @pyqtSlot(result=str)
    def getChangeLogText(self) -> str:
        if not self._change_log_text:
            self._change_log_text = self._loadChangeLogText()
        return self._change_log_text

    def _loadChangeLogText(self) -> str:
        # Load change log texts and organize them with a dict
        try:
            file_path = Resources.getPath(Resources.Texts, "change_log.txt")
        except FileNotFoundError as e:
            # I have no idea how / when this happens, but we're getting crash reports about it.
            return catalog.i18nc("@text:window", "The release notes could not be opened.") + "<br>" + str(e)
        change_logs_dict = {}  # type: Dict[Version, Dict[str, List[str]]]
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                open_version = None  # type: Optional[Version]
                open_header = ""  # Initialise to an empty header in case there is no "*" in the first line of the changelog
                for line in f:
                    line = line.replace("\n", "")
                    if "[" in line and "]" in line:
                        line = line.replace("[", "")
                        line = line.replace("]", "")
                        open_version = Version(line)
                        if open_version < Version([0, 0, 1]):  # Something went wrong with parsing, assume non-numerical alternate version that should be on top.
                            open_version = Version([99, 99, 99])
                        if Version([14, 99, 99]) < open_version < Version([16, 0, 0]):  # Bit of a hack: We released the 15.x.x versions before 2.x
                            open_version = Version([0, open_version.getMinor(), open_version.getRevision(), open_version.getPostfixVersion()])
                        open_header = ""
                        change_logs_dict[open_version] = collections.OrderedDict()
                    elif line.startswith("*"):
                        open_header = line.replace("*", "")
                        change_logs_dict[cast(Version, open_version)][open_header] = []
                    elif line != "":
                        if open_header not in change_logs_dict[cast(Version, open_version)]:
                            change_logs_dict[cast(Version, open_version)][open_header] = []
                        change_logs_dict[cast(Version, open_version)][open_header].append(line)
        except EnvironmentError as e:
            return catalog.i18nc("@text:window", "The release notes could not be opened.") + "<br>" + str(e)

        # Format changelog text
        content = ""
        for version in sorted(change_logs_dict.keys(), reverse=True):
            text_version = version
            if version < Version([1, 0, 0]):  # Bit of a hack: We released the 15.x.x versions before 2.x
                text_version = Version([15, version.getMinor(), version.getRevision(), version.getPostfixVersion()])
            if version > Version([99, 0, 0]):  # Leave it out altogether if it was originally a non-numbered version.
                text_version = ""
            content += ("<h1>" + str(text_version) + "</h1><br>") if text_version else ""
            content += ""
            for change in change_logs_dict[version]:
                if str(change) != "":
                    content += "<b>" + str(change) + "</b><br>"
                for line in change_logs_dict[version][change]:
                    content += str(line) + "<br>"
                content += "<br>"

        return content
