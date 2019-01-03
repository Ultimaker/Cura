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

    I18N_CATALOG = i18nCatalog("cura")

    MESSAGE_TITLE = I18N_CATALOG.i18nc("@info:title", "Backups")