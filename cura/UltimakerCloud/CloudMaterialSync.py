# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QObject, QUrl
from PyQt5.QtGui import QDesktopServices
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
        self.sync_all_dialog = None  # type: Optional[QObject]
        self._export_upload_status = "idle"
        self._checkIfNewMaterialsWereInstalled()
        self._export_progress = 0.0
        self._printer_status = {}  # type: Dict[str, str]

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
                qml_path, {})
        if self.sync_all_dialog is None:  # Failed to load QML file.
            return
        self.sync_all_dialog.setProperty("syncModel", self)
        self.sync_all_dialog.setProperty("pageIndex", 0)  # Return to first page.
        self.sync_all_dialog.setProperty("hasExportedUsb", False)  # If the user exported USB before, reset that page.
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
                name = catalog.i18nc("@action:button", "Sync materials with printers"),
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
            QDesktopServices.openUrl(QUrl("https://support.ultimaker.com/hc/en-us/articles/360013137919?utm_source=cura&utm_medium=software&utm_campaign=sync-material-printer-message"))

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

    @pyqtSlot(QUrl)
    def exportAll(self, file_path: QUrl, notify_progress: Optional["Signal"] = None) -> None:
        """
        Export all materials to a certain file path.
        :param file_path: The path to export the materials to.
        """
        registry = CuraContainerRegistry.getInstance()

        # Create empty archive.
        try:
            archive = zipfile.ZipFile(file_path.toLocalFile(), "w", compression = zipfile.ZIP_DEFLATED)
        except OSError as e:
            Logger.log("e", f"Can't write to destination {file_path.toLocalFile()}: {type(e)} - {str(e)}")
            error_message = Message(
                text = catalog.i18nc("@message:text", "Could not save material archive to {}:").format(file_path.toLocalFile()) + " " + str(e),
                title = catalog.i18nc("@message:title", "Failed to save material archive"),
                message_type = Message.MessageType.ERROR
            )
            error_message.show()
            return

        materials_metadata = registry.findInstanceContainersMetadata(type = "material")
        for index, metadata in enumerate(materials_metadata):
            if notify_progress is not None:
                progress = index / len(materials_metadata)
                notify_progress.emit(progress)
            if metadata["base_file"] != metadata["id"]:  # Only process base files.
                continue
            if metadata["id"] == "empty_material":  # Don't export the empty material.
                continue
            material = registry.findContainers(id = metadata["id"])[0]
            suffix = registry.getMimeTypeForContainer(type(material)).preferredSuffix
            filename = metadata["id"] + "." + suffix
            try:
                archive.writestr(filename, material.serialize())
            except OSError as e:
                Logger.log("e", f"An error has occurred while writing the material \'{metadata['id']}\' in the file \'{filename}\': {e}.")

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
