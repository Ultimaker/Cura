# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtProperty, QObject
import re
from typing import Any, Dict, List, Optional

from cura.Settings.CuraContainerRegistry import CuraContainerRegistry  # To get names of materials we're compatible with.
from UM.i18n import i18nCatalog  # To translate placeholder names if data is not present.

catalog = i18nCatalog("cura")


class PackageModel(QObject):
    """
    Represents a package, containing all the relevant information to be displayed about a package.

    Effectively this behaves like a glorified named tuple, but as a QObject so that its properties can be obtained from
    QML. The model can also be constructed directly from a response received by the API.
    """

    def __init__(self, package_data: Dict[str, Any], installation_status: str, section_title: Optional[str] = None, parent: Optional[QObject] = None) -> None:
        """
        Constructs a new model for a single package.
        :param package_data: The data received from the Marketplace API about the package to create.
        :param installation_status: Whether the package is `not_installed`, `installed` or `bundled`.
        :param section_title: If the packages are to be categorized per section provide the section_title
        :param parent: The parent QML object that controls the lifetime of this model (normally a PackageList).
        """
        super().__init__(parent)
        self._package_id = package_data.get("package_id", "UnknownPackageId")
        self._package_type = package_data.get("package_type", "")
        self._icon_url = package_data.get("icon_url", "")
        self._display_name = package_data.get("display_name", catalog.i18nc("@label:property", "Unknown Package"))
        tags = package_data.get("tags", [])
        self._is_checked_by_ultimaker = (self._package_type == "plugin" and "verified" in tags) or (self._package_type == "material" and "certified" in tags)
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

        self._installation_status = installation_status
        self._section_title = section_title
        # Note that there's a lot more info in the package_data than just these specified here.

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
        url_regex = re.compile(r"(((http|https)://)[a-zA-Z0-9@:%._+~#?&/=]{2,256}\.[a-z]{2,12}(/[a-zA-Z0-9@:%.-_+~#?&/=]*)?)")
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

    @pyqtProperty(str, constant = True)
    def packageType(self) -> str:
        return self._package_type

    @pyqtProperty(str, constant=True)
    def iconUrl(self):
        return self._icon_url

    @pyqtProperty(str, constant = True)
    def displayName(self) -> str:
        return self._display_name

    @pyqtProperty(bool, constant = True)
    def isCheckedByUltimaker(self):
        return self._is_checked_by_ultimaker

    @pyqtProperty(str, constant=True)
    def packageVersion(self):
        return self._package_version

    @pyqtProperty(str, constant=True)
    def packageInfoUrl(self):
        return self._package_info_url

    @pyqtProperty(int, constant=True)
    def downloadCount(self):
        return self._download_count

    @pyqtProperty(str, constant=True)
    def description(self):
        return self._description

    @pyqtProperty(str, constant = True)
    def formattedDescription(self) -> str:
        return self._formatted_description

    @pyqtProperty(str, constant=True)
    def authorName(self):
        return self._author_name

    @pyqtProperty(str, constant=True)
    def authorInfoUrl(self):
        return self._author_info_url

    @pyqtProperty(str, constant = True)
    def installationStatus(self) -> str:
        return self._installation_status

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
