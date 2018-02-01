import zipfile

from io import StringIO

from UM.Resources import Resources
from UM.Mesh.MeshWriter import MeshWriter
from UM.Logger import Logger
from UM.PluginRegistry import PluginRegistry

MYPY = False
try:
    if not MYPY:
        import xml.etree.cElementTree as ET
except ImportError:
    Logger.log("w", "Unable to load cElementTree, switching to slower version")
    import xml.etree.ElementTree as ET


class UCPWriter(MeshWriter):
    def __init__(self):
        super().__init__()
        self._namespaces = {
            "content-types": "http://schemas.openxmlformats.org/package/2006/content-types",
            "relationships": "http://schemas.openxmlformats.org/package/2006/relationships",
        }

    def write(self, stream, nodes, mode = MeshWriter.OutputMode.BinaryMode):
        self._archive = None  # Reset archive
        archive = zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED)

        gcode_file = zipfile.ZipInfo("3D/model.gcode")
        gcode_file.compress_type = zipfile.ZIP_DEFLATED

        # Create content types file
        content_types_file = zipfile.ZipInfo("[Content_Types].xml")
        content_types_file.compress_type = zipfile.ZIP_DEFLATED
        content_types = ET.Element("Types", xmlns=self._namespaces["content-types"])

        rels_type = ET.SubElement(content_types, "Default", Extension="rels",
                                  ContentType="application/vnd.openxmlformats-package.relationships+xml")
        gcode_type = ET.SubElement(content_types, "Default", Extension="gcode",
                                   ContentType="text/x-gcode")
        image_type = ET.SubElement(content_types, "Default", Extension="png",
                                   ContentType="image/png")

        # Create _rels/.rels file
        relations_file = zipfile.ZipInfo("_rels/.rels")
        relations_file.compress_type = zipfile.ZIP_DEFLATED
        relations_element = ET.Element("Relationships", xmlns=self._namespaces["relationships"])

        thumbnail_relation_element = ET.SubElement(relations_element, "Relationship", Target="/Metadata/thumbnail.png", Id="rel0",
                                               Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail")

        model_relation_element = ET.SubElement(relations_element, "Relationship", Target="/3D/model.gcode",
                                               Id="rel1",
                                               Type="http://schemas.ultimaker.org/package/2018/relationships/gcode")

        gcode_string = StringIO()

        PluginRegistry.getInstance().getPluginObject("GCodeWriter").write(gcode_string, None)

        archive.write(Resources.getPath(Resources.Images, "cura-icon.png"), "Metadata/thumbnail.png")

        archive.writestr(gcode_file, gcode_string.getvalue())
        archive.writestr(content_types_file, b'<?xml version="1.0" encoding="UTF-8"?> \n' + ET.tostring(content_types))
        archive.writestr(relations_file, b'<?xml version="1.0" encoding="UTF-8"?> \n' + ET.tostring(relations_element))

        archive.close()
