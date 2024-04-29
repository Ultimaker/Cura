# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional

from PyQt6.QtCore import Qt, QObject, pyqtSlot, pyqtProperty, pyqtSignal

from UM.Logger import Logger
from UM.Qt.ListModel import ListModel
from UM.i18n import i18nCatalog


class CompatibleMachineModel(ListModel):
    NameRole = Qt.ItemDataRole.UserRole + 1
    UniqueIdRole = Qt.ItemDataRole.UserRole + 2
    ExtrudersRole = Qt.ItemDataRole.UserRole + 3

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

        self._catalog = i18nCatalog("cura")

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.UniqueIdRole, "unique_id")
        self.addRoleName(self.ExtrudersRole, "extruders")

        self._update()

        from cura.CuraApplication import CuraApplication
        machine_manager = CuraApplication.getInstance().getMachineManager()
        machine_manager.globalContainerChanged.connect(self._update)
        machine_manager.outputDevicesChanged.connect(self._update)

    @pyqtSlot()
    def forceUpdate(self):
        self._update()

    def _update(self) -> None:
        self.clear()

        def _makeMaterial(brand, name, color):
            if name.lower() in ["", "empty"]:
                return {"brand": "", "name": "(empty)", "hexcolor": "#ffffff"}
            else:
                return {"brand": brand, "name": name, "hexcolor": color}

        from cura.CuraApplication import CuraApplication
        machine_manager = CuraApplication.getInstance().getMachineManager()

        # Loop over the output-devices, not the stacks; need all applicable configurations, not just the current loaded one.
        for output_device in machine_manager.printerOutputDevices:
            for printer in output_device.printers:
                extruder_configs = dict()
                # If the printer name already exist in the queue skip it
                if printer.name in [item["name"] for item in self.items]:
                    continue

                # initialize & add current active material:
                for extruder in printer.extruders:
                    if not extruder.activeMaterial:
                        continue
                    materials = [_makeMaterial(
                        extruder.activeMaterial.brand, extruder.activeMaterial.name, extruder.activeMaterial.color)]
                    extruder_configs[extruder.getPosition()] = {
                        "position": extruder.getPosition(),
                        "core": extruder.hotendID,
                        "materials": materials
                    }

                # add currently inactive, but possible materials:
                for configuration in printer.availableConfigurations:
                    for extruder in configuration.extruderConfigurations:
                        if not extruder.position in extruder_configs:
                            Logger.log("w", f"No active extruder for position {extruder.position}.")
                            continue

                        entry = _makeMaterial(extruder.material.brand, extruder.material.name, extruder.material.color)
                        if entry not in extruder_configs[extruder.position]["materials"]:
                            extruder_configs[extruder.position]["materials"].append(entry)

                if any([len(extruder["materials"]) > 0 for extruder in extruder_configs.values()]):
                    self.appendItem({
                        "name": printer.name,
                        "unique_id": printer.name,  # <- Can assume the cloud doesn't have duplicate names?
                        "extruders": list(extruder_configs.values())
                    })
