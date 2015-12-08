# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import Qt, pyqtSlot, QUrl, pyqtSignal

from UM.Application import Application
from UM.Qt.ListModel import ListModel
from UM.Settings.SettingOverrideDecorator import SettingOverrideDecorator

class SettingOverrideModel(ListModel):
    KeyRole = Qt.UserRole + 1
    LabelRole = Qt.UserRole + 2
    DescriptionRole = Qt.UserRole + 3
    ValueRole = Qt.UserRole + 4
    TypeRole = Qt.UserRole + 5
    UnitRole = Qt.UserRole + 6
    ValidRole = Qt.UserRole + 7
    OptionsRole = Qt.UserRole + 8
    WarningDescriptionRole = Qt.UserRole + 9
    ErrorDescriptionRole = Qt.UserRole + 10
    GlobalOnlyRole = Qt.UserRole + 11

    def __init__(self, node, parent = None):
        super().__init__(parent)

        self._ignore_setting_change = None

        self._node = node
        self._node.decoratorsChanged.connect(self._onDecoratorsChanged)
        self._onDecoratorsChanged(None)

        self.addRoleName(self.KeyRole, "key")
        self.addRoleName(self.LabelRole, "label")
        self.addRoleName(self.DescriptionRole, "description")
        self.addRoleName(self.ValueRole,"value")
        self.addRoleName(self.TypeRole, "type")
        self.addRoleName(self.UnitRole, "unit")
        self.addRoleName(self.ValidRole, "valid")
        self.addRoleName(self.OptionsRole, "options")
        self.addRoleName(self.WarningDescriptionRole, "warning_description")
        self.addRoleName(self.ErrorDescriptionRole, "error_description")
        self.addRoleName(self.GlobalOnlyRole, "global_only")

    @pyqtSlot(str, "QVariant")
    def setSettingValue(self, key, value):
        if not self._decorator:
            return

        self._decorator.setSettingValue(key, value)

    def _onDecoratorsChanged(self, node):
        if not self._node.getDecorator(SettingOverrideDecorator):
            self.clear()
            return
        self._decorator = self._node.getDecorator(SettingOverrideDecorator)
        self._decorator.settingAdded.connect(self._onSettingsChanged)
        self._decorator.settingRemoved.connect(self._onSettingsChanged)
        self._decorator.settingValueChanged.connect(self._onSettingValueChanged)
        self._onSettingsChanged()

    def _createOptionsModel(self, options):
        if not options:
            return None

        model = ListModel()
        model.addRoleName(Qt.UserRole + 1, "value")
        model.addRoleName(Qt.UserRole + 2, "name")
        for value, name in options.items():
            model.appendItem({"value": str(value), "name": str(name)})
        return model

    @pyqtSlot()
    def reload(self):
        self.clear()
        #if self._machine_instance:
            #for category in self._machine_instance.getMachineDefinition().getAllCategories():
                #self.appendItem({
                    #"id": category.getKey(),
                    #"name": category.getLabel(),
                    #"icon": category.getIcon(),
                    #"visible": category.isVisible(),
                    #"settings": SettingsFromCategoryModel.SettingsFromCategoryModel(category),
                    #"hiddenValuesCount": category.getHiddenValuesCount()
                #})

    def _onSettingsChanged(self):
        self.clear()

        items = []
        for key, setting in self._decorator.getAllSettings().items():
            value = self._decorator.getSettingValue(key)
            items.append({
                "key": key,
                "label": setting.getLabel(),
                "description": setting.getDescription(),
                "value": str(value),
                "type": setting.getType(),
                "unit": setting.getUnit(),
                "valid": setting.validate(value),
                "options": self._createOptionsModel(setting.getOptions()),
                "warning_description": setting.getWarningDescription(),
                "error_description": setting.getErrorDescription(),
                "global_only": setting.getGlobalOnly()
            })
        items.sort(key = lambda i: i["key"])

        for item in items:
            self.appendItem(item)

    def _onSettingValueChanged(self, setting):
        index = self.find("key", setting.getKey())
        value = self._decorator.getSettingValue(setting.getKey())
        if index != -1:
            self.setProperty(index, "value", str(value))
            self.setProperty(index, "valid", setting.validate(value))
