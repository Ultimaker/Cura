# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Logger import Logger
from UM.Tool import Tool
from UM.Scene.Selection import Selection
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Application import Application
from cura.Settings.SettingOverrideDecorator import SettingOverrideDecorator
from cura.Settings.ExtruderManager import ExtruderManager
from UM.Settings.SettingInstance import SettingInstance
from UM.Event import Event


class PerObjectSettingsTool(Tool):
    """This tool allows the user to add & change settings per node in the scene.
    
    The settings per object are kept in a ContainerStack, which is linked to a node by decorator.
    """
    def __init__(self):
        super().__init__()
        self._model = None

        self.setExposedProperties("SelectedObjectId", "ContainerID", "SelectedActiveExtruder", "MeshType")

        self._multi_extrusion = False
        self._single_model_selected = False
        self.visibility_handler = None

        Selection.selectionChanged.connect(self.propertyChanged)
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalContainerChanged)
        self._onGlobalContainerChanged()
        Selection.selectionChanged.connect(self._updateEnabled)

    def event(self, event):
        super().event(event)
        if event.type == Event.MousePressEvent and self._controller.getToolsEnabled():
            self.operationStopped.emit(self)
        return False

    def getSelectedObjectId(self):
        selected_object = Selection.getSelectedObject(0)
        selected_object_id = id(selected_object)
        return selected_object_id

    def getContainerID(self):
        selected_object = Selection.getSelectedObject(0)
        try:
            return selected_object.callDecoration("getStack").getId()
        except AttributeError:
            return ""

    def getSelectedActiveExtruder(self):
        """Gets the active extruder of the currently selected object.
        
        :return: The active extruder of the currently selected object.
        """

        selected_object = Selection.getSelectedObject(0)
        return selected_object.callDecoration("getActiveExtruder")

    def setSelectedActiveExtruder(self, extruder_stack_id):
        """Changes the active extruder of the currently selected object.
        
        :param extruder_stack_id: The ID of the extruder to print the currently
        selected object with.
        """

        selected_object = Selection.getSelectedObject(0)
        stack = selected_object.callDecoration("getStack") #Don't try to get the active extruder since it may be None anyway.
        if not stack:
            selected_object.addDecorator(SettingOverrideDecorator())
        selected_object.callDecoration("setActiveExtruder", extruder_stack_id)

    def setMeshType(self, mesh_type: str) -> bool:
        """Returns True when the mesh_type was changed, False when current mesh_type == mesh_type"""

        old_mesh_type = self.getMeshType()
        if old_mesh_type == mesh_type:
            return False

        selected_object = Selection.getSelectedObject(0)
        if selected_object is None:
            Logger.log("w", "Tried setting the mesh type of the selected object, but no object was selected")
            return False

        stack = selected_object.callDecoration("getStack") #Don't try to get the active extruder since it may be None anyway.
        if not stack:
            selected_object.addDecorator(SettingOverrideDecorator())
            stack = selected_object.callDecoration("getStack")

        settings_visibility_changed = False
        settings = stack.getTop()
        for property_key in ["infill_mesh", "cutting_mesh", "support_mesh", "anti_overhang_mesh"]:
            if property_key != mesh_type:
                if settings.getInstance(property_key):
                    settings.removeInstance(property_key)
            else:
                if not (settings.getInstance(property_key) and settings.getProperty(property_key, "value")):
                    definition = stack.getSettingDefinition(property_key)
                    new_instance = SettingInstance(definition, settings)
                    new_instance.setProperty("value", True)
                    new_instance.resetState()  # Ensure that the state is not seen as a user state.
                    settings.addInstance(new_instance)

        for property_key in ["top_bottom_thickness", "wall_thickness"]:
            if mesh_type == "infill_mesh":
                if settings.getInstance(property_key) is None:
                    definition = stack.getSettingDefinition(property_key)
                    new_instance = SettingInstance(definition, settings)
                    new_instance.setProperty("value", 0)
                    new_instance.resetState()  # Ensure that the state is not seen as a user state.
                    settings.addInstance(new_instance)
                    settings_visibility_changed = True

            elif old_mesh_type == "infill_mesh" and settings.getInstance(property_key) and settings.getProperty(property_key, "value") == 0:
                settings.removeInstance(property_key)
                settings_visibility_changed = True

        if settings_visibility_changed:
            self.visibility_handler.forceVisibilityChanged()

        self.propertyChanged.emit()
        return True

    def getMeshType(self):
        selected_object = Selection.getSelectedObject(0)
        stack = selected_object.callDecoration("getStack") #Don't try to get the active extruder since it may be None anyway.
        if not stack:
            return ""

        settings = stack.getTop()
        for property_key in ["infill_mesh", "cutting_mesh", "support_mesh", "anti_overhang_mesh"]:
            if settings.getInstance(property_key) and settings.getProperty(property_key, "value"):
                return property_key

        return ""

    def _onGlobalContainerChanged(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:

            # used for enabling or disabling per extruder settings per object
            self._multi_extrusion = global_container_stack.getProperty("machine_extruder_count", "value") > 1

            extruder_stack = ExtruderManager.getInstance().getExtruderStack(0)

            if extruder_stack:
                root_node = Application.getInstance().getController().getScene().getRoot()
                for node in DepthFirstIterator(root_node):
                    new_stack_id = extruder_stack.getId()
                    # Get position of old extruder stack for this node
                    old_extruder_pos = node.callDecoration("getActiveExtruderPosition")
                    if old_extruder_pos is not None:
                        # Fetch current (new) extruder stack at position
                        new_stack = ExtruderManager.getInstance().getExtruderStack(old_extruder_pos)
                        if new_stack:
                            new_stack_id = new_stack.getId()
                    node.callDecoration("setActiveExtruder", new_stack_id)

                self._updateEnabled()

    def _updateEnabled(self):
        selected_objects = Selection.getAllSelectedObjects()
        if len(selected_objects)> 1:
            self._single_model_selected = False
        elif len(selected_objects) == 1 and selected_objects[0].callDecoration("isGroup"):
            self._single_model_selected = False # Group is selected, so tool needs to be disabled
        else:
            self._single_model_selected = True
        Application.getInstance().getController().toolEnabledChanged.emit(self._plugin_id, self._single_model_selected)
