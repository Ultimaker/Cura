#  Copyright (c) 2025 UltiMaker
#  Cura is released under the terms of the LGPLv3 or higher.

import hashlib
import json
from io import StringIO
import xml.etree.ElementTree as ET
import zipfile

from PyQt6.QtCore import Qt, QBuffer
from PyQt6.QtGui import QImage

from UM.Application import Application
from UM.Logger import Logger
from UM.Mesh.MeshWriter import MeshWriter
from UM.PluginRegistry import PluginRegistry
from typing import cast

from cura.CuraApplication import CuraApplication

from .ThreeMFVariant import ThreeMFVariant
from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

# Path constants
METADATA_PATH = "Metadata"
THUMBNAIL_PATH_MULTIPLATE = f"{METADATA_PATH}/plate_1.png"
THUMBNAIL_PATH_MULTIPLATE_SMALL = f"{METADATA_PATH}/plate_1_small.png"
GCODE_PATH = f"{METADATA_PATH}/plate_1.gcode"
GCODE_MD5_PATH = f"{GCODE_PATH}.md5"
MODEL_SETTINGS_PATH = f"{METADATA_PATH}/model_settings.config"
PLATE_DESC_PATH = f"{METADATA_PATH}/plate_1.json"
SLICE_INFO_PATH = f"{METADATA_PATH}/slice_info.config"

