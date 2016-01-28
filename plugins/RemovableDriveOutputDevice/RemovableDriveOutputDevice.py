import os.path

from UM.Application import Application
from UM.Logger import Logger
from UM.Message import Message
from UM.Mesh.WriteMeshJob import WriteMeshJob
from UM.Mesh.MeshWriter import MeshWriter
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator
from UM.OutputDevice.OutputDevice import OutputDevice
from UM.OutputDevice import OutputDeviceError
from UM.Preferences import Preferences

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

        Preferences.getInstance().addPreference("removable_drive/file_type", "text/x-gcode") #Add a preference that says in what file type we should store the file.

        self._writing = False

    def requestWrite(self, node, file_name = None):
        if self._writing:
            raise OutputDeviceError.DeviceBusyError()

        file_type = Preferences.getInstance().getValue("removable_drive/file_type")
        gcode_writer = Application.getInstance().getMeshFileHandler().getWriterByMimeType(file_type)
        if not gcode_writer:
            Logger.log("e", "Could not find writer for MIME type %s, not writing to removable drive %s", file_type, self.getName())
            raise OutputDeviceError.WriteRequestFailedError()

        if file_name == None:
            for n in BreadthFirstIterator(node):
                if n.getMeshData():
                    file_name = n.getName()
                    if file_name:
                        break

        if not file_name:
            Logger.log("e", "Could not determine a proper file name when trying to write to %s, aborting", self.getName())
            raise OutputDeviceError.WriteRequestFailedError()

        file_name = os.path.join(self.getId(), os.path.splitext(file_name)[0] + ".gcode")

        try:
            Logger.log("d", "Writing to %s", file_name)
            stream = open(file_name, "wt")
            job = WriteMeshJob(gcode_writer, stream, node, MeshWriter.OutputMode.TextMode)
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
            raise OutputDeviceError.PermissionDeniedError() from e
        except OSError as e:
            Logger.log("e", "Operating system would not let us write to %s: %s", file_name, str(e))
            raise OutputDeviceError.WriteRequestFailedError() from e

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
            message = Message(catalog.i18nc("@info:status", "Saved to Removable Drive {0} as {1}").format(self.getName(), os.path.basename(job.getFileName())))
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

