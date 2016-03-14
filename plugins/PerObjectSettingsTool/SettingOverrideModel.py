# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import Qt, pyqtSlot, QUrl

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

        self._activeProfile = Application.getInstance().getMachineManager().getWorkingProfile() #To be able to get notified when a setting changes.
        self._activeProfile.settingValueChanged.connect(self._onProfileSettingValueChanged)
        Application.getInstance().getMachineManager().activeProfileChanged.connect(self._onProfileChanged)

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

    ##  Updates the active profile in this model if the active profile is
    #   changed.
    #
    #   This links the settingValueChanged of the new profile to this model's
    #   _onSettingValueChanged function, so that it properly listens to those
    #   events again.
    def _onProfileChanged(self):
        if self._activeProfile: #Unlink from the old profile.
            self._activeProfile.settingValueChanged.disconnect(self._onProfileSettingValueChanged)
        old_profile = self._activeProfile
        self._activeProfile = Application.getInstance().getMachineManager().getWorkingProfile()
        self._activeProfile.settingValueChanged.connect(self._onProfileSettingValueChanged) #Re-link to the new profile.
        for setting_name in old_profile.getChangedSettings().keys(): #Update all changed settings in the old and new profiles.
            self._onProfileSettingValueChanged(setting_name)
        for setting_name in self._activeProfile.getChangedSettings().keys():
            self._onProfileSettingValueChanged(setting_name)

    ##  Updates the global_only property of a setting once a setting value
    #   changes.
    #
    #   This method should only get called on settings that are dependent on the
    #   changed setting.
    #
    #   \param setting_name The setting that needs to be updated.
    def _onProfileSettingValueChanged(self, setting_name):
        index = self.find("key", setting_name)
        if index != -1:
            self.setProperty(index, "global_only", Application.getInstance().getMachineManager().getActiveMachineInstance().getMachineDefinition().getSetting(setting_name).getGlobalOnly())

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
            self.setProperty(index, "global_only", setting.getGlobalOnly())