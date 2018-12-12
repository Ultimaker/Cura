# Copyright (c) 2018 Ultimaker B.V.
from typing import Any, List, Dict

from UM.Qt.ListModel import ListModel

from PyQt5.QtCore import Qt


class BackupListModel(ListModel):
    """
    The BackupListModel transforms the backups data that came from the server so it can be served to the Qt UI.
    """

    def __init__(self, parent = None) -> None:
        super().__init__(parent)
        self.addRoleName(Qt.UserRole + 1, "backup_id")
        self.addRoleName(Qt.UserRole + 2, "download_url")
        self.addRoleName(Qt.UserRole + 3, "generated_time")
        self.addRoleName(Qt.UserRole + 4, "md5_hash")
        self.addRoleName(Qt.UserRole + 5, "data")

    def loadBackups(self, data: List[Dict[str, Any]]) -> None:
        """
        Populate the model with server data.
        :param data:
        """
        items = []
        for backup in data:
            # We do this loop because we only want to append these specific fields.
            # Without this, ListModel will break.
            items.append({
                "backup_id": backup["backup_id"],
                "download_url": backup["download_url"],
                "generated_time": backup["generated_time"],
                "md5_hash": backup["md5_hash"],
                "data": backup["metadata"]
            })
        self.setItems(items)
