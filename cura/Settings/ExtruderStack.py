# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.MimeTypeDatabase import MimeType, MimeTypeDatabase
from UM.Settings.ContainerStack import ContainerStack
from UM.Settings.ContainerRegistry import ContainerRegistry

class ExtruderStack(ContainerStack):
    def __init__(self, container_id, *args, **kwargs):
        super().__init__(container_id, *args, **kwargs)

extruder_stack_mime = MimeType(
    name = "application/x-cura-extruderstack",
    comment = "Cura Extruder Stack",
    suffixes = [ "extruder.cfg" ]
)

MimeTypeDatabase.addMimeType(extruder_stack_mime)
ContainerRegistry.addContainerTypeByName(ExtruderStack, "extruder_stack", extruder_stack_mime.name)
