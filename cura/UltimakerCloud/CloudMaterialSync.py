# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt6.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QObject, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices
from typing import Dict, Optional, TYPE_CHECKING
import zipfile  # To export all materials in a .zip archive.

import cura.CuraApplication  # Imported like this to prevent circular imports.
from UM.Resources import Resources
from cura.PrinterOutput.UploadMaterialsJob import UploadMaterialsJob, UploadMaterialsError  # To export materials to the output printer.
from cura.Settings.CuraContainerRegistry import CuraContainerRegistry
from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.Message import Message

if TYPE_CHECKING:
    from UM.Signal import Signal
catalog = i18nCatalog("cura")


class CloudMaterialSync(QObject):
    """
    Handles the synchronisation of material profiles with cloud accounts.
    """

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self.sync_all_dialog: Optional[QObject] = None
        self._export_upload_status: str = "idle"
        self._checkIfNewMaterialsWereInstalled()
        self._export_progress: float = 0.0
        self._printer_status: Dict[str, str] = {}
        self._is_exporting_to_file: bool = False

    def _checkIfNewMaterialsWereInstalled(self) -> None:
        """
        Checks whether new material packages were installed in the latest startup. If there were, then it shows
        a message prompting the user to sync the materials with their printers.
        """
        application = cura.CuraApplication.CuraApplication.getInstance()
        for package_id, package_data in application.getPackageManager().getPackagesInstalledOnStartup().items():
            if package_data["package_info"]["package_type"] == "material":
                # At least one new material was installed
                self._showSyncNewMaterialsMessage()
                break

    def openSyncAllWindow(self):
        self.reset()

        if self.sync_all_dialog is None:
            qml_path = Resources.getPath(cura.CuraApplication.CuraApplication.ResourceTypes.QmlFiles, "Preferences",
                                         "Materials", "MaterialsSyncDialog.qml")
            self.sync_all_dialog = cura.CuraApplication.CuraApplication.getInstance().createQmlComponent(
                qml_path, {}, {"syncModel": self})
        if self.sync_all_dialog is None:  # Failed to load QML file.
            return
        self.sync_all_dialog.setProperty("pageIndex", 0)  # Return to first page.
        self.sync_all_dialog.setProperty("hasExportedUsb", False)  # If the user exported USB before, reset that page.
        self.sync_all_dialog.setProperty("syncStatusText", "")  # Reset any previous error messages.
        self.sync_all_dialog.show()

    def _showSyncNewMaterialsMessage(self) -> None:
        sync_materials_message = Message(
                text = catalog.i18nc("@action:button",
                                     "Please sync the material profiles with your printers before starting to print."),
                title = catalog.i18nc("@action:button", "New materials installed"),
                message_type = Message.MessageType.WARNING,
                lifetime = 0
        )

        sync_materials_message.addAction(
                "sync",
                name = catalog.i18nc("@action:button", "Sync materials"),
                icon = "",
                description = "Sync your newly installed materials with your printers.",
                button_align = Message.ActionButtonAlignment.ALIGN_RIGHT
        )

        sync_materials_message.addAction(
                "learn_more",
                name = catalog.i18nc("@action:button", "Learn more"),
                icon = "",
                description = "Learn more about syncing your newly installed materials with your printers.",
                button_align = Message.ActionButtonAlignment.ALIGN_LEFT,
                button_style = Message.ActionButtonStyle.LINK
        )
        sync_materials_message.actionTriggered.connect(self._onSyncMaterialsMessageActionTriggered)

        # Show the message only if there are printers that support material export
        container_registry = cura.CuraApplication.CuraApplication.getInstance().getContainerRegistry()
        global_stacks = container_registry.findContainerStacks(type = "machine")
        if any([stack.supportsMaterialExport for stack in global_stacks]):
            sync_materials_message.show()

    def _onSyncMaterialsMessageActionTriggered(self, sync_message: Message, sync_message_action: str):
        if sync_message_action == "sync":
            self.openSyncAllWindow()
            sync_message.hide()
        elif sync_message_action == "learn_more":
            QDesktopServices.openUrl(QUrl("https://support.ultimaker.com/s/article/1667337567839"))

    @pyqtSlot(result = QUrl)
    def getPreferredExportAllPath(self) -> QUrl:
        """
        Get the preferred path to export materials to.

        If there is a removable drive, that should be the preferred path. Otherwise it should be the most recent local
        file path.
        :return: The preferred path to export all materials to.
        """
        cura_application = cura.CuraApplication.CuraApplication.getInstance()
        device_manager = cura_application.getOutputDeviceManager()
        devices = device_manager.getOutputDevices()
        for device in devices:
            if device.__class__.__name__ == "RemovableDriveOutputDevice":
                return QUrl.fromLocalFile(device.getId())
        else:  # No removable drives? Use local path.
            return cura_application.getDefaultPath("dialog_material_path")

    exportToFileFinished = pyqtSignal(bool)
    isExportingToFileChanged = pyqtSignal()

    @pyqtProperty(bool, notify = isExportingToFileChanged)
    def isExportingToFile(self) -> bool:
        return self._is_exporting_to_file

    @pyqtSlot(QUrl)
    def exportAllToFile(self, file_path: QUrl) -> None:
        """
        Export all materials to a file chosen by the user.
        Emits exportToFileFinished when done.

        The export itself runs on the main thread and will block the UI, so this first flags the export as started and
        gives the UI a moment to show that before starting the actual work.
        :param file_path: The path to export the materials to.
        """
        if self._is_exporting_to_file:
            return
        self._is_exporting_to_file = True
        self.isExportingToFileChanged.emit()
        QTimer.singleShot(100, lambda: self._exportToFile(file_path))

    def _exportToFile(self, file_path: QUrl) -> None:
        error: Optional[Exception] = None
        try:
            self.exportAll(file_path)
        except Exception as e:
            Logger.logException("e", f"Failed to export material archive to {file_path.toLocalFile()}: {e}")
            error = e
        self._onExportToFileFinished(file_path, error)

    def _onExportToFileFinished(self, file_path: QUrl, error: Optional[Exception]) -> None:
        if error is not None:
            error_message = Message(
                text = catalog.i18nc("@message:text", "Could not save material archive to {}:").format(file_path.toLocalFile()) + " " + str(error),
                title = catalog.i18nc("@message:title", "Failed to save material archive"),
                message_type = Message.MessageType.ERROR
            )
            error_message.show()
        self._is_exporting_to_file = False
        self.isExportingToFileChanged.emit()
        self.exportToFileFinished.emit(error is None)

    def exportAll(self, file_path: QUrl, notify_progress: Optional["Signal"] = None) -> None:
        """
        Export all materials to a certain file path.
        :param file_path: The path to export the materials to.
        :raises OSError: If the archive could not be created or written.
        """
        registry = CuraContainerRegistry.getInstance()
        with zipfile.ZipFile(file_path.toLocalFile(), "w", compression = zipfile.ZIP_DEFLATED) as archive:
            materials_metadata = registry.findInstanceContainersMetadata(type = "material")
            for index, metadata in enumerate(materials_metadata):
                if notify_progress is not None:
                    progress = index / len(materials_metadata)
                    notify_progress.emit(progress)
                if metadata["base_file"] != metadata["id"]:  # Only process base files.
                    continue
                if metadata["id"] == "empty_material":  # Don't export the empty material.
                    continue
                # Ignore materials that are marked as not visible for whatever reason
                if not bool(metadata.get("visible", True)):
                    continue
                material = registry.findContainers(id = metadata["id"])[0]
                suffix = registry.getMimeTypeForContainer(type(material)).preferredSuffix
                archive.writestr(metadata["id"] + "." + suffix, material.serialize())

    exportUploadStatusChanged = pyqtSignal()

    @pyqtProperty(str, notify = exportUploadStatusChanged)
    def exportUploadStatus(self) -> str:
        return self._export_upload_status

    @pyqtSlot()
    def exportUpload(self) -> None:
        """
        Export all materials and upload them to the user's account.
        """
        self._export_upload_status = "uploading"
        self.exportUploadStatusChanged.emit()
        job = UploadMaterialsJob(self)
        job.uploadProgressChanged.connect(self._onUploadProgressChanged)
        job.uploadCompleted.connect(self.exportUploadCompleted)
        job.start()

    def _onUploadProgressChanged(self, progress: float, printers_status: Dict[str, str]):
        self.setExportProgress(progress)
        self.setPrinterStatus(printers_status)

    def exportUploadCompleted(self, job_result: UploadMaterialsJob.Result, job_error: Optional[Exception]):
        if not self.sync_all_dialog:  # Shouldn't get triggered before the dialog is open, but better to check anyway.
            return
        if job_result == UploadMaterialsJob.Result.FAILED:
            if isinstance(job_error, UploadMaterialsError):
                self.sync_all_dialog.setProperty("syncStatusText", str(job_error))
            else:  # Could be "None"
                self.sync_all_dialog.setProperty("syncStatusText", catalog.i18nc("@text", "Unknown error."))
            self._export_upload_status = "error"
        else:
            self._export_upload_status = "success"
        self.exportUploadStatusChanged.emit()

    exportProgressChanged = pyqtSignal(float)

    def setExportProgress(self, progress: float) -> None:
        self._export_progress = progress
        self.exportProgressChanged.emit(self._export_progress)

    @pyqtProperty(float, fset = setExportProgress, notify = exportProgressChanged)
    def exportProgress(self) -> float:
        return self._export_progress

    printerStatusChanged = pyqtSignal()

    def setPrinterStatus(self, new_status: Dict[str, str]) -> None:
        self._printer_status = new_status
        self.printerStatusChanged.emit()

    @pyqtProperty("QVariantMap", fset = setPrinterStatus, notify = printerStatusChanged)
    def printerStatus(self) -> Dict[str, str]:
        return self._printer_status

    def reset(self) -> None:
        self.setPrinterStatus({})
        self.setExportProgress(0.0)
        self._export_upload_status = "idle"
        self.exportUploadStatusChanged.emit()
