# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

# TODO?: documentation

from typing import Optional, Dict, cast

from PyQt6.QtCore import Qt, QObject, pyqtSlot, pyqtProperty, pyqtSignal

from UM.Qt.ListModel import ListModel
from UM.Settings.ContainerStack import ContainerStack
from UM.i18n import i18nCatalog
from UM.Util import parseBool

from cura.Settings.CuraContainerRegistry import CuraContainerRegistry
from cura.Settings.ExtruderStack import ExtruderStack


class CompatibleMachineModel(ListModel):
    NameRole = Qt.ItemDataRole.UserRole + 1
    IdRole = Qt.ItemDataRole.UserRole + 2
    ExtrudersRole = Qt.ItemDataRole.UserRole + 3

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

        self._catalog = i18nCatalog("cura")

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.IdRole, "id")
        self.addRoleName(self.ExtrudersRole, "extruders")

        self._update()

        from cura.CuraApplication import CuraApplication
        machine_manager = CuraApplication.getInstance().getMachineManager()
        machine_manager.globalContainerChanged.connect(self._update)

    def _update(self) -> None:
        self.clear()

        from cura.CuraApplication import CuraApplication
        machine_manager = CuraApplication.getInstance().getMachineManager()

        # Need  to loop over the output-devices, not the stacks, since we need all applicable configurations, not just the current loaded one.
        for output_device in machine_manager.printerOutputDevices:
            for printer in output_device.printers:
                extruder_configs = dict()

                # initialize & add current active material:
                for extruder in printer.extruders:
                    materials = [] if not extruder.activeMaterial else [{
                            "brand": extruder.activeMaterial.brand,
                            "name": extruder.activeMaterial.name,
                            "hexcolor": extruder.activeMaterial.color
                        }]
                    extruder_configs[extruder.getPosition()] = {
                        "position": extruder.getPosition(),
                        "core": extruder.hotendID,
                        "materials": materials
                    }

                # add currently inactive, but possible materials:
                for configuration in printer.availableConfigurations:
                    print("    CONFIG !")
                    for extruder in configuration.extruderConfigurations:

                        if not extruder.position in extruder_configs:
                            # TODO: log -- all extruders should be present in the init round, regardless of if a material was active
                            continue

                        extruder_configs[extruder.position]["materials"].append({
                            "brand": extruder.material.brand,
                            "name": extruder.material.name,
                            "hexcolor": extruder.material.color
                        })

                self.appendItem({
                    "name": printer.name,
                    "id": printer.uniqueName,
                    "extruders": [extruder for extruder in extruder_configs.values()]
                })

        # TODO: Handle 0 compatible machines -> option to close window? Message in card? (remember  the design has a refresh button!)
