# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import io
from typing import Optional, Dict, Union, List, cast

from UM.FileHandler.FileHandler import FileHandler
from UM.FileHandler.FileWriter import FileWriter
from UM.Logger import Logger
from UM.OutputDevice import OutputDeviceError  # To show that something went wrong when writing.
from UM.Scene.SceneNode import SceneNode
from UM.Version import Version  # To check against firmware versions for support.
from UM.i18n import i18nCatalog
from cura.CuraApplication import CuraApplication


I18N_CATALOG = i18nCatalog("cura")


## This class is responsible for choosing the formats used by the connected clusters.
class MeshFormatHandler:

    def __init__(self, file_handler: Optional[FileHandler], firmware_version: str) -> None:
        self._file_handler = file_handler or CuraApplication.getInstance().getMeshFileHandler()
        self._preferred_format = self._getPreferredFormat(firmware_version)
        self._writer = self._getWriter(self.mime_type) if self._preferred_format else None

    @property
    def is_valid(self) -> bool:
        return bool(self._writer)

    ## Chooses the preferred file format.
    #  \return A dict with the file format details, with the following keys:
    #       {id: str, extension: str, description: str, mime_type: str, mode: int, hide_in_file_dialog: bool}
    @property
    def preferred_format(self) -> Optional[Dict[str, Union[str, int, bool]]]:
        return self._preferred_format

    ## Gets the file writer for the given file handler and mime type.
    #  \return A file writer.
    @property
    def writer(self) -> Optional[FileWriter]:
        return self._writer

    @property
    def mime_type(self) -> str:
        return cast(str, self._preferred_format["mime_type"])

    ## Gets the file mode (FileWriter.OutputMode.TextMode or FileWriter.OutputMode.BinaryMode)
    @property
    def file_mode(self) -> int:
        return cast(int, self._preferred_format["mode"])

    ## Gets the file extension
    @property
    def file_extension(self) -> str:
        return cast(str, self._preferred_format["extension"])

    ## Creates the right kind of stream based on the preferred format.
    def createStream(self) -> Union[io.BytesIO, io.StringIO]:
        if self.file_mode == FileWriter.OutputMode.TextMode:
            return io.StringIO()
        else:
            return io.BytesIO()

    ## Writes the mesh and returns its value.
    def getBytes(self, nodes: List[SceneNode]) -> bytes:
        if self.writer is None:
            raise ValueError("There is no writer for the mesh format handler.")
        stream = self.createStream()
        self.writer.write(stream, nodes)
        value = stream.getvalue()
        if isinstance(value, str):
            value = value.encode()
        return value

    ## Chooses the preferred file format for the given file handler.
    #  \param firmware_version: The version of the firmware.
    #  \return A dict with the file format details.
    def _getPreferredFormat(self, firmware_version: str) -> Dict[str, Union[str, int, bool]]:
        # Formats supported by this application (file types that we can actually write).
        application = CuraApplication.getInstance()

        file_formats = self._file_handler.getSupportedFileTypesWrite()

        global_stack = application.getGlobalContainerStack()
        # Create a list from the supported file formats string.
        if not global_stack:
            Logger.log("e", "Missing global stack!")
            return {}

        machine_file_formats = global_stack.getMetaDataEntry("file_formats").split(";")
        machine_file_formats = [file_type.strip() for file_type in machine_file_formats]
        # Exception for UM3 firmware version >=4.4: UFP is now supported and should be the preferred file format.
        if "application/x-ufp" not in machine_file_formats and Version(firmware_version) >= Version("4.4"):
            machine_file_formats = ["application/x-ufp"] + machine_file_formats

        # Take the intersection between file_formats and machine_file_formats.
        format_by_mimetype = {f["mime_type"]: f for f in file_formats}

        # Keep them ordered according to the preference in machine_file_formats.
        file_formats = [format_by_mimetype[mimetype] for mimetype in machine_file_formats]

        if len(file_formats) == 0:
            Logger.log("e", "There are no file formats available to write with!")
            raise OutputDeviceError.WriteRequestFailedError(
                I18N_CATALOG.i18nc("@info:status", "There are no file formats available to write with!")
            )
        return file_formats[0]

    ## Gets the file writer for the given file handler and mime type.
    #  \param mime_type: The mine type.
    #  \return A file writer.
    def _getWriter(self, mime_type: str) -> Optional[FileWriter]:
        # Just take the first file format available.
        return self._file_handler.getWriterByMimeType(mime_type)
