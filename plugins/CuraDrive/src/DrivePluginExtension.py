# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os
from datetime import datetime
from typing import Optional

from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal

from UM.Application import Application
from UM.Extension import Extension
from UM.Message import Message
from cura.CuraApplication import CuraApplication

from .Settings import Settings
from .DriveApiService import DriveApiService
from .models.BackupListModel import BackupListModel


class DrivePluginExtension(QObject, Extension):
    """
    The DivePluginExtension provides functionality to backup and restore your Cura configuration to Ultimaker's cloud.
    """

    # Signal emitted when the list of backups changed.
    backupsChanged = pyqtSignal()

    # Signal emitted when restoring has started. Needed to prevent parallel restoring.
    restoringStateChanged = pyqtSignal()

    # Signal emitted when creating has started. Needed to prevent parallel creation of backups.
    creatingStateChanged = pyqtSignal()

    # Signal emitted when preferences changed (like auto-backup).
    preferencesChanged = pyqtSignal()
    
    DATE_FORMAT = "%d/%m/%Y %H:%M:%S"

    def __init__(self):
        super(DrivePluginExtension, self).__init__()

        # Local data caching for the UI.
        self._drive_window = None  # type: Optional[QObject]
        self._backups_list_model = BackupListModel()
        self._is_restoring_backup = False
        self._is_creating_backup = False

        # Initialize services.
        self._preferences = CuraApplication.getInstance().getPreferences()
        self._drive_api_service = DriveApiService()

        # Attach signals.
        CuraApplication.getInstance().getCuraAPI().account.loginStateChanged.connect(self._onLoginStateChanged)
        self._drive_api_service.onRestoringStateChanged.connect(self._onRestoringStateChanged)
        self._drive_api_service.onCreatingStateChanged.connect(self._onCreatingStateChanged)

        # Register preferences.
        self._preferences.addPreference(Settings.AUTO_BACKUP_ENABLED_PREFERENCE_KEY, False)
        self._preferences.addPreference(Settings.AUTO_BACKUP_LAST_DATE_PREFERENCE_KEY, datetime.now()
                                        .strftime(self.DATE_FORMAT))
        
        # Register menu items.
        self._updateMenuItems()

        # Make auto-backup on boot if required.
        CuraApplication.getInstance().engineCreatedSignal.connect(self._autoBackup)

    def showDriveWindow(self) -> None:
        """Show the Drive UI popup window."""
        if not self._drive_window:
            self._drive_window = self.createDriveWindow()
        self.refreshBackups()
        if self._drive_window:
            self._drive_window.show()

    def createDriveWindow(self) -> Optional["QObject"]:
        """
        Create an instance of the Drive UI popup window.
        :return: The popup window object.
        """
        path = os.path.join(os.path.dirname(__file__), "qml", "main.qml")
        return CuraApplication.getInstance().createQmlComponent(path, {"CuraDrive": self})
    
    def _updateMenuItems(self) -> None:
        """Update the menu items."""
        self.addMenuItem(Settings.translatable_messages["extension_menu_entry"], self.showDriveWindow)

    def _autoBackup(self) -> None:
        """Automatically make a backup on boot if enabled."""
        if self._preferences.getValue(Settings.AUTO_BACKUP_ENABLED_PREFERENCE_KEY) and self._lastBackupTooLongAgo():
            self.createBackup()
            
    def _lastBackupTooLongAgo(self) -> bool:
        """Check if the last backup was longer than 1 day ago."""
        current_date = datetime.now()
        last_backup_date = self._getLastBackupDate()
        date_diff = current_date - last_backup_date
        return date_diff.days > 1

    def _getLastBackupDate(self) -> "datetime":
        """Get the last backup date as datetime object."""
        last_backup_date = self._preferences.getValue(Settings.AUTO_BACKUP_LAST_DATE_PREFERENCE_KEY)
        return datetime.strptime(last_backup_date, self.DATE_FORMAT)

    def _storeBackupDate(self) -> None:
        """Store the current date as last backup date."""
        backup_date = datetime.now().strftime(self.DATE_FORMAT)
        self._preferences.setValue(Settings.AUTO_BACKUP_LAST_DATE_PREFERENCE_KEY, backup_date)

    def _onLoginStateChanged(self, logged_in: bool = False) -> None:
        """Callback handler for changes in the login state."""
        if logged_in:
            self.refreshBackups()

    def _onRestoringStateChanged(self, is_restoring: bool = False, error_message: str = None) -> None:
        """Callback handler for changes in the restoring state."""
        self._is_restoring_backup = is_restoring
        self.restoringStateChanged.emit()
        if error_message:
            Message(error_message, title = Settings.MESSAGE_TITLE, lifetime = 5).show()

    def _onCreatingStateChanged(self, is_creating: bool = False, error_message: str = None) -> None:
        """Callback handler for changes in the creation state."""
        self._is_creating_backup = is_creating
        self.creatingStateChanged.emit()
        if error_message:
            Message(error_message, title = Settings.MESSAGE_TITLE, lifetime = 5).show()
        else:
            self._storeBackupDate()
        if not is_creating:
            # We've finished creating a new backup, to the list has to be updated.
            self.refreshBackups()

    @pyqtSlot(bool, name = "toggleAutoBackup")
    def toggleAutoBackup(self, enabled: bool) -> None:
        """Enable or disable the auto-backup feature."""
        self._preferences.setValue(Settings.AUTO_BACKUP_ENABLED_PREFERENCE_KEY, enabled)
        self.preferencesChanged.emit()

    @pyqtProperty(bool, notify = preferencesChanged)
    def autoBackupEnabled(self) -> bool:
        """Check if auto-backup is enabled or not."""
        return bool(self._preferences.getValue(Settings.AUTO_BACKUP_ENABLED_PREFERENCE_KEY))

    @pyqtProperty(QObject, notify = backupsChanged)
    def backups(self) -> BackupListModel:
        """
        Get a list of the backups.
        :return: The backups as Qt List Model.
        """
        return self._backups_list_model

    @pyqtSlot(name = "refreshBackups")
    def refreshBackups(self) -> None:
        """
        Forcefully refresh the backups list.
        """
        self._backups_list_model.loadBackups(self._drive_api_service.getBackups())
        self.backupsChanged.emit()

    @pyqtProperty(bool, notify = restoringStateChanged)
    def isRestoringBackup(self) -> bool:
        """
        Get the current restoring state.
        :return: Boolean if we are restoring or not.
        """
        return self._is_restoring_backup

    @pyqtProperty(bool, notify = creatingStateChanged)
    def isCreatingBackup(self) -> bool:
        """
        Get the current creating state.
        :return: Boolean if we are creating or not.
        """
        return self._is_creating_backup

    @pyqtSlot(str, name = "restoreBackup")
    def restoreBackup(self, backup_id: str) -> None:
        """
        Download and restore a backup by ID.
        :param backup_id: The ID of the backup.
        """
        index = self._backups_list_model.find("backup_id", backup_id)
        backup = self._backups_list_model.getItem(index)
        self._drive_api_service.restoreBackup(backup)

    @pyqtSlot(name = "createBackup")
    def createBackup(self) -> None:
        """
        Create a new backup.
        """
        self._drive_api_service.createBackup()

    @pyqtSlot(str, name = "deleteBackup")
    def deleteBackup(self, backup_id: str) -> None:
        """
        Delete a backup by ID.
        :param backup_id: The ID of the backup.
        """
        self._drive_api_service.deleteBackup(backup_id)
        self.refreshBackups()
