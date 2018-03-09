# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import Qt, pyqtProperty

from UM.Qt.ListModel import ListModel


#
# This model is for the Material management page.
#
class MaterialManagementModel(ListModel):
    RootMaterialIdRole = Qt.UserRole + 1
    DisplayNameRole = Qt.UserRole + 2
    BrandRole = Qt.UserRole + 3
    MaterialTypeRole = Qt.UserRole + 4
    ColorNameRole = Qt.UserRole + 5
    ColorCodeRole = Qt.UserRole + 6
    ContainerNodeRole = Qt.UserRole + 7
    ContainerIdRole = Qt.UserRole + 8

    DescriptionRole = Qt.UserRole + 9
    AdhesionInfoRole = Qt.UserRole + 10
    ApproximateDiameterRole = Qt.UserRole + 11
    GuidRole = Qt.UserRole + 12
    DensityRole = Qt.UserRole + 13
    DiameterRole = Qt.UserRole + 14
    IsReadOnlyRole = Qt.UserRole + 15

    def __init__(self, parent = None):
        super().__init__(parent)

        self.addRoleName(self.RootMaterialIdRole, "root_material_id")
        self.addRoleName(self.DisplayNameRole, "name")
        self.addRoleName(self.BrandRole, "brand")
        self.addRoleName(self.MaterialTypeRole, "material")
        self.addRoleName(self.ColorNameRole, "color_name")
        self.addRoleName(self.ColorCodeRole, "color_code")
        self.addRoleName(self.ContainerNodeRole, "container_node")
        self.addRoleName(self.ContainerIdRole, "container_id")

        self.addRoleName(self.DescriptionRole, "description")
        self.addRoleName(self.AdhesionInfoRole, "adhesion_info")
        self.addRoleName(self.ApproximateDiameterRole, "approximate_diameter")
        self.addRoleName(self.GuidRole, "guid")
        self.addRoleName(self.DensityRole, "density")
        self.addRoleName(self.DiameterRole, "diameter")
        self.addRoleName(self.IsReadOnlyRole, "is_read_only")

        from cura.CuraApplication import CuraApplication
        self._container_registry = CuraApplication.getInstance().getContainerRegistry()
        self._machine_manager = CuraApplication.getInstance().getMachineManager()
        self._extruder_manager = CuraApplication.getInstance().getExtruderManager()
        self._material_manager = CuraApplication.getInstance().getMaterialManager()

        self._machine_manager.globalContainerChanged.connect(self._update)
        self._extruder_manager.activeExtruderChanged.connect(self._update)
        self._material_manager.materialsUpdated.connect(self._update)

        self._update()

    def _update(self):
        global_stack = self._machine_manager.activeMachine
        if global_stack is None:
            self.setItems([])
            return
        active_extruder_stack = self._machine_manager.activeStack

        available_material_dict = self._material_manager.getAvailableMaterialsForMachineExtruder(global_stack,
                                                                                                 active_extruder_stack)
        if available_material_dict is None:
            self.setItems([])
            return

        material_list = []
        for root_material_id, container_node in available_material_dict.items():
            keys_to_fetch = ("name",
                             "brand",
                             "material",
                             "color_name",
                             "color_code",
                             "description",
                             "adhesion_info",
                             "approximate_diameter",)

            item = {"root_material_id": container_node.metadata["base_file"],
                    "container_node": container_node,
                    "guid": container_node.metadata["GUID"],
                    "container_id": container_node.metadata["id"],
                    "density": container_node.metadata.get("properties", {}).get("density", ""),
                    "diameter": container_node.metadata.get("properties", {}).get("diameter", ""),
                    "is_read_only": self._container_registry.isReadOnly(container_node.metadata["id"]),
                    }

            for key in keys_to_fetch:
                item[key] = container_node.metadata.get(key, "")

            material_list.append(item)

        material_list = sorted(material_list, key = lambda k: (k["brand"].upper(), k["name"].upper()))
        self.setItems(material_list)