class BambuLabVariant(ThreeMFVariant):
    """BambuLab specific implementation of the 3MF format."""
    
    @property
    def mime_type(self) -> str:
        return "application/vnd.bambulab-package.3dmanufacturing-3dmodel+xml"
    
    def process_thumbnail(self, snapshot: QImage, thumbnail_buffer: QBuffer, 
                          archive: zipfile.ZipFile, relations_element: ET.Element) -> None:
        """Process the thumbnail for BambuLab variant."""
        # Write thumbnail
        archive.writestr(zipfile.ZipInfo(THUMBNAIL_PATH_MULTIPLATE), thumbnail_buffer.data())
        
        # Add relations elements for thumbnails
        ET.SubElement(relations_element, "Relationship",
                      Target="/" + THUMBNAIL_PATH_MULTIPLATE, Id="rel-2",
                      Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail")
        
        ET.SubElement(relations_element, "Relationship",
                      Target="/" + THUMBNAIL_PATH_MULTIPLATE, Id="rel-4",
                      Type="http://schemas.bambulab.com/package/2021/cover-thumbnail-middle")
        
        # Create and save small thumbnail
        small_snapshot = snapshot.scaled(128, 128, transformMode=Qt.TransformationMode.SmoothTransformation)
        small_thumbnail_buffer = QBuffer()
        small_thumbnail_buffer.open(QBuffer.OpenModeFlag.ReadWrite)
        small_snapshot.save(small_thumbnail_buffer, "PNG")
        
        # Write small thumbnail
        archive.writestr(zipfile.ZipInfo(THUMBNAIL_PATH_MULTIPLATE_SMALL), small_thumbnail_buffer.data())
        
        # Add relation for small thumbnail
        ET.SubElement(relations_element, "Relationship",
                      Target="/" + THUMBNAIL_PATH_MULTIPLATE_SMALL, Id="rel-5",
                      Type="http://schemas.bambulab.com/package/2021/cover-thumbnail-small")

    def add_extra_files(self, archive: zipfile.ZipFile, metadata_relations_element: ET.Element) -> None:
        """Add BambuLab specific files to the archive."""
        self._storeGCode(archive, metadata_relations_element)
        self._storeModelSettings(archive)
        self._storePlateDesc(archive)
        self._storeSliceInfo(archive)

    def _storeGCode(self, archive: zipfile.ZipFile, metadata_relations_element: ET.Element):
        """Store GCode data in the archive."""
        gcode_textio = StringIO()
        gcode_writer = cast(MeshWriter, PluginRegistry.getInstance().getPluginObject("GCodeWriter"))
        success = gcode_writer.write(gcode_textio, None)

        if not success:
            error_msg = catalog.i18nc("@info:error", "Can't write GCode to 3MF file")
            self._writer.setInformation(error_msg)
            Logger.error(error_msg)
            raise Exception(error_msg)

        gcode_data = gcode_textio.getvalue().encode("UTF-8")
        archive.writestr(zipfile.ZipInfo(GCODE_PATH), gcode_data)

        gcode_relation_element = ET.SubElement(metadata_relations_element, "Relationship",
                                              Target=f"/{GCODE_PATH}", Id="rel-1",
                                              Type="http://schemas.bambulab.com/package/2021/gcode")

        # Calculate and store the MD5 sum of the gcode data
        md5_hash = hashlib.md5(gcode_data).hexdigest()
        archive.writestr(zipfile.ZipInfo(GCODE_MD5_PATH), md5_hash.encode("UTF-8"))

    def _storeModelSettings(self, archive: zipfile.ZipFile):
        """Store model settings in the archive."""
        config = ET.Element("config")
        plate = ET.SubElement(config, "plate")
        ET.SubElement(plate, "metadata", key="plater_id", value="1")
        ET.SubElement(plate, "metadata", key="plater_name", value="")
        ET.SubElement(plate, "metadata", key="locked", value="false")
        ET.SubElement(plate, "metadata", key="filament_map_mode", value="Auto For Flush")
        extruders_count = len(CuraApplication.getInstance().getExtruderManager().extruderIds)
        ET.SubElement(plate, "metadata", key="filament_maps", value=" ".join("1" for _ in range(extruders_count)))
        ET.SubElement(plate, "metadata", key="gcode_file", value=GCODE_PATH)
        ET.SubElement(plate, "metadata", key="thumbnail_file", value=THUMBNAIL_PATH_MULTIPLATE)
        ET.SubElement(plate, "metadata", key="pattern_bbox_file", value=PLATE_DESC_PATH)

        self._writer._storeElementTree(archive, MODEL_SETTINGS_PATH, config)

    def _storePlateDesc(self, archive: zipfile.ZipFile):
        """Store plate description in the archive."""
        plate_desc = {}

        filament_ids = []
        filament_colors = []

        for extruder in CuraApplication.getInstance().getExtruderManager().getUsedExtruderStacks():
            filament_ids.append(extruder.getValue("extruder_nr"))
            filament_colors.append(self._writer._getMaterialColor(extruder))

        plate_desc["filament_ids"] = filament_ids
        plate_desc["filament_colors"] = filament_colors
        plate_desc["first_extruder"] = CuraApplication.getInstance().getExtruderManager().getInitialExtruderNr()
        plate_desc["is_seq_print"] = Application.getInstance().getGlobalContainerStack().getValue("print_sequence") == "one_at_a_time"
        plate_desc["nozzle_diameter"] = CuraApplication.getInstance().getExtruderManager().getActiveExtruderStack().getValue("machine_nozzle_size")
        plate_desc["version"] = 2

        file = zipfile.ZipInfo(PLATE_DESC_PATH)
        file.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(file, json.dumps(plate_desc).encode("UTF-8"))

    def _storeSliceInfo(self, archive: zipfile.ZipFile):
        """Store slice information in the archive."""
        config = ET.Element("config")

        header = ET.SubElement(config, "header")
        ET.SubElement(header, "header_item", key="X-BBL-Client-Type", value="slicer")
        ET.SubElement(header, "header_item", key="X-BBL-Client-Version", value="02.00.01.50")

        plate = ET.SubElement(config, "plate")
        ET.SubElement(plate, "metadata", key="index", value="1")
        ET.SubElement(plate,
                      "metadata",
                      key="nozzle_diameters",
                      value=str(CuraApplication.getInstance().getExtruderManager().getActiveExtruderStack().getValue("machine_nozzle_size")))

        print_information = CuraApplication.getInstance().getPrintInformation()
        for index, extruder in enumerate(Application.getInstance().getGlobalContainerStack().extruderList):
            used_m = print_information.materialLengths[index]
            used_g = print_information.materialWeights[index]
            if used_m > 0.0 and used_g > 0.0:
                ET.SubElement(plate,
                             "filament",
                             id=str(extruder.getValue("extruder_nr") + 1),
                             tray_info_idx="GFA00",
                             type=extruder.material.getMetaDataEntry("material", ""),
                             color=self._writer._getMaterialColor(extruder),
                             used_m=str(used_m),
                             used_g=str(used_g))

        self._writer._storeElementTree(archive, SLICE_INFO_PATH, config)