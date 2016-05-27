from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal
from UM.Application import Application
from UM.Settings.SettingInstance import SettingInstance
from UM.Logger import Logger

from cura.SettingOverrideDecorator import SettingOverrideDecorator


class PerObjectSettingVisibilityHandler(QObject):
    def __init__(self, parent = None, *args, **kwargs):
        super().__init__(parent = parent, *args, **kwargs)
        self._selected_object_id = None

    visibilityChanged = pyqtSignal()

    def setSelectedObjectId(self, id):
        self._selected_object_id = id
        self.visibilityChanged.emit()

    @pyqtProperty("quint64", fset = setSelectedObjectId)
    def selectedObjectId(self):
        pass

    def setVisible(self, visible):
        node = Application.getInstance().getController().getScene().findObject(self._selected_object_id)
        if not node:
            return
        stack = node.callDecoration("getStack")
        if not stack:
            node.addDecorator(SettingOverrideDecorator())
            stack = node.callDecoration("getStack")

        settings = stack.getTop()
        all_instances = settings.findInstances(**{})
        visibility_changed = False  # Flag to check if at the end the signal needs to be emitted

        # Remove all instances that are not in visibility list
        for instance in all_instances:
            if instance.definition.key not in visible:
                settings.removeInstance(instance.definition.key)
                visibility_changed = True

        # Add all instances that are not added, but are in visiblity list
        for item in visible:
            if not settings.getInstance(item):
                definition_container = Application.getInstance().getGlobalContainerStack().getBottom()
                definitions = definition_container.findDefinitions(key = item)
                if definitions:
                    settings.addInstance(SettingInstance(definitions[0], settings))
                    visibility_changed = True
                else:
                    Logger.log("w", "Unable to add instance (%s) to perobject visibility because we couldn't find the matching definition", item)

        if visibility_changed:
            self.visibilityChanged.emit()
        #settings.addInstance(SettingInstance())

    def getVisible(self):
        visible_settings = set()
        node = Application.getInstance().getController().getScene().findObject(self._selected_object_id)
        if not node:
            return visible_settings

        stack = node.callDecoration("getStack")
        if not stack:
            return visible_settings

        settings = stack.getTop()
        if not settings:
            return visible_settings

        all_instances = settings.findInstances(**{})
        for instance in all_instances:
            visible_settings.add(instance.definition.key)
        return visible_settings

