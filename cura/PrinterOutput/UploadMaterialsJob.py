# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QUrl
import os  # To delete the archive when we're done.
import tempfile  # To create an archive before we upload it.

import cura.CuraApplication  # Imported like this to prevent circular imports.
from UM.Job import Job


class UploadMaterialsJob(Job):
    """
    Job that uploads a set of materials to the Digital Factory.
    """

    def run(self):
        archive_file = tempfile.NamedTemporaryFile("wb", delete = False)
        archive_file.close()

        cura.CuraApplication.CuraApplication.getInstance().getMaterialManagementModel().exportAll(QUrl.fromLocalFile(archive_file.name))

        print("Creating archive completed. Now we need to upload it.")  # TODO: Upload that file.

        os.remove(archive_file.name)  # Clean up.