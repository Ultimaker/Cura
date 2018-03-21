# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, pyqtProperty

from UM.Application import Application
from UM.Extension import Extension
from UM.Logger import Logger
from UM.Message import Message
from UM.i18n import i18nCatalog
from UM.PluginRegistry import PluginRegistry
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator

catalog = i18nCatalog("cura")


SHRINKAGE_THRESHOLD = 0.5
WARNING_SIZE_XY = 150
WARNING_SIZE_Z = 100


class ModelChecker(QObject, Extension):

    needCheckChanged = pyqtSignal()

    def __init__(self):
        super().__init__()

        self._button_view = None
        self._need_checks = False

        self._happy_message = Message(catalog.i18nc(
            "@info:status",
            "The Model Checker did not detect any problems with your model / chosen materials combination."),
            lifetime = 5,
            title = catalog.i18nc("@info:title", "Model Checker"))
        self._caution_message = Message("", #Message text gets set when the message gets shown, to display the models in question.
            lifetime = 0,
            title = catalog.i18nc("@info:title", "Model Checker Warning"))

        Application.getInstance().initializationFinished.connect(self.bindSignals)

    def bindSignals(self):
        Application.getInstance().getMachineManager().rootMaterialChanged.connect(self._onChanged)

    def checkObjectsForShrinkage(self, nodes_to_check):
        material_shrinkage = self.getMaterialShrinkage()

        warning_nodes = []

        # Check node material shrinkage and bounding box size
        for node in nodes_to_check:
            node_extruder_position = node.callDecoration("getActiveExtruderPosition")
            if material_shrinkage[node_extruder_position] > SHRINKAGE_THRESHOLD:
                bbox = node.getBoundingBox()
                if bbox.width >= WARNING_SIZE_XY or bbox.depth >= WARNING_SIZE_XY or bbox.height >= WARNING_SIZE_Z:
                    warning_nodes.append(node)

        return warning_nodes

    def checkAllSliceableNodes(self):
        # Add all sliceable scene nodes to check
        scene = Application.getInstance().getController().getScene()
        nodes_to_check = []
        for node in DepthFirstIterator(scene.getRoot()):
            if node.callDecoration("isSliceable"):
                nodes_to_check.append(node)
        return self.checkObjectsForShrinkage(nodes_to_check)

    ##  Display warning message
    def showWarningMessage(self, warning_nodes):
        self._caution_message.setText(catalog.i18nc(
            "@info:status",
            "Some models may not be printed optimal due to object size and chosen material for models: {model_names}.\n"
            "Tips that may be useful to improve the print quality:\n"
            "1) Use rounded corners\n"
            "2) Turn the fan off (only if the are no tiny details on the model)\n"
            "3) Use a different material").format(model_names = ", ".join([n.getName() for n in warning_nodes])))
        self._caution_message.show()

    def showHappyMessage(self):
        self._happy_message.show()

    ##  Creates the view used by show popup. The view is saved because of the fairly aggressive garbage collection.
    def _createView(self):
        Logger.log("d", "Creating model checker view.")

        # Create the plugin dialog component
        path = os.path.join(PluginRegistry.getInstance().getPluginPath("ModelChecker"), "ModelChecker.qml")
        self._button_view = Application.getInstance().createQmlComponent(path, {"manager": self})

        # The qml is only the button
        Application.getInstance().addAdditionalComponent("jobSpecsButton", self._button_view)

        Logger.log("d", "Model checker view created.")

    def _onChanged(self, *args):
        if self._button_view is None:
            self._createView()
        old_need_checks = self._need_checks
        self._need_checks = self.calculateNeedCheck()
        if old_need_checks != self._need_checks:
            self.needCheckChanged.emit()

    @pyqtSlot()
    def runChecks(self):
        warning_nodes = self.checkAllSliceableNodes()
        if warning_nodes:
            self.showWarningMessage(warning_nodes)
        else:
            self.showHappyMessage()

    def getMaterialShrinkage(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack is None:
            return {}

        material_shrinkage = {}
        # Get all shrinkage values of materials used
        for extruder_position, extruder in global_container_stack.extruders.items():
            shrinkage = extruder.material.getProperty("material_shrinkage_percentage", "value")
            if shrinkage is None:
                shrinkage = 0
            material_shrinkage[extruder_position] = shrinkage
        return material_shrinkage

    @pyqtProperty(bool, notify = needCheckChanged)
    def needCheck(self):
        return self._need_checks

    def calculateNeedCheck(self):
        need_check = False

        for shrinkage in self.getMaterialShrinkage().values():
            if shrinkage > SHRINKAGE_THRESHOLD:
                need_check = True

        return need_check
