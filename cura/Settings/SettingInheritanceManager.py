from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal
import UM.Settings
from UM.Signal import signalemitter
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

            # Find the topmost parent & add that to the list as well
            parent = definitions[0].parent
            while parent.parent is not None:
                parent = parent.parent

            if parent.key not in self._settings_with_inheritance_warning and has_overwritten_inheritance:
                self._settings_with_inheritance_warning.append(parent.key)
                settings_with_inheritance_warning_changed = True

            elif parent.key in self._settings_with_inheritance_warning and not has_overwritten_inheritance:
                if not self._recursiveCheck(parent):
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

    # Check if a setting is being overwritten.
    def _settingIsOverwritingInheritance(self, key):
        has_setting_function = False
        stack = self._active_container_stack
        containers = []

        has_user_state = self._active_container_stack.getProperty(key, "state") == UM.Settings.InstanceState.User
        if not has_user_state:
            return False
        while stack:
            containers.extend(stack.getContainers())
            stack = stack.getNextStack()

        for container in containers:
            try:
                has_setting_function = isinstance(container.getProperty(key, "value"), UM.Settings.SettingFunction)
            except AttributeError:
                continue
            if has_setting_function:
                break
        return has_setting_function and not isinstance(self._active_container_stack.getTop().getProperty(key, "value"), UM.Settings.SettingFunction)

    def _update(self):
        self._settings_with_inheritance_warning = []
        for setting_key in self._global_container_stack.getAllKeys():
            override = self._settingIsOverwritingInheritance(setting_key)
            if override:
                self._settings_with_inheritance_warning.append(setting_key)
            definitions = self._global_container_stack.getBottom().findDefinitions(key=setting_key)
            parent = definitions[0].parent
            if parent is not None and override:
                while parent.parent is not None:
                    parent = parent.parent
                # Add the topmost container as well (if this wasn't already the case)
                if parent.key not in self._settings_with_inheritance_warning:
                    self._settings_with_inheritance_warning.append(parent.key)
        self.settingsWithIntheritanceChanged.emit()

    def _onGlobalContainerChanged(self):
        self._global_container_stack = Application.getInstance().getGlobalContainerStack()

    @staticmethod
    def createSettingInheritanceManager(engine=None, script_engine=None):
        return SettingInheritanceManager()