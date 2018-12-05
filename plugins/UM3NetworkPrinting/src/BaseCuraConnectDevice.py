# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional, Dict, Union

from UM.FileHandler.FileHandler import FileHandler
from UM.FileHandler.FileWriter import FileWriter
from UM.Logger import Logger
from UM.OutputDevice import OutputDeviceError  # To show that something went wrong when writing.
from UM.Version import Version  # To check against firmware versions for support.
from UM.i18n import i18nCatalog
from cura.CuraApplication import CuraApplication
from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice


## Class that contains all the translations for this module.
class T:
    # The translation catalog for this device.

    _I18N_CATALOG = i18nCatalog("cura")
    NO_FORMATS_AVAILABLE = _I18N_CATALOG.i18nc("@info:status", "There are no file formats available to write with!")


## This is the base class for the UM3 output devices (via connect or cloud)
class BaseCuraConnectDevice(NetworkedPrinterOutputDevice):

    ## Gets the default file handler
    @property
    def defaultFileHandler(self) -> FileHandler:
        return CuraApplication.getInstance().getMeshFileHandler()

    ## Chooses the preferred file format for the given file handler.
    #  \param file_handler: The file handler.
    #  \return A dict with the file format details, with format:
    #       {id: str, extension: str, description: str, mime_type: str, mode: int, hide_in_file_dialog: bool}
    def _getPreferredFormat(self, file_handler: Optional[FileHandler]) -> Optional[Dict[str, Union[str, int, bool]]]:
        # Formats supported by this application (file types that we can actually write).
        application = CuraApplication.getInstance()

        file_handler = file_handler or self.defaultFileHandler
        file_formats = file_handler.getSupportedFileTypesWrite()

        global_stack = application.getGlobalContainerStack()
        # Create a list from the supported file formats string.
        if not global_stack:
            Logger.log("e", "Missing global stack!")
            return

        machine_file_formats = global_stack.getMetaDataEntry("file_formats").split(";")
        machine_file_formats = [file_type.strip() for file_type in machine_file_formats]
        # Exception for UM3 firmware version >=4.4: UFP is now supported and should be the preferred file format.
        if "application/x-ufp" not in machine_file_formats and Version(self.firmwareVersion) >= Version("4.4"):
            machine_file_formats = ["application/x-ufp"] + machine_file_formats

        # Take the intersection between file_formats and machine_file_formats.
        format_by_mimetype = {f["mime_type"]: f for f in file_formats}

        # Keep them ordered according to the preference in machine_file_formats.
        file_formats = [format_by_mimetype[mimetype] for mimetype in machine_file_formats]

        if len(file_formats) == 0:
            Logger.log("e", "There are no file formats available to write with!")
            raise OutputDeviceError.WriteRequestFailedError(T.NO_FORMATS_AVAILABLE)
        return file_formats[0]

    ## Gets the file writer for the given file handler and mime type.
    #  \param file_handler: The file handler.
    #  \param mime_type: The mine type.
    #  \return A file writer.
    def _getWriter(self, file_handler: Optional[FileHandler], mime_type: str) -> Optional[FileWriter]:
        # Just take the first file format available.
        file_handler = file_handler or self.defaultFileHandler
        return file_handler.getWriterByMimeType(mime_type)
