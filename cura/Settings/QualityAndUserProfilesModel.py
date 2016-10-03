# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.
from UM.Application import Application
from UM.Settings.ContainerRegistry import ContainerRegistry

from cura.QualityManager import QualityManager
from cura.Settings.ProfilesModel import ProfilesModel

##  QML Model for listing the current list of valid quality and quality changes profiles.
#
class QualityAndUserProfilesModel(ProfilesModel):
    def __init__(self, parent = None):
        super().__init__(parent)

    ##  Fetch the list of containers to display.
    #
    #   See UM.Settings.Models.InstanceContainersModel._fetchInstanceContainers().
    def _fetchInstanceContainers(self):
        # Fetch the list of qualities
        quality_list = super()._fetchInstanceContainers()

        # Fetch the list of quality changes.
        quality_manager = QualityManager.getInstance()
        application = Application.getInstance()

        machine_definition = quality_manager.getParentMachineDefinition(application.getGlobalContainerStack().getBottom())
        if machine_definition.getMetaDataEntry("has_machine_quality"):
            definition_id = machine_definition.getId()
        else:
            definition_id = "fdmprinter"

        filter_dict = { "type": "quality_changes", "extruder": None, "definition": definition_id }
        quality_changes_list = ContainerRegistry.getInstance().findInstanceContainers(**filter_dict)

        return quality_list + quality_changes_list
