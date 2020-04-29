from typing import Optional, TYPE_CHECKING, List, Dict

from PyQt5.QtCore import QObject, pyqtSlot, Qt, pyqtSignal, pyqtProperty

from UM.Qt.ListModel import ListModel

if TYPE_CHECKING:
    from cura.CuraApplication import CuraApplication


class DiscoveredUltimakerCloudPrintersModel(ListModel):
    DeviceKeyRole = Qt.UserRole + 1
    DeviceNameRole = Qt.UserRole + 2
    DeviceTypeRole = Qt.UserRole + 3
    DeviceFirmwareVersionRole = Qt.UserRole + 4

    cloudPrintersDetectedChanged = pyqtSignal(bool)

    def __init__(self, application: "CuraApplication", parent: Optional["QObject"] = None) -> None:
        super().__init__(parent)

        self.addRoleName(self.DeviceKeyRole, "key")
        self.addRoleName(self.DeviceNameRole, "name")
        self.addRoleName(self.DeviceTypeRole, "machine_type")
        self.addRoleName(self.DeviceFirmwareVersionRole, "firmware_version")

        self._discovered_ultimaker_cloud_printers_list = []  # type: List[Dict[str, str]]
        self._new_cloud_printers_detected = False  # type: bool
        self._application = application  # type: CuraApplication

    def addDiscoveredUltimakerCloudPrinters(self, new_devices: List[Optional[Dict[str, str]]]) -> None:
        for device in new_devices:
            self._discovered_ultimaker_cloud_printers_list.append({
                "key": device.getId(),
                "name": device.name,
                "machine_type": device.printerTypeName,
                "firmware_version": device.firmwareVersion
            })
        self._update()

        # Inform whether new cloud printers have been detected. If they have, the welcome wizard can close.
        self._new_cloud_printers_detected = len(new_devices) > 0
        self.cloudPrintersDetectedChanged.emit(len(new_devices) > 0)

    @pyqtSlot()
    def clear(self) -> None:
        self._discovered_ultimaker_cloud_printers_list = []
        self._update()
        self._new_cloud_printers_detected = False
        self.cloudPrintersDetectedChanged.emit(False)

    def _update(self) -> None:
        items = []

        for cloud_printer in self._discovered_ultimaker_cloud_printers_list:
            items.append(cloud_printer)

        # Execute all filters.
        filtered_items = list(items)

        filtered_items.sort(key = lambda k: k["name"])
        self.setItems(filtered_items)

    @pyqtProperty(bool, notify = cloudPrintersDetectedChanged)
    def newCloudPrintersDetected(self) -> bool:
        return self._new_cloud_printers_detected
