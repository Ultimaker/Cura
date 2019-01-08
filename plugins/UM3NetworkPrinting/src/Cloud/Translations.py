# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from UM import i18nCatalog


## Class that contains all the translations for this module.
class Translations:
    # The translation catalog for this device.

    _I18N_CATALOG = i18nCatalog("cura")

    PRINT_VIA_CLOUD_BUTTON = _I18N_CATALOG.i18nc("@action:button", "Print via Cloud")
    PRINT_VIA_CLOUD_TOOLTIP = _I18N_CATALOG.i18nc("@properties:tooltip", "Print via Cloud")

    CONNECTED_VIA_CLOUD = _I18N_CATALOG.i18nc("@info:status", "Connected via Cloud")
    BLOCKED_UPLOADING = _I18N_CATALOG.i18nc("@info:status", "Sending new jobs (temporarily) blocked, still sending "
                                                            "the previous print job.")

    COULD_NOT_EXPORT = _I18N_CATALOG.i18nc("@info:status", "Could not export print job.")

    ERROR = _I18N_CATALOG.i18nc("@info:title", "Error")
    UPLOAD_ERROR = _I18N_CATALOG.i18nc("@info:text", "Could not upload the data to the printer.")

    UPLOAD_SUCCESS_TITLE = _I18N_CATALOG.i18nc("@info:title", "Data Sent")
    UPLOAD_SUCCESS_TEXT = _I18N_CATALOG.i18nc("@info:status", "Print job was successfully sent to the printer.")

    JOB_COMPLETED_TITLE = _I18N_CATALOG.i18nc("@info:status", "Print finished")
    JOB_COMPLETED_PRINTER = _I18N_CATALOG.i18nc("@info:status",
                                                "Printer '{printer_name}' has finished printing '{job_name}'.")

    JOB_COMPLETED_NO_PRINTER = _I18N_CATALOG.i18nc("@info:status", "The print job '{job_name}' was finished.")