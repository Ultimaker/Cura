# Copyright (c) 2026 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Generator, Set, Dict

from PyQt6.QtCore import QObject, pyqtSignal

from ModelChecker import OverhangChecker
from UM import i18nCatalog
from UM.Application import Application
from UM.Job import Job
from UM.Message import Message
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Signal import Signal

catalog = i18nCatalog("cura")


class ModelCheckerJob(Job):
    def __init__(self, caution_message: Message, do_overhangs: bool) -> None:
        super().__init__()
        self.needsRetry = Signal()

        self._caution_message = caution_message
        self._do_overhangs = do_overhangs
        self._warnings = {}

    def getWarnings(self) -> Dict[str, bool]:
        # NOTE: A value _not_ in the dictionary means 'no tested', rather than 'no warning for that value'.
        #       This means that it can be used in a 'dict.update' call in the caller.
        return self._warnings

    def run(self) -> None:
        self._warnings = {}
        self._caution_message.getActions().clear()

        danger_shrinkage = self._checkObjectsForShrinkage()
        self._warnings["shrinkage"] = danger_shrinkage

        overhangs = False
        if self._do_overhangs:
            overhangs = self._checkForOverhangs()
            self._warnings["overhangs"] = overhangs

        if any((danger_shrinkage, overhangs,)):
            self._caution_message.show()  # Already show the warnings, regardless of the state of the button.

        self.finished.emit(self)

    def _getMaterialShrinkage(self) -> float:
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack is None:
            return 100
        return global_container_stack.getProperty("material_shrinkage_percentage", "value")

    def _sliceableNodes(self) -> Generator:
        # Add all sliceable scene nodes to check
        scene = Application.getInstance().getController().getScene()
        for node in DepthFirstIterator(scene.getRoot()):
            if node.callDecoration("isSliceable"):
                yield node

    def _checkObjectsForShrinkage(self) -> bool:
        shrinkage_threshold = 100.5 #From what shrinkage percentage a warning will be issued about the model size.
        warning_size_xy = 150 #The horizontal size of a model that would be too large when dealing with shrinking materials.
        warning_size_z = 100 #The vertical size of a model that would be too large when dealing with shrinking materials.

        # This function can be triggered in the middle of a machine change, so do not proceed if the machine change
        # has not done yet.
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack is None:
            return False

        material_shrinkage = self._getMaterialShrinkage()

        warning_nodes = []

        # Check node material shrinkage and bounding box size
        for node in self._sliceableNodes():
            node_extruder_position = node.callDecoration("getActiveExtruderPosition")
            if node_extruder_position is None:
                continue

            # This function can be triggered in the middle of a machine change, so do not proceed if the machine change
            # has not been done yet.
            try:
                global_container_stack.extruderList[int(node_extruder_position)]
            except IndexError:
                Application.getInstance().callLater(lambda: self._retry_wrapper.needsRetry.emit())
                return False

            if material_shrinkage > shrinkage_threshold:
                bbox = node.getBoundingBox()
                if bbox is not None and (bbox.width >= warning_size_xy or bbox.depth >= warning_size_xy or bbox.height >= warning_size_z):
                    warning_nodes.append(node)

        if len(warning_nodes) <= 0:
            return False

        self._caution_message.setText(catalog.i18nc(
            "@info:status",
            "<p>One or more 3D models may not print optimally due to the model size and material configuration:</p>"
            "<p>{model_names}</p>"
            "<p>Find out how to ensure the best possible print quality and reliability.</p>"
            "<p><a href=\"https://support.ultimaker.com/s/article/1667337573434\">View print quality guide</a></p>"
            ).format(model_names = ", ".join([n.getName() for n in warning_nodes])))

        return True

    def _checkForOverhangs(self) -> bool:
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack and global_container_stack.getValue("support_enable"):
            return False

        warning_nodes = []
        for node in self._sliceableNodes():

            # Check for any enabled support in the per-model settings.
            if node.hasDecoration("getStack") and node.callDecoration("getStack").getValue("support_enable"):
                continue

            # Check if any support is painted on.
            if node.hasDecoration("getPaintedSupportTexels") and node.callDecoration("getPaintedSupportTexels"):
                continue

            # Actually check the model itself for any overhanging structures that'd need to be supported.
            if OverhangChecker.checkForDownFaces(node) or OverhangChecker.checkForDownVertices(node):
                warning_nodes.append(node)

        if len(warning_nodes) <= 0:
            return False

        self._caution_message.setText(catalog.i18nc(
            "@info:status",
            "<p>One or more 3D models may not print optimally due to the model shape and missing support:</p>"
            "<p>{model_names}</p>"
            "<p>Enable auto-support or paint on support for better print quality and reliability.</p>"
            "<p><a href=\"https://support.ultimaker.com/s/article/1667417606331\">View support settings guide</a></p>"
            ).format(model_names = ", ".join([n.getName() for n in warning_nodes])))
        self._caution_message.addAction("enable_support",
          name=catalog.i18nc("@button", "Enable Auto-Support"),
          icon="",
          description=catalog.i18nc("@label", "Support for the model is currently off, turn auto-support on.")
          )

        return True
