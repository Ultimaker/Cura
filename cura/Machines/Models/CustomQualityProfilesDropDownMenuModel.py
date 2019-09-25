# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Logger import Logger

import cura.CuraApplication  # Imported this way to prevent circular references.
from cura.Machines.ContainerTree import ContainerTree
from cura.Machines.Models.QualityProfilesDropDownMenuModel import QualityProfilesDropDownMenuModel


##  This model is used for the custom profile items in the profile drop down
#   menu.
class CustomQualityProfilesDropDownMenuModel(QualityProfilesDropDownMenuModel):

    def _update(self) -> None:
        Logger.log("d", "Updating {model_class_name}.".format(model_class_name = self.__class__.__name__))

        active_global_stack = cura.CuraApplication.CuraApplication.getInstance().getMachineManager().activeMachine
        if active_global_stack is None:
            self.setItems([])
            Logger.log("d", "No active GlobalStack, set %s as empty.", self.__class__.__name__)
            return

        quality_changes_list = ContainerTree.getInstance().getCurrentQualityChangesGroups()

        item_list = []
        for quality_changes_group in sorted(quality_changes_list, key = lambda qgc: qgc.name.lower()):
            item = {"name": quality_changes_group.name,
                    "layer_height": "",
                    "layer_height_without_unit": "",
                    "available": quality_changes_group.is_available,
                    "quality_changes_group": quality_changes_group}

            item_list.append(item)

        self.setItems(item_list)
