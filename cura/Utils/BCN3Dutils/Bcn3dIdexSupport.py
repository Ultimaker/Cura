import math

from UM.Application import Application
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.TranslateOperation import TranslateOperation
from UM.Controller import Controller
from UM.Scene.Selection import Selection
from UM.Scene.Scene import Scene
from UM.Math.Vector import Vector
from UM.Scene.SceneNode import SceneNode

from cura.Scene.CuraSceneNode import CuraSceneNode
from cura.Operations.SetParentOperation import SetParentOperation


from .PrintModeManager import PrintModeManager
from .Scene.DuplicatedNode import DuplicatedNode
from .Operations.RemoveNodesOperation import RemoveNodesOperation
from .Operations.AddNodesOperation import AddNodesOperation

# Recalculate Duplicated Nodes when center operation (@pyqtSlot def centerSelection())
# cura/CuraActions.py:84
def recaltulateDuplicatedNodeCenterMoveOperation(center_operation :TranslateOperation, current_node : SceneNode) -> TranslateOperation:
    print_mode = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "value")
    if print_mode == "duplication" or print_mode == "mirror":
        machine_width = Application.getInstance().getGlobalContainerStack().getProperty("machine_width", "value")
        center = -machine_width / 4
        if print_mode == "mirror":
            machine_head_with_fans_polygon = Application.getInstance().getGlobalContainerStack().getProperty("machine_head_with_fans_polygon", "value")
            machine_head_size = math.fabs(machine_head_with_fans_polygon[0][0] - machine_head_with_fans_polygon[2][0])
            center -= machine_head_size / 4
        vector = Vector(current_node._position.x - center, current_node._position.y, current_node._position.z)

        return TranslateOperation(current_node, -vector)
    return center_operation

# Remove duplicate Nodes before delete its parents (@pyqtSlot() def deleteSelection(self))
# cura/CuraActions.py:113
def removeDuplitedNode(op : GroupedOperation, node : SceneNode) -> GroupedOperation:
    print_mode = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "value")
    if print_mode not in ["singleT0", "singleT1", "dual"]:
        node_dup = PrintModeManager.getInstance().getDuplicatedNode(node)
        if(node_dup):
            op.addOperation(RemoveNodesOperation(node_dup))
    return op

# Update node boundary for duplicated nodes (def updateNodeBoundaryCheck(self))
# cura/BuildVolume.py:308 
def updateNodeBoundaryCheckForDuplicated(global_container_stack) -> None:
    print_mode = global_container_stack.getProperty("print_mode", "value")
    if print_mode not in ["singleT0", "singleT1", "dual"]:
        duplicated_nodes = PrintModeManager.getInstance().getDuplicatedNodes()
        for node_dup in duplicated_nodes:
            node_dup._outside_buildarea = node_dup.node._outside_buildarea

# Deleted duplitaed nodes when group selected for being deleted (@pyqtSlot() def groupSelected(self) )
# cura/CuraApplication.py:1652
def duplicatedGroupSelected(globalContainerStack, controller : Controller, group_node : CuraSceneNode, selection : Selection, setParentOperation : SetParentOperation, print_mode_manager: PrintModeManager) -> None:
    print_mode_enabled = globalContainerStack.getProperty("print_mode", "enabled")
    if print_mode_enabled:
        print_mode = globalContainerStack.getProperty("print_mode", "value")
        if print_mode not in ["singleT0","singleT1","dual"]:
            duplicated_group_node = DuplicatedNode(group_node, controller.getScene().getRoot())
        else:
            duplicated_group_node = DuplicatedNode(group_node)

    op = GroupedOperation()
    for node in selection.getAllSelectedObjects():
        if print_mode_enabled:
            node_dup = print_mode_manager.getDuplicatedNode(node)
            op.addOperation(setParentOperation(node_dup, duplicated_group_node))

        op.addOperation(setParentOperation(node, group_node))

    op.push()

# On group with duplicated nodes selected (@pyqtSlot() def ungroupSelected(self))
# cura/CuraApplication.py:1680
def onDuplicatedgroupSelected(op : GroupedOperation, globalContainerStack, node : SceneNode):
        print_mode = self.getGlobalContainerStack().getProperty("print_mode", "value")
        if print_mode not in ["singleT0", "singleT1", "dual"]:
            duplicated_group_node = self._print_mode_manager.getDuplicatedNode(node)
            duplicated_group_parent = duplicated_group_node.getParent()
            duplicated_children = duplicated_group_node.getChildren().copy()
            for child in duplicated_children:
                op.addOperation(SetParentOperation(child, duplicated_group_parent))

# On group with duplicated nodes selected (def _readMeshFinished(self, job))
# cura/CuraApplication.py:1958
def onReadMeshFinished(nodes_to_arrange, globalContainerStack, node : SceneNode, scene : Scene):
    print_mode_enabled = globalContainerStack().getProperty("print_mode", "enabled")
    if print_mode_enabled:
        node_dup = DuplicatedNode(node)
        op = AddNodesOperation(node_dup, scene.getRoot())
        op.redo()
        op.push()
        nodes_to_arrange.append(node_dup)
    else:
        op = AddSceneNodeOperation(node, scene.getRoot())
    op.push()
    node.callDecoration("setActiveExtruder", default_extruder_id)
    scene.sceneChanged.emit(node)