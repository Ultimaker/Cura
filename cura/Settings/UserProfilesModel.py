# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Application import Application
from cura.QualityManager import QualityManager
from cura.Settings.ProfilesModel import ProfilesModel
from cura.Settings.ExtruderManager import ExtruderManager

##  QML Model for listing the current list of valid quality changes profiles.
#
class UserProfilesModel(ProfilesModel):
    def __init__(self, parent = None):
        super().__init__(parent)

        #Need to connect to the metaDataChanged signal of the active materials.
        self.__current_extruders = []
        self.__current_materials = []

        Application.getInstance().getExtruderManager().extrudersChanged.connect(self.__onExtrudersChanged)
        self.__onExtrudersChanged()
        self.__current_materials = [extruder.material for extruder in self.__current_extruders]
        for material in self.__current_materials:
            material.metaDataChanged.connect(self._onContainerChanged)

    ##  Fetch the list of containers to display.
    #
    #   See UM.Settings.Models.InstanceContainersModel._fetchInstanceContainers().
    def _fetchInstanceContainers(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if not global_container_stack:
            return {}, {}

        # Fetch the list of quality changes.
        quality_manager = QualityManager.getInstance()
        machine_definition = quality_manager.getParentMachineDefinition(global_container_stack.definition)
        quality_changes_list = quality_manager.findAllQualityChangesForMachine(machine_definition)

        extruder_manager = ExtruderManager.getInstance()
        active_extruder = extruder_manager.getActiveExtruderStack()
        extruder_stacks = self._getOrderedExtruderStacksList()

        # Fetch the list of usable qualities across all extruders.
        # The actual list of quality profiles come from the first extruder in the extruder list.
        quality_list = quality_manager.findAllUsableQualitiesForMachineAndExtruders(global_container_stack, extruder_stacks)

        # Filter the quality_change by the list of available quality_types
        quality_type_set = set([x.getMetaDataEntry("quality_type") for x in quality_list])

        filtered_quality_changes = {qc.getId():qc for qc in quality_changes_list if
                                    qc.getMetaDataEntry("quality_type") in quality_type_set and
                                    qc.getMetaDataEntry("extruder") is not None and
                                    (qc.getMetaDataEntry("extruder") == active_extruder.definition.getMetaDataEntry("quality_definition") or
                                     qc.getMetaDataEntry("extruder") == active_extruder.definition.getId())}

        return filtered_quality_changes, {} #Only return true profiles for now, no metadata. The quality manager is not able to get only metadata yet.

    ##  Called when a container changed on an extruder stack.
    #
    #   If it's the material we need to connect to the metaDataChanged signal of
    #   that.
    def __onContainerChanged(self, new_container):
        #Careful not to update when a quality or quality changes profile changed!
        #If you then update you're going to have an infinite recursion because the update may change the container.
        if new_container.getMetaDataEntry("type") == "material":
            for material in self.__current_materials:
                material.metaDataChanged.disconnect(self._onContainerChanged)
            self.__current_materials = [extruder.material for extruder in self.__current_extruders]
            for material in self.__current_materials:
                material.metaDataChanged.connect(self._onContainerChanged)

    ##  Called when the current set of extruders change.
    #
    #   This makes sure that we are listening to the signal for when the
    #   materials change.
    def __onExtrudersChanged(self):
        for extruder in self.__current_extruders:
            extruder.containersChanged.disconnect(self.__onContainerChanged)
        self.__current_extruders = Application.getInstance().getExtruderManager().getExtruderStacks()
        for extruder in self.__current_extruders:
            extruder.containersChanged.connect(self.__onContainerChanged)