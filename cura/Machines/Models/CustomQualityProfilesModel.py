# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Application import Application
from UM.Logger import Logger

from cura.Machines.Models.QualityProfilesModel import QualityProfilesModel


class CustomQualityProfilesModel(QualityProfilesModel):

    def _update(self):
        Logger.log("d", "Updating %s ...", self.__class__.__name__)

        active_global_stack = Application.getInstance().getMachineManager().activeMachine
        if active_global_stack is None:
            self.setItems([])
            Logger.log("d", "No active GlobalStack, set %s as empty.", self.__class__.__name__)
            return

        quality_changes_group_dict = self._quality_manager.getQualityChangesGroups(active_global_stack)

        item_list = []
        for key in sorted(quality_changes_group_dict):
            quality_changes_group = quality_changes_group_dict[key]

            item = {"name": quality_changes_group.name,
                    "layer_height": "",
                    "layer_height_without_unit": "",
                    "available": quality_changes_group.is_available,
                    "quality_changes_group": quality_changes_group}

            item_list.append(item)

        self.setItems(item_list)
