# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import TYPE_CHECKING

from plugins.UM3NetworkPrinting.src.Cloud.CloudOutputDevice import CloudOutputDevice


if TYPE_CHECKING:
    from cura.CuraApplication import CuraApplication
    

##  The cloud output device manager is responsible for using the Ultimaker Cloud APIs to manage remote clusters.
#   Keeping all cloud related logic in this class instead of the UM3OutputDevicePlugin results in more readable code.
class CloudOutputDeviceManager:
    
    def __init__(self, application: "CuraApplication"):
        self._output_device_manager = application.getOutputDeviceManager()
        self._account = application.getCuraAPI().account
        self._getRemoteClusters()
        
        # For testing:
        application.globalContainerStackChanged.connect(self._addCloudOutputDevice)
        
    def _getRemoteClusters(self):
        # TODO: get list of remote clusters and create an output device for each.
        pass
    
    def _addCloudOutputDevice(self):
        device = CloudOutputDevice("xxxx-xxxx-xxxx-xxxx")
        self._output_device_manager.addOutputDevice(device)
        device.connect()
