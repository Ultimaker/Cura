# Copyright (c) 2024 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt6.QtCore import Qt, pyqtSignal

from UM import i18nCatalog
from UM.Logger import Logger
from UM.Settings.SettingDefinition import SettingDefinition
from UM.Qt.ListModel import ListModel

from cura.CuraApplication import CuraApplication


class SpecificSettingsModel(ListModel):
    CategoryRole = Qt.ItemDataRole.UserRole + 1
    LabelRole = Qt.ItemDataRole.UserRole + 2
    ValueRole = Qt.ItemDataRole.UserRole + 3

    def __init__(self, parent = None):
        super().__init__(parent = parent)
        self.addRoleName(self.CategoryRole, "category")
        self.addRoleName(self.LabelRole, "label")
        self.addRoleName(self.ValueRole, "value")

        self._settings_catalog = i18nCatalog("fdmprinter.def.json")
        self._update()

    modelChanged = pyqtSignal()


    def addSettingsFromStack(self, stack, category, settings):
        for setting, value in settings.items():
            unit = stack.getProperty(setting, "unit")

            setting_type = stack.getProperty(setting, "type")
            if setting_type in ("enum", "extruder", "optional_extruder"):
                value = CuraApplication.getInstance().getCuraAPI().interface.settings.getSettingDisplayValue(
                    setting, value, stack, self._settings_catalog
                )
            elif setting_type is not None:
                value = str(SettingDefinition.settingValueToString(setting_type, value))
                if unit:
                    value += " " + str(unit)
            else:
                value = str(value)

            label_msgctxt = f"{str(setting)} label"
            label_msgid = stack.getProperty(setting, "label")
            label = self._settings_catalog.i18nc(label_msgctxt, label_msgid)

            self.appendItem({
                "category": category,
                "label": label,
                "value": value
            })
        self.modelChanged.emit()

    def _update(self):
        Logger.debug(f"Updating {self.__class__.__name__}")
        self.setItems([])
        self.modelChanged.emit()
        return
