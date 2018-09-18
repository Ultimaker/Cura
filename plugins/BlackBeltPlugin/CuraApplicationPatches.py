from UM.Math.Vector import Vector
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation

from cura.Scene.CuraSceneNode import CuraSceneNode

from cura.Scene.BuildPlateDecorator import BuildPlateDecorator
from cura.Scene.ConvexHullDecorator import ConvexHullDecorator
from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator
from cura.Scene.BlockSlicingDecorator import BlockSlicingDecorator

from cura.Arranging.Arrange import Arrange
from cura.Arranging.ShapeArray import ShapeArray

import os

class CuraApplicationPatches():
    def __init__(self, application):
        self._application = application

        self._application._readMeshFinished = self._readMeshFinished
        self._application.arrange = self.arrange

        self._margin_between_models = 50

    ##  Arrange a set of nodes given a set of fixed nodes
    #   \param nodes nodes that we have to place
    #   \param fixed_nodes nodes that are placed in the arranger before finding spots for nodes
    #   Copied verbatim from CuraApplication.arrange, with a patch to place objects in a row
    def arrange(self, nodes, fixed_nodes):
        ### START PATCH: perform simplified arrange for blackbelt printers
        global_container_stack = self._application.getGlobalContainerStack()
        if not global_container_stack:
            return

        definition_container = global_container_stack.getBottom()
        if definition_container.getId() == "blackbelt":
            leading_edge = self._application.getBuildVolume().getBoundingBox().front

            for fixed_node in fixed_nodes:
                leading_edge = min(leading_edge, existing_node.getBoundingBox().back)

            for node in nodes:
                half_node_depth = node.getBoundingBox().depth / 2
                node.setPosition(Vector(0, 0, leading_edge - half_node_depth - self._margin_between_models))
                leading_edge = node.getBoundingBox().back

            return
        ### END PATCH

        min_offset = self._application.getBuildVolume().getEdgeDisallowedSize() + 2  # Allow for some rounding errors
        job = ArrangeObjectsJob(nodes, fixed_nodes, min_offset = max(min_offset, 8))
        job.start()


    #   Copied verbatim from CuraApplication._readMeshFinished, with a patch to place objects in a row
    def _readMeshFinished(self, job):
        ### START PATCH: detect blackbelt printer
        global_container_stack = self._application.getGlobalContainerStack()
        if not global_container_stack:
            return

        definition_container = global_container_stack.getBottom()
        is_blackbelt_printer = definition_container.getId() == "blackbelt"
        ### END PATCH

        nodes = job.getResult()
        file_name = job.getFileName()
        file_name_lower = file_name.lower()
        file_extension = file_name_lower.split(".")[-1]
        self._application._currently_loading_files.remove(file_name)

        self._application.fileLoaded.emit(file_name)
        target_build_plate = self._application.getMultiBuildPlateModel().activeBuildPlate

        root = self._application.getController().getScene().getRoot()
        fixed_nodes = []
        for node_ in DepthFirstIterator(root):
            if node_.callDecoration("isSliceable") and node_.callDecoration("getBuildPlateNumber") == target_build_plate:
                fixed_nodes.append(node_)
        global_container_stack = self._application.getGlobalContainerStack()
        machine_width = global_container_stack.getProperty("machine_width", "value")
        machine_depth = global_container_stack.getProperty("machine_depth", "value")
        arranger = Arrange.create(x = machine_width, y = machine_depth, fixed_nodes = fixed_nodes)
        min_offset = 8
        default_extruder_position = self._application.getMachineManager().defaultExtruderPosition
        default_extruder_id = self._application._global_container_stack.extruders[default_extruder_position].getId()

        select_models_on_load = self._application.getPreferences().getValue("cura/select_models_on_load")

        for original_node in nodes:

            # Create a CuraSceneNode just if the original node is not that type
            if isinstance(original_node, CuraSceneNode):
                node = original_node
            else:
                node = CuraSceneNode()
                node.setMeshData(original_node.getMeshData())

                #Setting meshdata does not apply scaling.
                if(original_node.getScale() != Vector(1.0, 1.0, 1.0)):
                    node.scale(original_node.getScale())

            node.setSelectable(True)
            node.setName(os.path.basename(file_name))
            self._application.getBuildVolume().checkBoundsAndUpdate(node)

            is_non_sliceable = "." + file_extension in self._application._non_sliceable_extensions

            if is_non_sliceable:
                self._application.callLater(lambda: self._application.getController().setActiveView("SimulationView"))

                block_slicing_decorator = BlockSlicingDecorator()
                node.addDecorator(block_slicing_decorator)
            else:
                sliceable_decorator = SliceableObjectDecorator()
                node.addDecorator(sliceable_decorator)

            scene = self._application.getController().getScene()

            # If there is no convex hull for the node, start calculating it and continue.
            if not node.getDecorator(ConvexHullDecorator):
                node.addDecorator(ConvexHullDecorator())
            for child in node.getAllChildren():
                if not child.getDecorator(ConvexHullDecorator):
                    child.addDecorator(ConvexHullDecorator())

            ### START PATCH: don't do standard arrange on load for blackbelt printers
            ###              but place in a line instead
            if is_blackbelt_printer:
                half_node_depth = node.getBoundingBox().depth / 2
                build_plate_empty = True
                leading_edge = self._application.getBuildVolume().getBoundingBox().front

                for existing_node in DepthFirstIterator(root):
                    if (
                        not issubclass(type(existing_node), CuraSceneNode) or
                        (not existing_node.getMeshData() and not existing_node.callDecoration("getLayerData")) or
                        (existing_node.callDecoration("getBuildPlateNumber") != target_build_plate)):

                        continue

                    build_plate_empty = False
                    leading_edge = min(leading_edge, existing_node.getBoundingBox().back)

                if not build_plate_empty or leading_edge < half_node_depth:
                    node.setPosition(Vector(0, 0, leading_edge - half_node_depth - self._margin_between_models))

            ### END PATCH
            if file_extension != "3mf":
                if node.callDecoration("isSliceable"):
                    # Only check position if it's not already blatantly obvious that it won't fit.
                    if node.getBoundingBox() is None or self._application._volume.getBoundingBox() is None or node.getBoundingBox().width < self._application._volume.getBoundingBox().width or node.getBoundingBox().depth < self._application._volume.getBoundingBox().depth:
                        # Find node location
                        offset_shape_arr, hull_shape_arr = ShapeArray.fromNode(node, min_offset = min_offset)

                        # If a model is to small then it will not contain any points
                        if offset_shape_arr is None and hull_shape_arr is None:
                            Message(self._application._i18n_catalog.i18nc("@info:status", "The selected model was too small to load."),
                                    title=self._application._i18n_catalog.i18nc("@info:title", "Warning")).show()
                            return

                        # Step is for skipping tests to make it a lot faster. it also makes the outcome somewhat rougher
                        arranger.findNodePlacement(node, offset_shape_arr, hull_shape_arr, step = 10)

            # This node is deep copied from some other node which already has a BuildPlateDecorator, but the deepcopy
            # of BuildPlateDecorator produces one that's associated with build plate -1. So, here we need to check if
            # the BuildPlateDecorator exists or not and always set the correct build plate number.
            build_plate_decorator = node.getDecorator(BuildPlateDecorator)
            if build_plate_decorator is None:
                build_plate_decorator = BuildPlateDecorator(target_build_plate)
                node.addDecorator(build_plate_decorator)
            build_plate_decorator.setBuildPlateNumber(target_build_plate)

            op = AddSceneNodeOperation(node, scene.getRoot())
            op.push()

            node.callDecoration("setActiveExtruder", default_extruder_id)
            scene.sceneChanged.emit(node)

            if select_models_on_load:
                Selection.add(node)

        self._application.fileCompleted.emit(file_name)
