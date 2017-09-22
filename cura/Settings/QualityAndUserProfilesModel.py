# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.
from UM.Application import Application

from cura.QualityManager import QualityManager
from cura.Settings.ProfilesModel import ProfilesModel
from cura.Settings.ExtruderManager import ExtruderManager

##  QML Model for listing the current list of valid quality and quality changes profiles.
#
class QualityAndUserProfilesModel(ProfilesModel):
    def __init__(self, parent = None):
        super().__init__(parent)

    ##  Fetch the list of containers to display.
    #
    #   See UM.Settings.Models.InstanceContainersModel._fetchInstanceContainers().
    def _fetchInstanceContainers(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if not global_container_stack:
            return []

        # Fetch the list of quality changes.
        quality_manager = QualityManager.getInstance()
        machine_definition = quality_manager.getParentMachineDefinition(global_container_stack.getBottom())
        quality_changes_list = quality_manager.findAllQualityChangesForMachine(machine_definition)

        # Detecting if the machine has multiple extrusion
        multiple_extrusion = False
        # Get the  list of extruders and place the selected extruder at the front of the list.
        extruder_manager = ExtruderManager.getInstance()
        active_extruder = extruder_manager.getActiveExtruderStack()
        extruder_stacks = extruder_manager.getActiveExtruderStacks()
        if active_extruder in extruder_stacks:
            multiple_extrusion = True
            extruder_stacks.remove(active_extruder)
            extruder_stacks = [active_extruder] + extruder_stacks

        # Fetch the list of useable qualities across all extruders.
        # The actual list of quality profiles come from the first extruder in the extruder list.
        quality_list = quality_manager.findAllUsableQualitiesForMachineAndExtruders(global_container_stack,
                                                                                                  extruder_stacks)

        # Filter the quality_change by the list of available quality_types
        quality_type_set = set([x.getMetaDataEntry("quality_type") for x in quality_list])

        if multiple_extrusion:
            # If the printer has multiple extruders then quality changes related to the current extruder are kept
            filtered_quality_changes = [qc for qc in quality_changes_list if qc.getMetaDataEntry("quality_type") in quality_type_set and qc.getMetaDataEntry("extruder") == active_extruder.definition.getId()]
        else:
            # If not, the quality changes of the global stack are selected
            filtered_quality_changes = [qc for qc in quality_changes_list if qc.getMetaDataEntry("quality_type") in quality_type_set]

        return quality_list + filtered_quality_changes
