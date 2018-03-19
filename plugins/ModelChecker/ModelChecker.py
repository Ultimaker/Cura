# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QTimer
from cura.Scene.CuraSceneNode import CuraSceneNode

from UM.Application import Application
from UM.Extension import Extension
from UM.Message import Message
from UM.i18n import i18nCatalog

catalog = i18nCatalog("cura")


SHRINKAGE_THRESHOLD = 0.5
WARNING_SIZE_XY = 150
WARNING_SIZE_Z = 100

MESSAGE_LIFETIME = 10


class ModelChecker(Extension):
    def __init__(self):
        super().__init__()

        self._update_timer = QTimer()
        self._update_timer.setInterval(5000)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self.checkObjects)

        self._nodes_to_check = set()

        self._warning_model_names = set()  # Collect the names of models so we show the next warning with timeout

        ## Reacting to an event. ##
        Application.getInstance().getController().getScene().sceneChanged.connect(self._onSceneChanged)

    def checkObjects(self):
        warning_nodes = []
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        material_shrinkage = {}
        need_check = False

        # Get all shrinkage values of materials used
        for extruder_position, extruder in global_container_stack.extruders.items():
            shrinkage = extruder.material.getProperty("material_shrinkage_ratio_percentage", "value")
            if shrinkage is None:
                shrinkage = 0
            if shrinkage > SHRINKAGE_THRESHOLD:
                need_check = True
            material_shrinkage[extruder_position] = shrinkage

        # Check if we can bail out fast
        if not need_check:
            return

        # Check node material shrinkage and bounding box size
        for node in self._nodes_to_check:
            node_extruder_position = node.callDecoration("getActiveExtruderPosition")
            if material_shrinkage[node_extruder_position] > SHRINKAGE_THRESHOLD:
                bbox = node.getBoundingBox()
                if bbox.width >= WARNING_SIZE_XY or bbox.depth >= WARNING_SIZE_XY or bbox.height >= WARNING_SIZE_Z:
                    warning_nodes.append(node)

        # Display warning message
        if warning_nodes:
            message_lifetime = MESSAGE_LIFETIME
            for node in warning_nodes:
                if node.getName() not in self._warning_model_names:
                    message_lifetime = 0  # infinite
                    self._warning_model_names.add(node.getName())
            caution_message = Message(catalog.i18nc(
                "@info:warning",
                "Some models may not be printed optimal due to object size and material chosen [%s].\n" 
                "Tips that may be useful to improve the print quality:\n" 
                "1) Use rounded corners\n" 
                "2) Turn the fan off (only if the are no tiny details on the model)\n" 
                "3) Use a different material") % ", ".join([n.getName() for n in warning_nodes]),
                lifetime = message_lifetime,
                title = catalog.i18nc("@info:title", "Model Warning"))
            caution_message.show()

    def _onSceneChanged(self, source):
        if isinstance(source, CuraSceneNode) and source.callDecoration("isSliceable"):
            self._nodes_to_check.add(source)
            self._update_timer.start()
