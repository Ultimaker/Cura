# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import json
import threading
from json import JSONDecodeError
from typing import List, Dict, Any, Callable, Union, Optional

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtNetwork import QNetworkReply

from UM.FileHandler.FileHandler import FileHandler
from UM.Logger import Logger
from UM.Message import Message
from UM.Scene.SceneNode import SceneNode
from cura.CuraApplication import CuraApplication
from .BackwardsCompatibleMessage import getBackwardsCompatibleMessage
from .DFLibraryFileUploadRequest import DFLibraryFileUploadRequest
from .DFLibraryFileUploadResponse import DFLibraryFileUploadResponse
from .DFPrintJobUploadRequest import DFPrintJobUploadRequest
from .DFPrintJobUploadResponse import DFPrintJobUploadResponse
from .DigitalFactoryApiClient import DigitalFactoryApiClient
from .ExportFileJob import ExportFileJob


class DFFileExportAndUploadManager:
    """
    Class responsible for exporting the scene and uploading the exported data to the Digital Factory Library. Since 3mf
    and (UFP or makerbot) files may need to be uploaded at the same time, this class keeps a single progress and success message for
    both files and updates those messages according to the progress of both the file job uploads.
    """
    def __init__(self, file_handlers: Dict[str, FileHandler],
                 nodes: List[SceneNode],
                 library_project_id: str,
                 library_project_name: str,
                 file_name: str,
                 formats: List[str],
                 on_upload_error: Callable[[], Any],
                 on_upload_success: Callable[[], Any],
                 on_upload_finished: Callable[[], Any],
                 on_upload_progress: Callable[[int], Any]) -> None:

        self._file_handlers: Dict[str, FileHandler] = file_handlers
        self._nodes: List[SceneNode] = nodes
        self._library_project_id: str = library_project_id
        self._library_project_name: str = library_project_name
        self._file_name: str = file_name
        self._upload_jobs: List[ExportFileJob] = []
        self._formats: List[str] = formats
        self._api = DigitalFactoryApiClient(application = CuraApplication.getInstance(), on_error = lambda error: Logger.log("e", str(error)))
        self._source_file_id: Optional[str] = None

        # Functions of the parent class that should be called based on the upload process output
        self._on_upload_error = on_upload_error
        self._on_upload_success = on_upload_success
        self._on_upload_finished = on_upload_finished
        self._on_upload_progress = on_upload_progress

        # Lock used for updating the progress message (since the progress is changed by two parallel upload jobs) or
        # show the success message (once both upload jobs are done)
        self._message_lock = threading.Lock()

        self._file_upload_job_metadata: Dict[str, Dict[str, Any]] = self.initializeFileUploadJobMetadata()

        self.progress_message = Message(
                title = "Uploading...",
                text = "Uploading files to '{}'".format(self._library_project_name),
                progress = -1,
                lifetime = 0,
                dismissable = False,
                use_inactivity_timer = False
        )

        self._generic_success_message = getBackwardsCompatibleMessage(
                text = "Your {} uploaded to '{}'.".format("file was" if len(self._file_upload_job_metadata) <= 1 else "files were", self._library_project_name),
                title = "Upload successful",
                lifetime = 30,
                message_type_str = "POSITIVE"
        )
        self._generic_success_message.addAction(
                "open_df_project",
                "Open project",
                "open-folder", "Open the project containing the file in Digital Library"
        )
        self._generic_success_message.actionTriggered.connect(self._onMessageActionTriggered)

    def _onCuraProjectFileExported(self, job: ExportFileJob) -> None:
        """Handler for when the DF Library workspace file (3MF) has been created locally.

        It can now be sent over the Digital Factory API.
        """
        if not job.getOutput():
            self._onJobExportError(job.getFileName())
            return
        self._file_upload_job_metadata[job.getFileName()]["export_job_output"] = job.getOutput()
        request = DFLibraryFileUploadRequest(
                content_type = job.getMimeType(),
                file_name = job.getFileName(),
                file_size = len(job.getOutput()),
                library_project_id = self._library_project_id
        )
        self._api.requestUpload3MF(request, on_finished = self._uploadFileData, on_error = self._onRequestUploadCuraProjectFileFailed)

    def _onPrintFileExported(self, job: ExportFileJob) -> None:
        """Handler for when the DF Library print job file (UFP) has been created locally.

        It can now be sent over the Digital Factory API.
        """
        if not job.getOutput():
            self._onJobExportError(job.getFileName())
            return
        self._file_upload_job_metadata[job.getFileName()]["export_job_output"] = job.getOutput()
        request = DFPrintJobUploadRequest(
                content_type = job.getMimeType(),
                job_name = job.getFileName(),
                file_size = len(job.getOutput()),
                library_project_id = self._library_project_id,
                source_file_id = self._source_file_id
        )
        self._api.requestUploadMeshFile(request, on_finished = self._uploadFileData, on_error = self._onRequestUploadPrintFileFailed)

    def _uploadFileData(self, file_upload_response: Union[DFLibraryFileUploadResponse, DFPrintJobUploadResponse]) -> None:
        """Uploads the exported file data after the file or print job upload has been registered at the Digital Factory
        Library API.

        :param file_upload_response: The response received from the Digital Factory Library API.
        """
        if isinstance(file_upload_response, DFLibraryFileUploadResponse):
            file_name = file_upload_response.file_name

            # store the `file_id` so it can be as `source_file_id` when uploading the print file
            self._source_file_id = file_upload_response.file_id
        elif isinstance(file_upload_response, DFPrintJobUploadResponse):
            file_name = file_upload_response.job_name if file_upload_response.job_name is not None else ""
        else:
            Logger.log("e", "Wrong response type received. Aborting uploading file to the Digital Library")
            getBackwardsCompatibleMessage(
                    text = "Upload error",
                    title = f"Failed to upload {file_name}. Received unexpected response from server.",
                    message_type_str = "ERROR",
                    lifetime = 0
            ).show()
            return
        if file_name not in self._file_upload_job_metadata:
            Logger.error(f"API response for uploading doesn't match the file name we just uploaded: {file_name} was never uploaded.")
            getBackwardsCompatibleMessage(
                    text = "Upload error",
                    title = f"Failed to upload {file_name}. Name doesn't match the one sent back in confirmation.",
                    message_type_str = "ERROR",
                    lifetime = 0
            ).show()
            return
        with self._message_lock:
            self.progress_message.show()
        self._file_upload_job_metadata[file_name]["file_upload_response"] = file_upload_response
        job_output = self._file_upload_job_metadata[file_name]["export_job_output"]

        with self._message_lock:
            self._file_upload_job_metadata[file_name]["upload_status"] = "uploading"

        self._api.uploadExportedFileData(file_upload_response,
                                         job_output,
                                         on_finished = self._onFileUploadFinished,
                                         on_success = self._onUploadSuccess,
                                         on_progress = self._onUploadProgress,
                                         on_error = self._onUploadError)

        self._handleNextUploadJob()

    def _onUploadProgress(self, filename: str, progress: int) -> None:
        """
        Updates the progress message according to the total progress of the two files and displays it to the user. It is
        made thread-safe with a lock, since the progress can be updated by two separate upload jobs

        :param filename: The name of the file for which we have progress (including the extension).
        :param progress: The progress percentage
        """
        with self._message_lock:
            self._file_upload_job_metadata[filename]["upload_progress"] = progress
            self._file_upload_job_metadata[filename]["upload_status"] = "uploading"
            total_progress = self.getTotalProgress()
            self.progress_message.setProgress(total_progress)
            self.progress_message.show()
        self._on_upload_progress(progress)

    def _onUploadSuccess(self, filename: str) -> None:
        """
        Sets the upload status to success and the progress of the file with the given filename to 100%. This function is
        should be called only if the file has uploaded all of its data successfully (i.e. no error occurred during the
        upload process).

        :param filename: The name of the file that was uploaded successfully (including the extension).
        """
        with self._message_lock:
            self._file_upload_job_metadata[filename]["upload_status"] = "success"
            self._file_upload_job_metadata[filename]["upload_progress"] = 100
        self._on_upload_success()

    def _onFileUploadFinished(self, filename: str) -> None:
        """
        Callback that makes sure the correct messages are displayed according to the statuses of the individual jobs.

        This function is called whenever an upload job has finished, regardless if it had errors or was successful.
        Both jobs have to have finished for the messages to show.

        :param filename: The name of the file that has finished uploading (including the extension).
        """
        with self._message_lock:

            # All files have finished their uploading process
            if all([(file_upload_job["upload_progress"] == 100 and file_upload_job["upload_status"] != "uploading") for file_upload_job in self._file_upload_job_metadata.values()]):

                # Reset and hide the progress message
                self.progress_message.setProgress(-1)
                self.progress_message.hide()

                # All files were successfully uploaded.
                if all([(file_upload_job["upload_status"] == "success") for file_upload_job in self._file_upload_job_metadata.values()]):
                    # Show a single generic success message for all files
                    self._generic_success_message.show()
                else:  # One or more files failed to upload.
                    # Show individual messages for each file, according to their statuses
                    for filename, upload_job_metadata in self._file_upload_job_metadata.items():
                        if upload_job_metadata["upload_status"] == "success":
                            upload_job_metadata["file_upload_success_message"].show()
                        else:
                            upload_job_metadata["file_upload_failed_message"].show()

                # Call the parent's finished function
                self._on_upload_finished()

    def _onJobExportError(self, filename: str) -> None:
        """
        Displays an appropriate message when the process to export a file fails.

        :param filename: The name of the file that failed to be exported (including the extension).
        """
        Logger.log("d", "Error while exporting file '{}'".format(filename))
        with self._message_lock:
            # Set the progress to 100% when the upload job fails, to avoid having the progress message stuck
            self._file_upload_job_metadata[filename]["upload_status"] = "failed"
            self._file_upload_job_metadata[filename]["upload_progress"] = 100
            self._file_upload_job_metadata[filename]["file_upload_failed_message"] = getBackwardsCompatibleMessage(
                    text = "Failed to export the file '{}'. The upload process is aborted.".format(filename),
                    title = "Export error",
                    message_type_str = "ERROR",
                    lifetime = 30
            )
        self._on_upload_error()
        self._onFileUploadFinished(filename)

    def _onRequestUploadCuraProjectFileFailed(self, reply: "QNetworkReply", network_error: "QNetworkReply.NetworkError") -> None:
        """
        Displays an appropriate message when the request to upload the Cura project file (.3mf) to the Digital Library fails.
        This means that something went wrong with the initial request to create a "file" entry in the digital library.
        """
        reply_string = bytes(reply.readAll()).decode()
        filename_3mf = self._file_name + ".3mf"
        Logger.log("d", "An error occurred while uploading the Cura project file '{}' to the Digital Library project '{}': {}".format(filename_3mf, self._library_project_id, reply_string))
        with self._message_lock:
            # Set the progress to 100% when the upload job fails, to avoid having the progress message stuck
            self._file_upload_job_metadata[filename_3mf]["upload_status"] = "failed"
            self._file_upload_job_metadata[filename_3mf]["upload_progress"] = 100

            human_readable_error = self.extractErrorTitle(reply_string)
            self._file_upload_job_metadata[filename_3mf]["file_upload_failed_message"] = getBackwardsCompatibleMessage(
                    text = "Failed to upload the file '{}' to '{}'. {}".format(filename_3mf, self._library_project_name, human_readable_error),
                    title = "File upload error",
                    message_type_str = "ERROR",
                    lifetime = 30
            )
        self._on_upload_error()
        self._onFileUploadFinished(filename_3mf)

    def _onRequestUploadPrintFileFailed(self, reply: "QNetworkReply", network_error: "QNetworkReply.NetworkError") -> None:
        """
        Displays an appropriate message when the request to upload the print file (.ufp) to the Digital Library fails.
        This means that something went wrong with the initial request to create a "file" entry in the digital library.
        """
        reply_string = bytes(reply.readAll()).decode()
        if "ufp" in self._formats:
            filename_meshfile = self._file_name + ".ufp"
        elif "makerbot" in self._formats:
            filename_meshfile = self._file_name + ".makerbot"
        Logger.log("d", "An error occurred while uploading the print job file '{}' to the Digital Library project '{}': {}".format(filename_meshfile, self._library_project_id, reply_string))
        with self._message_lock:
            # Set the progress to 100% when the upload job fails, to avoid having the progress message stuck
            self._file_upload_job_metadata[filename_meshfile]["upload_status"] = "failed"
            self._file_upload_job_metadata[filename_meshfile]["upload_progress"] = 100

            human_readable_error = self.extractErrorTitle(reply_string)
            self._file_upload_job_metadata[filename_meshfile]["file_upload_failed_message"] = getBackwardsCompatibleMessage(
                    title = "File upload error",
                    text = "Failed to upload the file '{}' to '{}'. {}".format(filename_meshfile, self._library_project_name, human_readable_error),
                    message_type_str = "ERROR",
                    lifetime = 30
            )
        self._on_upload_error()
        self._onFileUploadFinished(filename_meshfile)

    @staticmethod
    def extractErrorTitle(reply_body: Optional[str]) -> str:
        error_title = ""
        if reply_body:
            try:
                reply_dict = json.loads(reply_body)
            except JSONDecodeError:
                Logger.logException("w", "Unable to extract title from reply body")
                return error_title
            if "errors" in reply_dict and len(reply_dict["errors"]) >= 1 and "title" in reply_dict["errors"][0]:
                error_title = reply_dict["errors"][0]["title"]
        return error_title

    def _onUploadError(self, filename: str, reply: "QNetworkReply", error: "QNetworkReply.NetworkError") -> None:
        """
        Displays the given message if uploading the mesh has failed due to a generic error (i.e. lost connection).
        If one of the two files fail, this error function will set its progress as finished, to make sure that the
        progress message doesn't get stuck.

        :param filename: The name of the file that failed to upload (including the extension).
        """
        reply_string = bytes(reply.readAll()).decode()
        Logger.log("d", "Error while uploading '{}' to the Digital Library project '{}'. Reply: {}".format(filename, self._library_project_id, reply_string))
        with self._message_lock:
            # Set the progress to 100% when the upload job fails, to avoid having the progress message stuck
            self._file_upload_job_metadata[filename]["upload_status"] = "failed"
            self._file_upload_job_metadata[filename]["upload_progress"] = 100
            human_readable_error = self.extractErrorTitle(reply_string)
            self._file_upload_job_metadata[filename]["file_upload_failed_message"] = getBackwardsCompatibleMessage(
                    title = "File upload error",
                    text = "Failed to upload the file '{}' to '{}'. {}".format(self._file_name, self._library_project_name, human_readable_error),
                    message_type_str = "ERROR",
                    lifetime = 30
            )

        self._on_upload_error()

    def getTotalProgress(self) -> int:
        """
        Returns the total upload progress of all the upload jobs

        :return: The average progress percentage
        """
        return int(sum([file_upload_job["upload_progress"] for file_upload_job in self._file_upload_job_metadata.values()]) / len(self._file_upload_job_metadata.values()))

    def _onMessageActionTriggered(self, message, action):
        if action == "open_df_project":
            project_url = "{}/app/library/project/{}?wait_for_new_files=true&utm_source=cura&utm_medium=software&utm_campaign=saved-library-file-message".format(CuraApplication.getInstance().ultimakerDigitalFactoryUrl, self._library_project_id)
            QDesktopServices.openUrl(QUrl(project_url))
            message.hide()

    def start(self) -> None:
        self._handleNextUploadJob()

    def _handleNextUploadJob(self):
        try:
            job = self._upload_jobs.pop(0)
            job.start()
        except IndexError:
            pass  # Empty list, do nothing.

    def initializeFileUploadJobMetadata(self) -> Dict[str, Any]:
        metadata = {}
        self._upload_jobs = []
        if "3mf" in self._formats and "3mf" in self._file_handlers and self._file_handlers["3mf"]:
            filename_3mf = self._file_name + ".3mf"
            metadata[filename_3mf] = {
                "export_job_output"   : None,
                "upload_progress"     : -1,
                "upload_status"       : "",
                "file_upload_response": None,
                "file_upload_success_message": getBackwardsCompatibleMessage(
                    text = "'{}' was uploaded to '{}'.".format(filename_3mf, self._library_project_name),
                    title = "Upload successful",
                    message_type_str = "POSITIVE",
                    lifetime = 30
                ),
                "file_upload_failed_message": getBackwardsCompatibleMessage(
                    text = "Failed to upload the file '{}' to '{}'.".format(filename_3mf, self._library_project_name),
                    title = "File upload error",
                    message_type_str = "ERROR",
                    lifetime = 30
                )
            }
            job_3mf = ExportFileJob(self._file_handlers["3mf"], self._nodes, self._file_name, "3mf")
            job_3mf.finished.connect(self._onCuraProjectFileExported)
            self._upload_jobs.append(job_3mf)

        if "ufp" in self._formats and "ufp" in self._file_handlers and self._file_handlers["ufp"]:
            filename_ufp = self._file_name + ".ufp"
            metadata[filename_ufp] = {
                "export_job_output"   : None,
                "upload_progress"     : -1,
                "upload_status"       : "",
                "file_upload_response": None,
                "file_upload_success_message": getBackwardsCompatibleMessage(
                    text = "'{}' was uploaded to '{}'.".format(filename_ufp, self._library_project_name),
                    title = "Upload successful",
                    message_type_str = "POSITIVE",
                    lifetime = 30,
                ),
                "file_upload_failed_message": getBackwardsCompatibleMessage(
                    text = "Failed to upload the file '{}' to '{}'.".format(filename_ufp, self._library_project_name),
                    title = "File upload error",
                    message_type_str = "ERROR",
                    lifetime = 30
                )
            }
            job_ufp = ExportFileJob(self._file_handlers["ufp"], self._nodes, self._file_name, "ufp")
            job_ufp.finished.connect(self._onPrintFileExported)
            self._upload_jobs.append(job_ufp)

        if "makerbot" in self._formats and "makerbot" in self._file_handlers and self._file_handlers["makerbot"]:
            filename_makerbot = self._file_name + ".makerbot"
            metadata[filename_makerbot] = {
                "export_job_output"   : None,
                "upload_progress"     : -1,
                "upload_status"       : "",
                "file_upload_response": None,
                "file_upload_success_message": getBackwardsCompatibleMessage(
                    text = "'{}' was uploaded to '{}'.".format(filename_makerbot, self._library_project_name),
                    title = "Upload successful",
                    message_type_str = "POSITIVE",
                    lifetime = 30,
                ),
                "file_upload_failed_message": getBackwardsCompatibleMessage(
                    text = "Failed to upload the file '{}' to '{}'.".format(filename_makerbot, self._library_project_name),
                    title = "File upload error",
                    message_type_str = "ERROR",
                    lifetime = 30
                )
            }
            job_makerbot = ExportFileJob(self._file_handlers["makerbot"], self._nodes, self._file_name, "makerbot")
            job_makerbot.finished.connect(self._onPrintFileExported)
            self._upload_jobs.append(job_makerbot)
        return metadata
