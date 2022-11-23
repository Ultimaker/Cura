
from UM.Tool import Tool
from UM.Scene.Selection import Selection
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Application import Application
from UM.Logger import Logger
from ...extensions.idex.IdexPlugin import IdexPlugin
from cura.Settings.ExtruderManager import ExtruderManager
from .PrintModesLitsener import  PrintModesLitsener
from PyQt6.QtQml import qmlRegisterSingletonType

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("uranium")
from UM.Logger import Logger

from UM.Event import Event


class PrintModesPlugin(Tool):

    def __init__(self):
        super().__init__()
        
        self._model = None
        self._multi_extrusion = False
        self._single_model_selected = False
        self.visibility_handler = None
        Logger.info(f"PrintModesPlugin init")
        self._print_mode = PrintModesLitsener.getInstance()
        Selection.selectionChanged.connect(self.propertyChanged)
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalContainerChanged)
        self._onGlobalContainerChanged()
        Selection.selectionChanged.connect(self._updateEnabled)
        qmlRegisterSingletonType(PrintModesLitsener, "Cura", 1, 1, self.getModeManager, "PrintModeService")
        #qmlRegisterSingletonType(PrintModesLitsener, "Cura", 1, 1, self.getModeManager, "CuraActions")

        Logger.info(f"PrintModesLitsener registered")


    def event(self, event):
        super().event(event)
        if event.type == Event.MousePressEvent and self._controller.getToolsEnabled():
            self.operationStopped.emit(self)
        return False

    def getModeManager(self, *args):
        return self._print_mode

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
        """Enable plugin if we have > 1 nodes selectec,
            if we want to disable it, we must change _single_model_selected to false
               """
        selected_objects = Selection.getAllSelectedObjects()
        if len(selected_objects)> 1:
            self._single_model_selected = True
        elif len(selected_objects) == 1 and selected_objects[0].callDecoration("isGroup"):
            self._single_model_selected = True # Group is selected, so tool needs to be disabled
        else:
            self._single_model_selected = True
        Application.getInstance().getController().toolEnabledChanged.emit(self._plugin_id, self._single_model_selected)


