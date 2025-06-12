#  Copyright (c) 2025 UltiMaker
#  Cura is released under the terms of the LGPLv3 or higher.

import xml.etree.ElementTree as ET
import zipfile

from PyQt6.QtCore import QBuffer
from PyQt6.QtGui import QImage

from .ThreeMFVariant import ThreeMFVariant

# Standard 3MF paths
METADATA_PATH = "Metadata"
THUMBNAIL_PATH = f"{METADATA_PATH}/thumbnail.png"

class Cura3mfVariant(ThreeMFVariant):
    """Default implementation of the 3MF format."""
    
    @property
    def mime_type(self) -> str:
        return "application/vnd.ms-package.3dmanufacturing-3dmodel+xml"
    
    def process_thumbnail(self, snapshot: QImage, thumbnail_buffer: QBuffer, 
                          archive: zipfile.ZipFile, relations_element: ET.Element) -> None:
        """Process the thumbnail for default 3MF variant."""
        thumbnail_file = zipfile.ZipInfo(THUMBNAIL_PATH)
        # Don't try to compress snapshot file, because the PNG is pretty much as compact as it will get
        archive.writestr(thumbnail_file, thumbnail_buffer.data())

        # Add thumbnail relation to _rels/.rels file
        ET.SubElement(relations_element, "Relationship",
                      Target="/" + THUMBNAIL_PATH, Id="rel1",
                      Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail")
