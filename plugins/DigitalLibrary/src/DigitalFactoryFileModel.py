# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import List, Dict, Callable

from PyQt5.QtCore import Qt, pyqtSignal

from UM.Logger import Logger
from UM.Qt.ListModel import ListModel
from .DigitalFactoryFileResponse import DigitalFactoryFileResponse


DIGITAL_FACTORY_DISPLAY_DATETIME_FORMAT = "%d-%m-%Y %H:%M"


class DigitalFactoryFileModel(ListModel):
    FileNameRole = Qt.UserRole + 1
    FileIdRole = Qt.UserRole + 2
    FileSizeRole = Qt.UserRole + 3
    LibraryProjectIdRole = Qt.UserRole + 4
    DownloadUrlRole = Qt.UserRole + 5
    UsernameRole = Qt.UserRole + 6
    UploadedAtRole = Qt.UserRole + 7

    dfFileModelChanged = pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)

        self.addRoleName(self.FileNameRole, "fileName")
        self.addRoleName(self.FileIdRole, "fileId")
        self.addRoleName(self.FileSizeRole, "fileSize")
        self.addRoleName(self.LibraryProjectIdRole, "libraryProjectId")
        self.addRoleName(self.DownloadUrlRole, "downloadUrl")
        self.addRoleName(self.UsernameRole, "username")
        self.addRoleName(self.UploadedAtRole, "uploadedAt")
        
        self._files = []  # type: List[DigitalFactoryFileResponse]
        self._filters = {}  # type: Dict[str, Callable]

    def setFiles(self, df_files_in_project: List[DigitalFactoryFileResponse]) -> None:
        if self._files == df_files_in_project:
            return
        self.clear()
        self._files = df_files_in_project
        self._update()

    def clearFiles(self) -> None:
        self.clear()
        self._files.clear()
        self.dfFileModelChanged.emit()

    def _update(self) -> None:
        filtered_files_list = self.getFilteredFilesList()

        for file in filtered_files_list:
            self.appendItem({
                "fileName" : file.file_name,
                "fileId" : file.file_id,
                "fileSize": file.file_size,
                "libraryProjectId": file.library_project_id,
                "downloadUrl": file.download_url,
                "username": file.username,
                "uploadedAt": file.uploaded_at.strftime(DIGITAL_FACTORY_DISPLAY_DATETIME_FORMAT)
            })

        self.dfFileModelChanged.emit()

    def setFilters(self, filters: Dict[str, Callable]) -> None:
        """
        Sets the filters and updates the files model to contain only the files that meet all of the filters.

        :param filters: The filters to be applied
            example:
            {
                "attribute_name1": function_to_be_applied_on_DigitalFactoryFileResponse_attribute1,
                "attribute_name2": function_to_be_applied_on_DigitalFactoryFileResponse_attribute2
            }
        """
        self.clear()
        self._filters = filters
        self._update()

    def clearFilters(self) -> None:
        """
        Clears all the model filters
        """
        self.setFilters({})

    def getFilteredFilesList(self) -> List[DigitalFactoryFileResponse]:
        """
        Lists the files that meet all the filters specified in the self._filters. This is achieved by applying each
        filter function on the corresponding attribute for all the filters in the self._filters. If all of them are
        true, the file is added to the filtered files list.
        In order for this to work, the self._filters should be in the format:
        {
            "attribute_name": function_to_be_applied_on_the_DigitalFactoryFileResponse_attribute
        }

        :return: The list of files that meet all the specified filters
        """
        if not self._filters:
            return self._files

        filtered_files_list = []
        for file in self._files:
            filter_results = []
            for attribute, filter_func in self._filters.items():
                try:
                    filter_results.append(filter_func(getattr(file, attribute)))
                except AttributeError:
                    Logger.log("w", "Attribute '{}' doesn't exist in objects of type '{}'".format(attribute, type(file)))
            all_filters_met = all(filter_results)
            if all_filters_met:
                filtered_files_list.append(file)

        return filtered_files_list
