#Copyright (c) 2018 Ultimaker B.V.
#Cura is released under the terms of the LGPLv3 or higher.

from charon.VirtualFile import VirtualFile #To open UFP files.
from charon.OpenMode import OpenMode #To indicate that we want to write to UFP files.
from io import StringIO #For converting g-code to bytes.
import os.path #To get the placeholder kitty icon.

from UM.Mesh.MeshWriter import MeshWriter #The writer we need to implement.
from UM.PluginRegistry import PluginRegistry #To get the g-code writer.

class UFPWriter(MeshWriter):
    def write(self, stream, nodes, mode = MeshWriter.OutputMode.BinaryMode):
        archive = VirtualFile()
        archive.open(stream, OpenMode.WriteOnly)

        #Store the g-code from the scene.
        archive.addContentType(extension = "gcode", mime_type = "text/x-gcode")
        gcode_textio = StringIO() #We have to convert the g-code into bytes.
        PluginRegistry.getInstance().getPluginObject("GCodeWriter").write(gcode_textio, None)
        gcode = archive.getStream("/3D/model.gcode")
        gcode.write(gcode_textio.getvalue().encode("UTF-8"))
        archive.addRelation(target = "/3D/model.gcode", file_type = "http://schemas.ultimaker.org/package/2018/relationships/gcode")

        #Store the thumbnail.
        #TODO: Generate the thumbnail image. Below is just a placeholder.
        archive.addContentType(extension = "png", mime_type = "image/png")
        thumbnail = archive.getStream("/Metadata/thumbnail.png")
        thumbnail.write(os.path.join(os.path.basename(__file__), "kitten.png"))
        archive.addRelation(target = "/Metadata/thumbnail.png", file_type = "http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail")