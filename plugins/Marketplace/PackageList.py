# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, Qt
from typing import TYPE_CHECKING

from UM.i18n import i18nCatalog
from UM.Qt.ListModel import ListModel

if TYPE_CHECKING:
    from PyQt5.QtCore import QObject

catalog = i18nCatalog("cura")


class PackageList(ListModel):
    PackageRole = Qt.UserRole + 1

    def __init__(self, parent: "QObject" = None) -> None:
        super().__init__(parent)
        self._error_message = ""
        self.addRoleName(self.PackageRole, "package")
        self._is_loading = False
        self._has_more = False

    @pyqtSlot()
    def updatePackages(self) -> None:
        """
        Initialize the first page of packages
        """
        self.setErrorMessage("")  # Clear any previous errors.
        self.isLoadingChanged.emit()

    @pyqtSlot()
    def abortUpdating(self) -> None:
        pass

    def reset(self) -> None:
        self.clear()

    isLoadingChanged = pyqtSignal()

    def setIsLoading(self, value: bool) -> None:
        if self._is_loading != value:
            self._is_loading = value
            self.isLoadingChanged.emit()

    @pyqtProperty(bool, fset = setIsLoading, notify = isLoadingChanged)
    def isLoading(self) -> bool:
        """
        Gives whether the list is currently loading the first page or loading more pages.
        :return: ``True`` if the list is being gathered, or ``False`` if .
        """
        return self._is_loading

    hasMoreChanged = pyqtSignal()

    def setHasMore(self, value: bool) -> None:
        if self._has_more != value:
            self._has_more = value
            self.hasMoreChanged.emit()

    @pyqtProperty(bool, fset = setHasMore, notify = hasMoreChanged)
    def hasMore(self) -> bool:
        """
        Returns whether there are more packages to load.
        :return: ``True`` if there are more packages to load, or ``False`` if we've reached the last page of the
        pagination.
        """
        return self._has_more

    def setErrorMessage(self, error_message: str) -> None:
        if self._error_message != error_message:
            self._error_message = error_message
            self.errorMessageChanged.emit()

    errorMessageChanged = pyqtSignal()

    @pyqtProperty(str, notify = errorMessageChanged, fset = setErrorMessage)
    def errorMessage(self) -> str:
        """
        If an error occurred getting the list of packages, an error message will be held here.

        If no error occurred (yet), this will be an empty string.
        :return: An error message, if any, or an empty string if everything went okay.
        """
        return self._error_message
