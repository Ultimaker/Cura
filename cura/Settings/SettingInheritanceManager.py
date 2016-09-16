from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal
import UM.Settings
from UM.Application import Application
import cura.Settings



class SettingInheritanceManager(QObject):
    def __init__(self, parent = None):
        super().__init__(parent)
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalContainerChanged)
        self._global_container_stack = None
        self._onGlobalContainerChanged()
        self._settings_with_inheritance_warning = []
        self._active_container_stack = None
        cura.Settings.ExtruderManager.getInstance().activeExtruderChanged.connect(self._onActiveExtruderChanged)
        self._onActiveExtruderChanged()

    settingsWithIntheritanceChanged = pyqtSignal()

    @pyqtSlot()
    def test(self):
        pass

    ##  Get the keys of all children settings with an override.
    @pyqtSlot(str, result = "QStringList")
    def getChildrenKeysWithOverride(self, key):
        definitions = self._global_container_stack.getBottom().findDefinitions(key=key)
        if not definitions:
            return
        result = []
        for key in definitions[0].getAllKeys():
            if key in self._settings_with_inheritance_warning:
                result.append(key)
        return result

    @pyqtSlot(str)
    def manualRemoveOverride(self, key):
        if key in self._settings_with_inheritance_warning:
            self._settings_with_inheritance_warning.remove(key)
            self.settingsWithIntheritanceChanged.emit()

    def _onActiveExtruderChanged(self):
        if self._active_container_stack:
            self._active_container_stack.propertyChanged.disconnect(self._onPropertyChanged)

        new_active_stack = cura.Settings.ExtruderManager.getInstance().getActiveExtruderStack()
        if not new_active_stack:
            new_active_stack = self._global_container_stack

        if new_active_stack != self._active_container_stack:
            # Check if changed
            self._active_container_stack = new_active_stack
            self._update()  # Ensure that the settings_with_inheritance_warning list is populated.
            self._active_container_stack.propertyChanged.connect(self._onPropertyChanged)

    def _onPropertyChanged(self, key, property_name):
        if property_name == "value" and self._global_container_stack:

            definitions = self._global_container_stack.getBottom().findDefinitions(key = key)
            if not definitions:
                return

            has_overwritten_inheritance = self._settingIsOverwritingInheritance(key)

            settings_with_inheritance_warning_changed = False

            # Check if the setting needs to be in the list.
            if key not in self._settings_with_inheritance_warning and has_overwritten_inheritance:
                self._settings_with_inheritance_warning.append(key)
                settings_with_inheritance_warning_changed = True
            elif key in self._settings_with_inheritance_warning and not has_overwritten_inheritance:
                self._settings_with_inheritance_warning.remove(key)
                settings_with_inheritance_warning_changed = True

            # Find the topmost parent (Assumed to be a category)
            parent = definitions[0].parent
            while parent.parent is not None:
                parent = parent.parent

            if parent.key not in self._settings_with_inheritance_warning and has_overwritten_inheritance:
                # Category was not in the list yet, so needs to be added now.
                self._settings_with_inheritance_warning.append(parent.key)
                settings_with_inheritance_warning_changed = True

            elif parent.key in self._settings_with_inheritance_warning and not has_overwritten_inheritance:
                # Category was in the list and one of it's settings is not overwritten.
                if not self._recursiveCheck(parent):  # Check if any of it's children have overwritten inheritance.
                    self._settings_with_inheritance_warning.remove(parent.key)
                    settings_with_inheritance_warning_changed = True

            # Emit the signal if there was any change to the list.
            if settings_with_inheritance_warning_changed:
                self.settingsWithIntheritanceChanged.emit()

    def _recursiveCheck(self, definition):
        for child in definition.children:
            if child.key in self._settings_with_inheritance_warning:
                return True
            if child.children:
                if self._recursiveCheck(child):
                    return True
        return False


    @pyqtProperty("QVariantList", notify = settingsWithIntheritanceChanged)
    def settingsWithInheritanceWarning(self):
        return self._settings_with_inheritance_warning

    ##  Check if a setting has an inheritance function that is overwritten
    def _settingIsOverwritingInheritance(self, key):
        has_setting_function = False
        stack = self._active_container_stack
        containers = []

        ## Check if the setting has a user state. If not, it is never overwritten.
        has_user_state = self._active_container_stack.getProperty(key, "state") == UM.Settings.InstanceState.User
        if not has_user_state:
            return False

        ## If a setting is not enabled, don't label it as overwritten (It's never visible anyway).
        if not self._active_container_stack.getProperty(key, "enabled"):
            return False

        ##  Mash all containers for all the stacks together.
        while stack:
            containers.extend(stack.getContainers())
            stack = stack.getNextStack()

        for container in containers:
            try:
                has_setting_function = isinstance(container.getProperty(key, "value"), UM.Settings.SettingFunction)
            except AttributeError:
                continue
            if has_setting_function:
                break  # There is a setting function somehwere, stop looking deeper.

        ## Also check if the top container is not a setting function (this happens if the inheritance is restored).
        return has_setting_function and not isinstance(self._active_container_stack.getTop().getProperty(key, "value"), UM.Settings.SettingFunction)

    def _update(self):
        self._settings_with_inheritance_warning = []  # Reset previous data.

        # Check all setting keys that we know of and see if they are overridden.
        for setting_key in self._global_container_stack.getAllKeys():
            override = self._settingIsOverwritingInheritance(setting_key)
            if override:
                self._settings_with_inheritance_warning.append(setting_key)

        # Check all the categories if any of their children have their inheritance overwritten.
        for category in self._global_container_stack.getBottom().findDefinitions(type = "category"):
            if self._recursiveCheck(category):
                self._settings_with_inheritance_warning.append(category.key)

        # Notify others that things have changed.
        self.settingsWithIntheritanceChanged.emit()

    def _onGlobalContainerChanged(self):
        self._global_container_stack = Application.getInstance().getGlobalContainerStack()

    @staticmethod
    def createSettingInheritanceManager(engine=None, script_engine=None):
        return SettingInheritanceManager()