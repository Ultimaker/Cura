# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from cura import UltimakerCloudAuthentication


class Settings:
    # Keeps the plugin settings.
    DRIVE_API_VERSION = 1
    DRIVE_API_URL = "{}/cura-drive/v{}".format(UltimakerCloudAuthentication.CuraCloudAPIRoot, str(DRIVE_API_VERSION))

    AUTO_BACKUP_ENABLED_PREFERENCE_KEY = "cura_drive/auto_backup_enabled"
    AUTO_BACKUP_LAST_DATE_PREFERENCE_KEY = "cura_drive/auto_backup_date"
