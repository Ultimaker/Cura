#  Copyright (c) 2025 UltiMaker
#  Cura is released under the terms of the LGPLv3 or higher.

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import xml.etree.ElementTree as ET
import zipfile

from PyQt6.QtGui import QImage
from PyQt6.QtCore import QBuffer

if TYPE_CHECKING:
    from .ThreeMFWriter import ThreeMFWriter

class ThreeMFVariant(ABC):
    """Base class for 3MF format variants.
    
    Different vendors may have their own extensions to the 3MF format,
    such as BambuLab's 3MF variant. This class provides an interface
    for implementing these variants.
    """
    
    def __init__(self, writer: 'ThreeMFWriter'):
        """
        :param writer: The ThreeMFWriter instance that will use this variant
        """
        self._writer = writer
    
    @property
    @abstractmethod
    def mime_type(self) -> str:
        """The MIME type for this 3MF variant."""
        pass

    def handles_mime_type(self, mime_type: str) -> bool:
        """Check if this variant handles the given MIME type.
        
        :param mime_type: The MIME type to check
        :return: True if this variant handles the MIME type, False otherwise
        """
        return mime_type == self.mime_type
    
    def prepare_content_types(self, content_types: ET.Element) -> None:
        """Prepare the content types XML element for this variant.
        
        :param content_types: The content types XML element
        """
        pass
    
    def prepare_relations(self, relations_element: ET.Element) -> None:
        """Prepare the relations XML element for this variant.
        
        :param relations_element: The relations XML element
        """
        pass
    
    def process_thumbnail(self, snapshot: QImage, thumbnail_buffer: QBuffer, 
                          archive: zipfile.ZipFile, relations_element: ET.Element) -> None:
        """Process the thumbnail for this variant.
        
        :param snapshot: The snapshot image
        :param thumbnail_buffer: Buffer containing the thumbnail data
        :param archive: The zip archive to write to
        :param relations_element: The relations XML element
        """
        pass

    def add_extra_files(self, archive: zipfile.ZipFile, metadata_relations_element: ET.Element) -> None:
        """Add any extra files required by this variant to the archive.
        
        :param archive: The zip archive to write to
        :param metadata_relations_element: The metadata relations XML element
        """
        pass
