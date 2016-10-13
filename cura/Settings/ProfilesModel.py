# Copyright (c) 2016 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from UM.Application import Application
from UM.Settings.Models.InstanceContainersModel import InstanceContainersModel

from cura.QualityManager import QualityManager
from cura.Settings.ExtruderManager import ExtruderManager
from cura.Settings.MachineManager import MachineManager

##  QML Model for listing the current list of valid quality profiles.
#
class ProfilesModel(InstanceContainersModel):
    def __init__(self, parent = None):
        super().__init__(parent)

        Application.getInstance().globalContainerStackChanged.connect(self._update)

        Application.getInstance().getMachineManager().activeVariantChanged.connect(self._update)
        Application.getInstance().getMachineManager().activeStackChanged.connect(self._update)
        Application.getInstance().getMachineManager().activeMaterialChanged.connect(self._update)

    ##  Fetch the list of containers to display.
    #
    #   See UM.Settings.Models.InstanceContainersModel._fetchInstanceContainers().
    def _fetchInstanceContainers(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack is None:
            return []

        # Get the  list of extruders and place the selected extruder at the front of the list.
        extruder_manager = ExtruderManager.getInstance()
        active_extruder = extruder_manager.getActiveExtruderStack()
        extruder_stacks = extruder_manager.getActiveExtruderStacks()
        extruder_stacks.remove(active_extruder)
        extruder_stacks = [active_extruder] + extruder_stacks

        # Fetch the list of useable qualities across all extruders.
        # The actual list of quality profiles come from the first extruder in the extruder list.
        return QualityManager.getInstance().findAllUsableQualitiesForMachineAndExtruders(global_container_stack,
                                                                                         extruder_stacks)
