# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import Qt

from UM.Qt.ListModel import ListModel


class QualityManagementModel(ListModel):
    NameRole = Qt.UserRole + 1
    IsReadOnlyRole = Qt.UserRole + 2
    QualityGroupRole = Qt.UserRole + 3
    QualityChangesGroupRole = Qt.UserRole + 4

    def __init__(self, parent = None):
        super().__init__(parent)

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.IsReadOnlyRole, "is_read_only")
        self.addRoleName(self.QualityGroupRole, "quality_group")
        self.addRoleName(self.QualityChangesGroupRole, "quality_changes_group")

        from cura.CuraApplication import CuraApplication
        self._container_registry = CuraApplication.getInstance().getContainerRegistry()
        self._machine_manager = CuraApplication.getInstance().getMachineManager()
        self._extruder_manager = CuraApplication.getInstance().getExtruderManager()
        self._quality_manager = CuraApplication.getInstance()._quality_manager

        self._machine_manager.globalContainerChanged.connect(self._update)
        #self._quality_manager.materialsUpdated.connect(self._update)  # TODO

        self._update()

    def _update(self):
        global_stack = self._machine_manager._global_container_stack

        quality_group_dict = self._quality_manager.getQualityGroups(global_stack)
        quality_changes_group_dict = self._quality_manager.getQualityChangesGroups(global_stack)

        available_quality_types = set(qt for qt, qg in quality_group_dict.items() if qg.is_available)
        if not available_quality_types and not quality_changes_group_dict:
            # Nothing to show
            self.setItems([])
            return

        item_list = []
        # Create quality group items
        for quality_group in quality_group_dict.values():
            if not quality_group.is_available:
                continue

            item = {"name": quality_group.name,
                    "is_read_only": True,
                    "quality_group": quality_group,
                    "quality_changes_group": None}
            item_list.append(item)
        # Sort by quality names
        item_list = sorted(item_list, key = lambda x: x["name"])

        # Create quality_changes group items
        quality_changes_item_list = []
        for quality_changes_group in quality_changes_group_dict.values():
            if quality_changes_group.quality_type not in available_quality_types:
                continue
            quality_group = quality_group_dict[quality_changes_group.quality_type]
            item = {"name": quality_changes_group.name,
                    "is_read_only": False,
                    "quality_group": quality_group,
                    "quality_changes_group": quality_changes_group}
            quality_changes_item_list.append(item)

        # Sort quality_changes items by names and append to the item list
        quality_changes_item_list = sorted(quality_changes_item_list, key = lambda x: x["name"])
        item_list += quality_changes_item_list

        self.setItems(item_list)
