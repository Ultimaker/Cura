# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import List, Optional

from PyQt5.QtCore import Qt, pyqtSignal

from UM.Logger import Logger
from UM.Qt.ListModel import ListModel
from .DigitalFactoryProjectResponse import DigitalFactoryProjectResponse

PROJECT_UPDATED_AT_DATETIME_FORMAT = "%d-%m-%Y"


class DigitalFactoryProjectModel(ListModel):
    DisplayNameRole = Qt.UserRole + 1
    LibraryProjectIdRole = Qt.UserRole + 2
    DescriptionRole = Qt.UserRole + 3
    ThumbnailUrlRole = Qt.UserRole + 5
    UsernameRole = Qt.UserRole + 6
    LastUpdatedRole = Qt.UserRole + 7

    dfProjectModelChanged = pyqtSignal()

    def __init__(self, parent = None) -> None:
        super().__init__(parent)
        self.addRoleName(self.DisplayNameRole, "displayName")
        self.addRoleName(self.LibraryProjectIdRole, "libraryProjectId")
        self.addRoleName(self.DescriptionRole, "description")
        self.addRoleName(self.ThumbnailUrlRole, "thumbnailUrl")
        self.addRoleName(self.UsernameRole, "username")
        self.addRoleName(self.LastUpdatedRole, "lastUpdated")
        self._projects = []  # type: List[DigitalFactoryProjectResponse]

    def setProjects(self, df_projects: List[DigitalFactoryProjectResponse]) -> None:
        if self._projects == df_projects:
            return
        self._items.clear()
        self._projects = df_projects
        # self.sortProjectsBy("display_name")
        self._update(df_projects)

    def extendProjects(self, df_projects: List[DigitalFactoryProjectResponse]) -> None:
        if not df_projects:
            return
        self._projects.extend(df_projects)
        # self.sortProjectsBy("display_name")
        self._update(df_projects)

    def clearProjects(self) -> None:
        self.clear()
        self._projects.clear()
        self.dfProjectModelChanged.emit()

    def _update(self, df_projects: List[DigitalFactoryProjectResponse]) -> None:
        for project in df_projects:
            self.appendItem({
                "displayName" : project.display_name,
                "libraryProjectId" : project.library_project_id,
                "description": project.description,
                "thumbnailUrl": project.thumbnail_url,
                "username": project.username,
                "lastUpdated": project.last_updated.strftime(PROJECT_UPDATED_AT_DATETIME_FORMAT) if project.last_updated else "",
            })
        self.dfProjectModelChanged.emit()
