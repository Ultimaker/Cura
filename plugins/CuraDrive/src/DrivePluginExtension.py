# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os
from datetime import datetime
from typing import Any, cast, Dict, List, Optional

from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal

from UM.Extension import Extension
from UM.Logger import Logger
from UM.Message import Message
from cura.CuraApplication import CuraApplication

from .Settings import Settings
from .DriveApiService import DriveApiService

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


# The DivePluginExtension provides functionality to backup and restore your Cura configuration to Ultimaker's cloud.
class DrivePluginExtension(QObject, Extension):

    # Signal emitted when the list of backups changed.
    backupsChanged = pyqtSignal()

    # Signal emitted when restoring has started. Needed to prevent parallel restoring.
    restoringStateChanged = pyqtSignal()

    # Signal emitted when creating has started. Needed to prevent parallel creation of backups.
    creatingStateChanged = pyqtSignal()

    # Signal emitted when preferences changed (like auto-backup).
    preferencesChanged = pyqtSignal()

    DATE_FORMAT = "%d/%m/%Y %H:%M:%S"

    def __init__(self) -> None:
        QObject.__init__(self, None)
        Extension.__init__(self)

        # Local data caching for the UI.
        self._drive_window = None  # type: Optional[QObject]
        self._backups = []  # type: List[Dict[str, Any]]
        self._is_restoring_backup = False
        self._is_creating_backup = False

        # Initialize services.
        preferences = CuraApplication.getInstance().getPreferences()
        self._drive_api_service = DriveApiService()

        # Attach signals.
        CuraApplication.getInstance().getCuraAPI().account.loginStateChanged.connect(self._onLoginStateChanged)
        self._drive_api_service.restoringStateChanged.connect(self._onRestoringStateChanged)
        self._drive_api_service.creatingStateChanged.connect(self._onCreatingStateChanged)

        # Register preferences.
        preferences.addPreference(Settings.AUTO_BACKUP_ENABLED_PREFERENCE_KEY, False)
        preferences.addPreference(Settings.AUTO_BACKUP_LAST_DATE_PREFERENCE_KEY,
                                  datetime.now().strftime(self.DATE_FORMAT))

        # Register the menu item
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Manage backups"), self.showDriveWindow)

        # Make auto-backup on boot if required.
        CuraApplication.getInstance().engineCreatedSignal.connect(self._autoBackup)

    def showDriveWindow(self) -> None:
        if not self._drive_window:
            plugin_dir_path = cast(str, CuraApplication.getInstance().getPluginRegistry().getPluginPath(self.getPluginId())) # We know this plug-in exists because that's us, so this always returns str.
            path = os.path.join(plugin_dir_path, "src", "qml", "main.qml")
            self._drive_window = CuraApplication.getInstance().createQmlComponent(path, {"CuraDrive": self})
        self.refreshBackups()
        if self._drive_window:
            self._drive_window.show()

    def _autoBackup(self) -> None:
        preferences = CuraApplication.getInstance().getPreferences()
        if preferences.getValue(Settings.AUTO_BACKUP_ENABLED_PREFERENCE_KEY) and self._isLastBackupTooLongAgo():
            self.createBackup()

    def _isLastBackupTooLongAgo(self) -> bool:
        current_date = datetime.now()
        last_backup_date = self._getLastBackupDate()
        date_diff = current_date - last_backup_date
        return date_diff.days > 1

    def _getLastBackupDate(self) -> "datetime":
        preferences = CuraApplication.getInstance().getPreferences()
        last_backup_date = preferences.getValue(Settings.AUTO_BACKUP_LAST_DATE_PREFERENCE_KEY)
        return datetime.strptime(last_backup_date, self.DATE_FORMAT)

    def _storeBackupDate(self) -> None:
        backup_date = datetime.now().strftime(self.DATE_FORMAT)
        preferences = CuraApplication.getInstance().getPreferences()
        preferences.setValue(Settings.AUTO_BACKUP_LAST_DATE_PREFERENCE_KEY, backup_date)

    def _onLoginStateChanged(self, logged_in: bool = False) -> None:
        if logged_in:
            self.refreshBackups()

    def _onRestoringStateChanged(self, is_restoring: bool = False, error_message: str = None) -> None:
        self._is_restoring_backup = is_restoring
        self.restoringStateChanged.emit()
        if error_message:
            Message(error_message, title = catalog.i18nc("@info:title", "Backup")).show()

    def _onCreatingStateChanged(self, is_creating: bool = False, error_message: str = None) -> None:
        self._is_creating_backup = is_creating
        self.creatingStateChanged.emit()
        if error_message:
            Message(error_message, title = catalog.i18nc("@info:title", "Backup")).show()
        else:
            self._storeBackupDate()
        if not is_creating and not error_message:
            # We've finished creating a new backup, to the list has to be updated.
            self.refreshBackups()

    @pyqtSlot(bool, name = "toggleAutoBackup")
    def toggleAutoBackup(self, enabled: bool) -> None:
        preferences = CuraApplication.getInstance().getPreferences()
        preferences.setValue(Settings.AUTO_BACKUP_ENABLED_PREFERENCE_KEY, enabled)

    @pyqtProperty(bool, notify = preferencesChanged)
    def autoBackupEnabled(self) -> bool:
        preferences = CuraApplication.getInstance().getPreferences()
        return bool(preferences.getValue(Settings.AUTO_BACKUP_ENABLED_PREFERENCE_KEY))

    @pyqtProperty("QVariantList", notify = backupsChanged)
    def backups(self) -> List[Dict[str, Any]]:
        return self._backups

    @pyqtSlot(name = "refreshBackups")
    def refreshBackups(self) -> None:
        self._drive_api_service.getBackups(self._backupsChangedCallback)

    def _backupsChangedCallback(self, backups):
        self._backups = backups
        self.backupsChanged.emit()

    @pyqtProperty(bool, notify = restoringStateChanged)
    def isRestoringBackup(self) -> bool:
        return self._is_restoring_backup

    @pyqtProperty(bool, notify = creatingStateChanged)
    def isCreatingBackup(self) -> bool:
        return self._is_creating_backup

    @pyqtSlot(str, name = "restoreBackup")
    def restoreBackup(self, backup_id: str) -> None:
        for backup in self._backups:
            if backup.get("backup_id") == backup_id:
                self._drive_api_service.restoreBackup(backup)
                return
        Logger.log("w", "Unable to find backup with the ID %s", backup_id)

    @pyqtSlot(name = "createBackup")
    def createBackup(self) -> None:
        self._drive_api_service.createBackup()

    @pyqtSlot(str, name = "deleteBackup")
    def deleteBackup(self, backup_id: str) -> None:
        self._drive_api_service.deleteBackup(backup_id)
        self.refreshBackups()
