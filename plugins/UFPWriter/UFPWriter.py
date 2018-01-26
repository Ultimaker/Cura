#Copyright (c) 2018 Ultimaker B.V.
#Cura is released under the terms of the LGPLv3 or higher.

import charon

from UM.Mesh.MeshWriter import MeshWriter #The writer we need to implement.
from UM.PluginRegistry import PluginRegistry #To get the g-code writer.

class UFPWriter(MeshWriter):
    def write(self, stream, nodes, mode = MeshWriter.OutputMode.BinaryMode):
        archive = charon.VirtualFile()
        archive.open(stream, charon.OpenMode.WriteOnly)

        #Store the g-code from the scene.
        archive.addContentType(extension = "gcode", mime_type = "text/x-gcode")
        gcode = archive.getStream("/3D/model.gcode")
        PluginRegistry.getInstance().getPluginObject("GCodeWriter").write(gcode, None)
        archive.addRelation(target = "/3D/model.gcode", file_type = "http://schemas.ultimaker.org/package/2018/relationships/gcode")

        #Store the thumbnail.
        #TODO