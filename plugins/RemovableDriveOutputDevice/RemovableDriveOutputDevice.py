import os.path

from UM.Application import Application
from UM.Logger import Logger
from UM.Message import Message
from UM.Mesh.WriteMeshJob import WriteMeshJob
from UM.Mesh.MeshWriter import MeshWriter
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator
from UM.OutputDevice.OutputDevice import OutputDevice
from UM.OutputDevice import OutputDeviceError

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

class RemovableDriveOutputDevice(OutputDevice):
    def __init__(self, device_id, device_name):
        super().__init__(device_id)

        self.setName(device_name)
        self.setShortDescription(catalog.i18nc("@action:button", "Save to Removable Drive"))
        self.setDescription(catalog.i18nc("@item:inlistbox", "Save to Removable Drive {0}").format(device_name))
        self.setIconName("save_sd")
        self.setPriority(1)

        self._writing = False

    def requestWrite(self, node, file_name = None, filter_by_machine = False):
        filter_by_machine = True # This plugin is indended to be used by machine (regardless of what it was told to do)
        if self._writing:
            raise OutputDeviceError.DeviceBusyError()

        # Formats supported by this application (File types that we can actually write)
        file_formats = Application.getInstance().getMeshFileHandler().getSupportedFileTypesWrite()
        if filter_by_machine:
            container = Application.getInstance().getGlobalContainerStack().findContainer({"file_formats": "*"})

            # Create a list from supported file formats string
            machine_file_formats = [file_type.strip() for file_type in container.getMetaDataEntry("file_formats").split(";")]

            # Take the intersection between file_formats and machine_file_formats.
            file_formats = list(filter(lambda file_format: file_format["mime_type"] in machine_file_formats, file_formats))

        if len(file_formats) == 0:
            Logger.log("e", "There are no file formats available to write with!")
            raise OutputDeviceError.WriteRequestFailedError()

        # Just take the first file format available.
        writer = Application.getInstance().getMeshFileHandler().getWriterByMimeType(file_formats[0]["mime_type"])
        extension = file_formats[0]["extension"]

        if file_name is None:
            for n in BreadthFirstIterator(node):
                if n.getMeshData():
                    file_name = n.getName()
                    if file_name:
                        break

        if not file_name:
            Logger.log("e", "Could not determine a proper file name when trying to write to %s, aborting", self.getName())
            raise OutputDeviceError.WriteRequestFailedError()

        if extension:  # Not empty string.
            extension = "." + extension
        file_name = os.path.join(self.getId(), os.path.splitext(file_name)[0] + extension)

        try:
            Logger.log("d", "Writing to %s", file_name)
            stream = open(file_name, "wt")
            job = WriteMeshJob(writer, stream, node, MeshWriter.OutputMode.TextMode)
            job.setFileName(file_name)
            job.progress.connect(self._onProgress)
            job.finished.connect(self._onFinished)

            message = Message(catalog.i18nc("@info:progress", "Saving to Removable Drive <filename>{0}</filename>").format(self.getName()), 0, False, -1)
            message.show()

            self.writeStarted.emit(self)

            job._message = message
            self._writing = True
            job.start()
        except PermissionError as e:
            Logger.log("e", "Permission denied when trying to write to %s: %s", file_name, str(e))
            raise OutputDeviceError.PermissionDeniedError(catalog.i18nc("@info:status", "Could not save to <filename>{0}</filename>: <message>{1}</message>").format(file_name, str(e))) from e
        except OSError as e:
            Logger.log("e", "Operating system would not let us write to %s: %s", file_name, str(e))
            raise OutputDeviceError.WriteRequestFailedError(catalog.i18nc("@info:status", "Could not save to <filename>{0}</filename>: <message>{1}</message>").format(file_name, str(e))) from e

    def _onProgress(self, job, progress):
        if hasattr(job, "_message"):
            job._message.setProgress(progress)
        self.writeProgress.emit(self, progress)

    def _onFinished(self, job):
        if hasattr(job, "_message"):
            job._message.hide()
            job._message = None

        self._writing = False
        self.writeFinished.emit(self)
        if job.getResult():
            message = Message(catalog.i18nc("@info:status", "Saved to Removable Drive {0} as {1}").format(self.getName(), os.path.basename(job.getFileName())), lifetime = 0)
            message.addAction("eject", catalog.i18nc("@action:button", "Eject"), "eject", catalog.i18nc("@action", "Eject removable device {0}").format(self.getName()))
            message.actionTriggered.connect(self._onActionTriggered)
            message.show()
            self.writeSuccess.emit(self)
        else:
            message = Message(catalog.i18nc("@info:status", "Could not save to removable drive {0}: {1}").format(self.getName(), str(job.getError())))
            message.show()
            self.writeError.emit(self)
        job.getStream().close()

    def _onActionTriggered(self, message, action):
        if action == "eject":
            Application.getInstance().getOutputDeviceManager().getOutputDevicePlugin("RemovableDriveOutputDevice").ejectDevice(self)

