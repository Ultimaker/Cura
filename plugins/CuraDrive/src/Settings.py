# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM import i18nCatalog

from cura import UltimakerCloudAuthentication


class Settings:
    """
    Keeps the application settings.
    """
    DRIVE_API_VERSION = 1
    DRIVE_API_URL = "{}/cura-drive/v{}".format(UltimakerCloudAuthentication.CuraCloudAPIRoot, str(DRIVE_API_VERSION))

    AUTO_BACKUP_ENABLED_PREFERENCE_KEY = "cura_drive/auto_backup_enabled"
    AUTO_BACKUP_LAST_DATE_PREFERENCE_KEY = "cura_drive/auto_backup_date"

    I18N_CATALOG_ID = "cura"
    I18N_CATALOG = i18nCatalog(I18N_CATALOG_ID)

    MESSAGE_TITLE = I18N_CATALOG.i18nc("@info:title", "Backups"),

    # Translatable messages for the entire plugin.
    translatable_messages = {
        
        # Menu items.
        "extension_menu_entry": I18N_CATALOG.i18nc("@item:inmenu", "Manage backups"),
        
        # Notification messages.
        "backup_failed": I18N_CATALOG.i18nc("@info:backup_status", "There was an error while creating your backup."),
        "uploading_backup": I18N_CATALOG.i18nc("@info:backup_status", "Uploading your backup..."),
        "uploading_backup_success": I18N_CATALOG.i18nc("@info:backup_status", "Your backup has finished uploading."),
        "uploading_backup_error": I18N_CATALOG.i18nc("@info:backup_status",
                                                     "There was an error while uploading your backup."),
        "get_backups_error": I18N_CATALOG.i18nc("@info:backup_status", "There was an error listing your backups."),
        "backup_restore_error_message": I18N_CATALOG.i18nc("@info:backup_status",
                                                           "There was an error trying to restore your backup.")
    }
