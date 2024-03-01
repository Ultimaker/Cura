#  Copyright (c) 2021 Ultimaker B.V.
#  Cura is released under the terms of the LGPLv3 or higher.

import re
from typing import Any, cast, Dict, List, Optional

from PyQt6.QtCore import pyqtProperty, QObject, pyqtSignal, pyqtSlot
from PyQt6.QtQml import QQmlEngine

from cura.CuraApplication import CuraApplication
from cura.CuraPackageManager import CuraPackageManager
from cura.Settings.CuraContainerRegistry import CuraContainerRegistry  # To get names of materials we're compatible with.
from UM.i18n import i18nCatalog  # To translate placeholder names if data is not present.
from UM.PluginRegistry import PluginRegistry

catalog = i18nCatalog("cura")


class PackageModel(QObject):
    """
    Represents a package, containing all the relevant information to be displayed about a package.
    """

    def __init__(self, package_data: Dict[str, Any], section_title: Optional[str] = None, parent: Optional[QObject] = None) -> None:
        """
        Constructs a new model for a single package.
        :param package_data: The data received from the Marketplace API about the package to create.
        :param section_title: If the packages are to be categorized per section provide the section_title
        :param parent: The parent QML object that controls the lifetime of this model (normally a PackageList).
        """
        super().__init__(parent)
        QQmlEngine.setObjectOwnership(self, QQmlEngine.ObjectOwnership.CppOwnership)
        self._package_manager: CuraPackageManager = cast(CuraPackageManager, CuraApplication.getInstance().getPackageManager())
        self._plugin_registry: PluginRegistry = CuraApplication.getInstance().getPluginRegistry()

        self._package_id = package_data.get("package_id", "UnknownPackageId")
        self._package_type = package_data.get("package_type", "")
        self._is_bundled = package_data.get("is_bundled", False)
        self._icon_url = package_data.get("icon_url", "")
        self._marketplace_url = package_data.get("marketplace_url", "")
        self._display_name = package_data.get("display_name", catalog.i18nc("@label:property", "Unknown Package"))
        tags = package_data.get("tags", [])
        self._is_checked_by_ultimaker = (self._package_type == "plugin" and "verified" in tags) or (
                    self._package_type == "material" and "certified" in tags)
        self._package_version = package_data.get("package_version", "")  # Display purpose, no need for 'UM.Version'.
        self._package_info_url = package_data.get("website", "")  # Not to be confused with 'download_url'.
        self._download_count = package_data.get("download_count", 0)
        self._description = package_data.get("description", "")
        self._formatted_description = self._format(self._description)

        self._download_url = package_data.get("download_url", "")
        self._release_notes = package_data.get("release_notes", "")  # Not used yet, propose to add to description?

        subdata = package_data.get("data", {})
        self._technical_data_sheet = self._findLink(subdata, "technical_data_sheet")
        self._safety_data_sheet = self._findLink(subdata, "safety_data_sheet")
        self._where_to_buy = self._findLink(subdata, "where_to_buy")
        self._compatible_printers = self._getCompatiblePrinters(subdata)
        self._compatible_support_materials = self._getCompatibleSupportMaterials(subdata)
        self._is_compatible_material_station = self._isCompatibleMaterialStation(subdata)
        self._is_compatible_air_manager = self._isCompatibleAirManager(subdata)

        author_data = package_data.get("author", {})
        self._author_name = author_data.get("display_name", catalog.i18nc("@label:property", "Unknown Author"))
        self._author_info_url = author_data.get("website", "")
        if not self._icon_url or self._icon_url == "":
            self._icon_url = author_data.get("icon_url", "")

        self._can_update = False
        self._section_title = section_title
        self.sdk_version = package_data.get("sdk_version_semver", "")
        # Note that there's a lot more info in the package_data than just these specified here.

        self.enablePackageTriggered.connect(self._plugin_registry.enablePlugin)
        self.disablePackageTriggered.connect(self._plugin_registry.disablePlugin)

        self._plugin_registry.pluginsEnabledOrDisabledChanged.connect(self.stateManageButtonChanged)
        self._package_manager.packageInstalled.connect(lambda pkg_id: self._packageInstalled(pkg_id))
        self._package_manager.packageUninstalled.connect(lambda pkg_id: self._packageInstalled(pkg_id))
        self._package_manager.packageInstallingFailed.connect(lambda pkg_id: self._packageInstalled(pkg_id))
        self._package_manager.packagesWithUpdateChanged.connect(self._processUpdatedPackages)

        self._is_busy = False

        self._is_missing_package_information = False

    @classmethod
    def fromIncompletePackageInformation(cls, display_name: str, package_version: str,
                                         package_type: str) -> "PackageModel":
        description = ""
        match package_type:
            case "material":
                description = catalog.i18nc("@label:label Ultimaker Marketplace is a brand name, don't translate",
                                            "The material package associated with the Cura project could not be found on the Ultimaker Marketplace. Use the partial material profile definition stored in the Cura project file at your own risk.")
            case "plugin":
                description = catalog.i18nc("@label:label Ultimaker Marketplace is a brand name, don't translate",
                                            "The plugin associated with the Cura project could not be found on the Ultimaker Marketplace. As the plugin may be required to slice the project it might not be possible to correctly slice the file.")

        package_data = {
            "display_name": display_name,
            "package_version": package_version,
            "package_type": package_type,
            "description": description,
        }
        package_model = cls(package_data)
        package_model.setIsMissingPackageInformation(True)
        return package_model

    @pyqtSlot()
    def _processUpdatedPackages(self):
        self.setCanUpdate(self._package_manager.checkIfPackageCanUpdate(self._package_id))

    def __del__(self):
        self._package_manager.packagesWithUpdateChanged.disconnect(self._processUpdatedPackages)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, PackageModel):
            return other == self
        elif isinstance(other, str):
            return other == self._package_id
        else:
            return False

    def __repr__(self) -> str:
        return f"<{self._package_id} : {self._package_version} : {self._section_title}>"

    def _findLink(self, subdata: Dict[str, Any], link_type: str) -> str:
        """
        Searches the package data for a link of a certain type.

        The links are not in a fixed path in the package data. We need to iterate over the available links to find them.
        :param subdata: The "data" element in the package data, which should contain links.
        :param link_type: The type of link to find.
        :return: A URL of where the link leads, or an empty string if there is no link of that type in the package data.
        """
        links = subdata.get("links", [])
        for link in links:
            if link.get("type", "") == link_type:
                return link.get("url", "")
        else:
            return ""  # No link with the correct type was found.

    def _format(self, text: str) -> str:
        """
        Formats a user-readable block of text for display.
        :return: A block of rich text with formatting embedded.
        """
        # Turn all in-line hyperlinks into actual links.
        url_regex = re.compile(r"(((http|https)://)[a-zA-Z0-9@:%.\-_+~#?&/=]{2,256}\.[a-z]{2,12}(/[a-zA-Z0-9@:%.\-_+~#?&/=]*)?)")
        text = re.sub(url_regex, r'<a href="\1">\1</a>', text)

        # Turn newlines into <br> so that they get displayed as newlines when rendering as rich text.
        text = text.replace("\n", "<br>")

        return text

    def _getCompatiblePrinters(self, subdata: Dict[str, Any]) -> List[str]:
        """
        Gets the list of printers that this package provides material compatibility with.

        Any printer is listed, even if it's only for a single nozzle on a single material in the package.
        :param subdata: The "data" element in the package data, which should contain this compatibility information.
        :return: A list of printer names that this package provides material compatibility with.
        """
        result = set()

        for material in subdata.get("materials", []):
            for compatibility in material.get("compatibility", []):
                printer_name = compatibility.get("machine_name")
                if printer_name is None:
                    continue  # Missing printer name information. Skip this one.
                for subcompatibility in compatibility.get("compatibilities", []):
                    if subcompatibility.get("hardware_compatible", False):
                        result.add(printer_name)
                        break

        return list(sorted(result))

    def _getCompatibleSupportMaterials(self, subdata: Dict[str, Any]) -> List[str]:
        """
        Gets the list of support materials that the materials in this package are compatible with.

        Since the materials are individually encoded as keys in the API response, only PVA and Breakaway are currently
        supported.
        :param subdata: The "data" element in the package data, which should contain this compatibility information.
        :return: A list of support materials that the materials in this package are compatible with.
        """
        result = set()

        container_registry = CuraContainerRegistry.getInstance()
        try:
            pva_name = container_registry.findContainersMetadata(id = "ultimaker_pva")[0].get("name", "Ultimaker PVA")
        except IndexError:
            pva_name = "Ultimaker PVA"
        try:
            breakaway_name = container_registry.findContainersMetadata(id = "ultimaker_bam")[0].get("name", "Ultimaker Breakaway")
        except IndexError:
            breakaway_name = "Ultimaker Breakaway"

        for material in subdata.get("materials", []):
            if material.get("pva_compatible", False):
                result.add(pva_name)
            if material.get("breakaway_compatible", False):
                result.add(breakaway_name)

        return list(sorted(result))

    def _isCompatibleMaterialStation(self, subdata: Dict[str, Any]) -> bool:
        """
        Finds out if this package provides any material that is compatible with the material station.
        :param subdata: The "data" element in the package data, which should contain this compatibility information.
        :return: Whether this package provides any material that is compatible with the material station.
        """
        for material in subdata.get("materials", []):
            for compatibility in material.get("compatibility", []):
                if compatibility.get("material_station_optimized", False):
                    return True
        return False

    def _isCompatibleAirManager(self, subdata: Dict[str, Any]) -> bool:
        """
        Finds out if this package provides any material that is compatible with the air manager.
        :param subdata: The "data" element in the package data, which should contain this compatibility information.
        :return: Whether this package provides any material that is compatible with the air manager.
        """
        for material in subdata.get("materials", []):
            for compatibility in material.get("compatibility", []):
                if compatibility.get("air_manager_optimized", False):
                    return True
        return False

    @pyqtProperty(str, constant = True)
    def packageId(self) -> str:
        return self._package_id

    @pyqtProperty(str, constant=True)
    def marketplaceURL(self)-> str:
        return self._marketplace_url

    @pyqtProperty(str, constant = True)
    def packageType(self) -> str:
        return self._package_type

    @pyqtProperty(str, constant = True)
    def iconUrl(self) -> str:
        return self._icon_url

    @pyqtProperty(str, constant = True)
    def displayName(self) -> str:
        return self._display_name

    @pyqtProperty(bool, constant = True)
    def isCheckedByUltimaker(self):
        return self._is_checked_by_ultimaker

    @pyqtProperty(str, constant = True)
    def packageVersion(self) -> str:
        return self._package_version

    @pyqtProperty(str, constant = True)
    def packageInfoUrl(self) -> str:
        return self._package_info_url

    @pyqtProperty(int, constant = True)
    def downloadCount(self) -> str:
        return self._download_count

    @pyqtProperty(str, constant = True)
    def description(self) -> str:
        return self._description

    @pyqtProperty(str, constant = True)
    def formattedDescription(self) -> str:
        return self._formatted_description

    @pyqtProperty(str, constant = True)
    def authorName(self) -> str:
        return self._author_name

    @pyqtProperty(str, constant = True)
    def authorInfoUrl(self) -> str:
        return self._author_info_url

    @pyqtProperty(str, constant = True)
    def sectionTitle(self) -> Optional[str]:
        return self._section_title

    @pyqtProperty(str, constant = True)
    def technicalDataSheet(self) -> str:
        return self._technical_data_sheet

    @pyqtProperty(str, constant = True)
    def safetyDataSheet(self) -> str:
        return self._safety_data_sheet

    @pyqtProperty(str, constant = True)
    def whereToBuy(self) -> str:
        return self._where_to_buy

    @pyqtProperty("QStringList", constant = True)
    def compatiblePrinters(self) -> List[str]:
        return self._compatible_printers

    @pyqtProperty("QStringList", constant = True)
    def compatibleSupportMaterials(self) -> List[str]:
        return self._compatible_support_materials

    @pyqtProperty(bool, constant = True)
    def isCompatibleMaterialStation(self) -> bool:
        return self._is_compatible_material_station

    @pyqtProperty(bool, constant = True)
    def isCompatibleAirManager(self) -> bool:
        return self._is_compatible_air_manager

    @pyqtProperty(bool, constant = True)
    def isBundled(self) -> bool:
        return self._is_bundled

    def setDownloadUrl(self, download_url):
        self._download_url = download_url

    # --- manage buttons signals ---

    stateManageButtonChanged = pyqtSignal()

    installPackageTriggered = pyqtSignal(str, str)

    uninstallPackageTriggered = pyqtSignal(str)

    updatePackageTriggered = pyqtSignal(str, str)

    enablePackageTriggered = pyqtSignal(str)

    disablePackageTriggered = pyqtSignal(str)

    busyChanged = pyqtSignal()

    @pyqtSlot()
    def install(self):
        self.setBusy(True)
        self.installPackageTriggered.emit(self.packageId, self._download_url)

    @pyqtSlot()
    def update(self):
        self.setBusy(True)
        self.updatePackageTriggered.emit(self.packageId, self._download_url)

    @pyqtSlot()
    def uninstall(self):
        self.uninstallPackageTriggered.emit(self.packageId)

    @pyqtProperty(bool, notify= busyChanged)
    def busy(self):
        """
        Property indicating that some kind of upgrade is active.
        """
        return self._is_busy

    @pyqtSlot()
    def enable(self):
        self.enablePackageTriggered.emit(self.packageId)

    @pyqtSlot()
    def disable(self):
        self.disablePackageTriggered.emit(self.packageId)

    def setBusy(self, value: bool):
        if self._is_busy != value:
            self._is_busy = value
            try:
                self.busyChanged.emit()
            except RuntimeError:
                pass

    def _packageInstalled(self, package_id: str) -> None:
        if self._package_id != package_id:
            return
        self.setBusy(False)
        try:
            self.stateManageButtonChanged.emit()
        except RuntimeError:
            pass

    @pyqtProperty(bool, notify = stateManageButtonChanged)
    def isInstalled(self) -> bool:
        return self._package_id in self._package_manager.getAllInstalledPackageIDs()

    @pyqtProperty(bool, notify = stateManageButtonChanged)
    def isToBeInstalled(self) -> bool:
        return self._package_id in self._package_manager.getPackagesToInstall()

    @pyqtProperty(bool, notify = stateManageButtonChanged)
    def isActive(self) -> bool:
        return not self._package_id in self._plugin_registry.getDisabledPlugins()

    @pyqtProperty(bool, notify = stateManageButtonChanged)
    def canDowngrade(self) -> bool:
        """Flag if the installed package can be downgraded to a bundled version"""
        return self._package_manager.canDowngrade(self._package_id)

    def setCanUpdate(self, value: bool) -> None:
        self._can_update = value
        self.stateManageButtonChanged.emit()

    @pyqtProperty(bool, fset = setCanUpdate, notify = stateManageButtonChanged)
    def canUpdate(self) -> bool:
        """Flag indicating if the package can be updated"""
        return self._can_update

    isMissingPackageInformationChanged = pyqtSignal()

    def setIsMissingPackageInformation(self, isMissingPackageInformation: bool) -> None:
        self._is_missing_package_information = isMissingPackageInformation
        self.isMissingPackageInformationChanged.emit()

    @pyqtProperty(bool, notify=isMissingPackageInformationChanged)
    def isMissingPackageInformation(self) -> bool:
        """Flag indicating if the package can be updated"""
        return self._is_missing_package_information
