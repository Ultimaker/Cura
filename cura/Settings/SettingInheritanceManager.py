from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty
import UM.Settings
from UM.Application import Application
import cura.Settings

class SettingInheritanceManager(QObject):
    def __init__(self, parent = None):
        super().__init__(parent)
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalContainerChanged)
        self._global_container_stack = None
        self._onGlobalContainerChanged()

        self._active_container_stack = None
        cura.Settings.ExtruderManager.getInstance().activeExtruderChanged.connect(self._onActiveExtruderChanged)
        self._onActiveExtruderChanged()
        pass

    @pyqtSlot()
    def test(self):
        print("test!")

    def _onActiveExtruderChanged(self):
        if self._active_container_stack:
            self._active_container_stack.propertyChanged.disconnect(self._onPropertyChanged)

        new_active_stack = cura.Settings.ExtruderManager.getInstance().getActiveExtruderStack()
        if not new_active_stack:
            new_active_stack = self._global_container_stack

        if new_active_stack != self._active_container_stack:
            # Check if changed
            self._active_container_stack = new_active_stack
            self._active_container_stack.propertyChanged.connect(self._onPropertyChanged)

    def _onPropertyChanged(self, key, property_name):
        if property_name == "value" and self._global_container_stack:

            definitions = self._global_container_stack.getBottom().findDefinitions(key = key)
            if not definitions:
                return

            # Pseudo code;
            # Check if the property change caused a inheritance warning to trigger.
            pass  # We need to do sum maaagic

    # Check if a setting is being overwritten.
    def _settingIsOverwritingInheritance(self, key):
        has_setting_function = False
        stack = self._active_container_stack
        containers = []
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
        pass

    def _onGlobalContainerChanged(self):
        self._global_container_stack = Application.getInstance().getGlobalContainerStack()

    @staticmethod
    def createSettingInheritanceManager(engine=None, script_engine=None):
        return SettingInheritanceManager()