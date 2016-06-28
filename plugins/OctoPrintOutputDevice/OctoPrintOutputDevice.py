# OctoPrintOutputDevice

import os.path

from PyQt5 import QtNetwork
from PyQt5.QtCore import QTemporaryFile, QUrl
from PyQt5.QtGui import QDesktopServices

from UM.Application import Application
from UM.Logger import Logger
from UM.Message import Message
from UM.Job import Job
from UM.Mesh.WriteMeshJob import WriteMeshJob
from UM.Mesh.MeshWriter import MeshWriter
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator
from UM.OutputDevice.OutputDevice import OutputDevice
from UM.OutputDevice import OutputDeviceError

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


from enum import Enum
class OutputStage(Enum):
    ready = 0
    writing = 1
    uploading = 2


class OctoPrintOutputDevice(OutputDevice):
    def __init__(self, name="OctoPrint", host="http://octopi.local", apiKey=""):
        super().__init__(name)

        self.setName(name)
        description = catalog.i18nc("@action:button", "Save to {0} ({1})").format(name, host)
        self.setShortDescription(description)
        self.setDescription(description)

        self._stage = OutputStage.ready
        self._host = host
        self._apiKey = apiKey

        self._qnam = QtNetwork.QNetworkAccessManager()
        self._qnam.authenticationRequired.connect(self._onAuthRequired)
        self._qnam.sslErrors.connect(self._onSslErrors)
        self._qnam.finished.connect(self._onNetworkFinished)

        self._stream = None
        self._cleanupRequest()

    def requestWrite(self, node, fileName = None, filterByMachine = False):
        if self._stage != OutputStage.ready:
            raise OutputDeviceError.DeviceBusyError()

        # get the file format
        fileFormats = Application.getInstance().getMeshFileHandler().getSupportedFileTypesWrite()
        gcodeFileFormat = None
        for fileFormat in fileFormats:
            if fileFormat["mime_type"] == "text/x-gcode":
                gcodeFileFormat = fileFormat
                break
        if gcodeFileFormat is None:
            Logger.log("e", "OctoPrint plugin couldn't find the g-code output file format")
            raise OutputDeviceError.WriteRequestFailedError()

        # get a writer for that format
        writer = Application.getInstance().getMeshFileHandler().getWriterByMimeType(gcodeFileFormat["mime_type"])
        extension = gcodeFileFormat["extension"]

        # figure out a filename
        for n in BreadthFirstIterator(node):
            if n.getMeshData():
                fileName = n.getName()
                if fileName:
                    break

        if not fileName:
            Logger.log("e", "fileName: {0}".format(fileName))
            Logger.log("e", "Could not determine a proper file name when trying to write to %s, aborting", self.getName())
            raise OutputDeviceError.WriteRequestFailedError()

        if extension:
            extension = "." + extension
        fileName = os.path.splitext(fileName)[0] + extension
        self._fileName = fileName
        tmpFileName = ""

        try:
            # create the temp file for the gcode
            self._stream = QTemporaryFile()
            self._stream.open()
            tmpFileName = self._stream.fileName()

            # create the writer job
            job = WriteMeshJob(writer, self._stream, node, MeshWriter.OutputMode.TextMode)
            job.setFileName(fileName)
            job.progress.connect(self._onProgress)
            job.finished.connect(self._onWriteFinished)

            # show a progress message
            message = Message(catalog.i18nc("@info:progress", "Saving to OctoPrint <filename>{0}</filename>").format(self.getName()), 0, False, -1)
            message.show()
            self._message = message
            job._message = message

            # set our state and start the job
            self._stage = OutputStage.writing
            self.writeStarted.emit(self)
            job.start()
        except PermissionError as e:
            Logger.log("e", "Permission denied when trying to write to temporary file %s for %s: %s", tmpFileName, fileName, str(e))
            raise OutputDeviceError.PermissionDeniedError(catalog.i18nc("@info:status", "Could not save to temporary file <filename>{0}</filename> for <filename>{1}</filename>: <message>{2}</message>").format(tmpFileName, fileName, str(e))) from e
        except OSError as e:
            Logger.log("e", "Unable to write to temporary file %s for %s: %s", tmpFileName, fileName, str(e))
            raise OutputDeviceError.WriteRequestFailedError(catalog.i18nc("@info:status", "Could not save to temporary file <filename>{0}</filename> for <filename>{1}</filename>: <message>{2}</message>").format(tmpFileName, fileName, str(e))) from e

    def _onProgress(self, job, progress):
        progress = (50 if self._stage == OutputStage.uploading else 0) + (progress / 2)
        if self._message:
            self._message.setProgress(progress)
        self.writeProgress.emit(self, progress)

    def _onWriteFinished(self, job):
        # failed to write the temporary gcode file
        if not job.getResult():
            if hasattr(job, "_message"):
                job._message.hide()
                job._message = None
            self._cleanupRequest()
            message = Message(catalog.i18nc("@info:status", "Could not save to OctoPrint {0}: {1}").format(self.getName(), str(job.getError())))
            message.show()
            self.writeError.emit(self)
            return

        # the temp file contains the gcode, now upload it
        self._stage = OutputStage.uploading
        self._stream.seek(0)

        # set up a multi-part post
        self._multipart = QtNetwork.QHttpMultiPart(QtNetwork.QHttpMultiPart.FormDataType)

        # add the form variables
        formvalues = {'select': 'false', 'print': 'false'}
        for key, value in formvalues.items():
            part = QtNetwork.QHttpPart()
            part.setHeader(QtNetwork.QNetworkRequest.ContentDispositionHeader,
                    'form-data; name="%s"' % key)
            part.setBody(value)
            self._multipart.append(part)

        # add the file part
        part = QtNetwork.QHttpPart()
        part.setHeader(QtNetwork.QNetworkRequest.ContentDispositionHeader,
                'form-data; name="file"; filename="%s"' % job.getFileName())
        part.setBodyDevice(self._stream)
        self._multipart.append(part)

        # send the post
        self._request = QtNetwork.QNetworkRequest(QUrl(self._host + "/api/files/local"))
        self._request.setRawHeader('User-agent', 'Cura OctoPrintOutputDevice Plugin')
        self._request.setRawHeader('X-Api-Key', self._apiKey)
        self._reply = self._qnam.post(self._request, self._multipart)

        # connect the reply signals
        self._reply.error.connect(self._onNetworkError)
        self._reply.uploadProgress.connect(self._onUploadProgress)
        self._reply.downloadProgress.connect(self._onDownloadProgress)

        if hasattr(job, "_message"):
            self._message = job._message
            job._message = None

    def _cleanupRequest(self):
        self._reply = None
        self._request = None
        self._multipart = None
        if self._stream:
            self._stream.close()
        self._stream = None
        self._stage = OutputStage.ready
        self._fileName = None

    def _onNetworkFinished(self, reply):
        Logger.log("i", "_onNetworkFinished reply: %s", repr(reply.readAll()))
        Logger.log("i", "_onNetworkFinished reply.error(): %s", repr(reply.error()))

        self._stage = OutputStage.ready
        if self._message:
            self._message.hide()
        self._message = None

        self.writeFinished.emit(self)
        if reply.error():
            message = Message(catalog.i18nc("@info:status", "Could not save to OctoPrint {0}: {1}").format(self.getName(), str(reply.errorString())))
            message.show()
            self.writeError.emit(self)
        else:
            message = Message(catalog.i18nc("@info:status", "Saved to OctoPrint {0} as {1}").format(self.getName(), os.path.basename(self._fileName)))
            message.addAction("open_browser", catalog.i18nc("@action:button", "Open Browser"), "globe", catalog.i18nc("@info:tooltip", "Open browser to OctoPrint."))
            message.actionTriggered.connect(self._onMessageActionTriggered)
            message.show()
            self.writeSuccess.emit(self)
        self._cleanupRequest()

    def _onMessageActionTriggered(self, message, action):
        if action == "open_browser":
            QDesktopServices.openUrl(QUrl(self._host))

    def _onAuthRequired(self, authenticator):
        Logger.log("e", "Not yet implemented: OctoPrint authentication other than api-key")

    def _onSslErrors(self, reply, errors):
        Logger.log("e", "Ssl errors: %s", repr(errors))

        errorString = ", ".join([str(error.errorString()) for error in errors])
        self.setError(errorString)
        message = Message(catalog.i18nc("@info:progress", "One or more SSL errors has occurred: {0}").format(errorString), 0, False, -1)
        message.show()

    def _onUploadProgress(self, bytesSent, bytesTotal):
        if bytesTotal > 0:
            self._onProgress(self, int(bytesSent * 100 / bytesTotal))

    def _onDownloadProgress(self, bytesReceived, bytesTotal):
        pass

    def _onNetworkError(self, errorCode):
        Logger.log("e", "_onNetworkError: %s", repr(errorCode))
        if self._message:
            self._message.hide()
        self._message = None
        self.setError(str(errorCode))

    def _cancelUpload(self):
        if self._message:
            self._message.hide()
        self._message = None
        self._reply.abort()
