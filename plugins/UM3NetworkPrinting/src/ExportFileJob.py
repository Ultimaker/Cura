# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import re  # Filtering out invalid characters.
from typing import List, Optional

from UM.FileHandler.FileHandler import FileHandler
from UM.FileHandler.WriteFileJob import WriteFileJob
from UM.Logger import Logger
from UM.Scene.SceneNode import SceneNode
from cura.CuraApplication import CuraApplication

from .MeshFormatHandler import MeshFormatHandler


class ExportFileJob(WriteFileJob):
    """Job that exports the build plate to the correct file format for the target cluster."""

    def __init__(self, file_handler: Optional[FileHandler], nodes: List[SceneNode], firmware_version: str) -> None:

        self._mesh_format_handler = MeshFormatHandler(file_handler, firmware_version)
        if not self._mesh_format_handler.is_valid:
            Logger.log("e", "Missing file or mesh writer!")
            return

        super().__init__(self._mesh_format_handler.writer, self._mesh_format_handler.createStream(), nodes,
                         self._mesh_format_handler.file_mode)

        # Determine the filename.
        job_name = CuraApplication.getInstance().getPrintInformation().jobName
        job_name = re.sub("[^\w\-. ()]", "-", job_name)
        extension = self._mesh_format_handler.preferred_format.get("extension", "")
        self.setFileName("{}.{}".format(job_name, extension))

    def getMimeType(self) -> str:
        """Get the mime type of the selected export file type."""

        return self._mesh_format_handler.mime_type

    def getOutput(self) -> bytes:
        """Get the job result as bytes as that is what we need to upload to the cluster."""

        output = self.getStream().getvalue()
        if isinstance(output, str):
            output = output.encode("utf-8")
        return output
