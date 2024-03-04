# Copyright (c) 2024 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt6.QtCore import Qt

from UM.Logger import Logger
from UM.Settings.SettingDefinition import SettingDefinition
from UM.Qt.ListModel import ListModel


class SpecificSettingsModel(ListModel):
    CategoryRole = Qt.ItemDataRole.UserRole + 1
    LabelRole = Qt.ItemDataRole.UserRole + 2
    ValueRole = Qt.ItemDataRole.UserRole + 3

    def __init__(self, parent = None):
        super().__init__(parent = parent)
        self.addRoleName(self.CategoryRole, "category")
        self.addRoleName(self.LabelRole, "label")
        self.addRoleName(self.ValueRole, "value")

        self._i18n_catalog = None
        self._update()


    def addSettingsFromStack(self, stack, category, settings):
        for setting, value in settings.items():
            unit = stack.getProperty(setting, "unit")

            setting_type = stack.getProperty(setting, "type")
            if setting_type is not None:
                # This is not very good looking, but will do for now
                value = str(SettingDefinition.settingValueToString(setting_type, value)) + " " + str(unit)
            else:
                value = str(value)

            self.appendItem({
                "category": category,
                "label": stack.getProperty(setting, "label"),
                "value": value
            })

    def _update(self):
        Logger.log("d", "Updating {model_class_name}.".format(model_class_name = self.__class__.__name__))
        self.setItems([])
        return
