# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Signal import signalemitter

from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.MimeTypeDatabase import MimeType, MimeTypeDatabase


##  A container for not supported profiles.
#
#
@signalemitter
class NotSupportedProfileContainer(InstanceContainer):

    def __init__(self, container_id: str, machine_id: str, material_id: str, *args, **kwargs):
        super().__init__(container_id, *args, **kwargs)

        # self._id = str(container_id)    # type: str
        # self._name = "Not supported"    # type: str

        self.setMetaData({
            "setting_version": 3,
            "supported": False,
            "type": "quality",
            "weight": "0",
            "material": material_id
        })

        # register this container
        ContainerRegistry.getInstance().addContainer(self)

        # set printer definition
        definition = ContainerRegistry.getInstance().findDefinitionContainers(id = machine_id)
        self.setDefinition(definition[0])


# register the container mime type
not_support_instance_mime = MimeType(
    name = "application/x-cura-notsupportedinstancecontainer",
    comment = "Cura Not Supported Instance Container",
    suffixes = []
)

MimeTypeDatabase.addMimeType(not_support_instance_mime)
ContainerRegistry.addContainerTypeByName(NotSupportedProfileContainer, "not_supported_instance", not_support_instance_mime.name)
