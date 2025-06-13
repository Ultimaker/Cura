from typing import List, Callable, Optional, Any

from PyQt6.QtCore import pyqtProperty, pyqtSignal, QObject, pyqtSlot
from UM.Application import Application
from UM.Scene.Selection import Selection

from cura.Scene.CuraSceneNode import CuraSceneNode


class PrintOrderManager(QObject):
    """Allows to order the object list to set the print sequence manually"""

    def __init__(self, get_nodes: Callable[[], List[CuraSceneNode]]) -> None:
        super().__init__()
        self._get_nodes = get_nodes
        self._configureEvents()

    _settingsChanged = pyqtSignal()
    _uiActionsOutdated = pyqtSignal()
    printOrderChanged = pyqtSignal()

    @pyqtSlot()
    def swapSelectedAndPreviousNodes(self) -> None:
        selected_node, previous_node, next_node = self._getSelectedAndNeighborNodes()
        self._swapPrintOrders(selected_node, previous_node)

    @pyqtSlot()
    def swapSelectedAndNextNodes(self) -> None:
        selected_node, previous_node, next_node = self._getSelectedAndNeighborNodes()
        self._swapPrintOrders(selected_node, next_node)

    @pyqtProperty(str, notify=_uiActionsOutdated)
    def previousNodeName(self) -> str:
        selected_node, previous_node, next_node = self._getSelectedAndNeighborNodes()
        return self._getNodeName(previous_node)

    @pyqtProperty(str, notify=_uiActionsOutdated)
    def nextNodeName(self) -> str:
        selected_node, previous_node, next_node = self._getSelectedAndNeighborNodes()
        return self._getNodeName(next_node)

    @pyqtProperty(bool, notify=_uiActionsOutdated)
    def shouldEnablePrintBeforeAction(self) -> bool:
        selected_node, previous_node, next_node = self._getSelectedAndNeighborNodes()
        can_swap_with_previous_node = selected_node is not None and previous_node is not None
        return can_swap_with_previous_node

    @pyqtProperty(bool, notify=_uiActionsOutdated)
    def shouldEnablePrintAfterAction(self) -> bool:
        selected_node, previous_node, next_node = self._getSelectedAndNeighborNodes()
        can_swap_with_next_node = selected_node is not None and next_node is not None
        return can_swap_with_next_node

    @pyqtProperty(bool, notify=_settingsChanged)
    def shouldShowEditPrintOrderActions(self) -> bool:
        return PrintOrderManager.isUserDefinedPrintOrderEnabled()

    @staticmethod
    def isUserDefinedPrintOrderEnabled() -> bool:
        stack = Application.getInstance().getGlobalContainerStack()
        is_enabled = stack and \
                     stack.getProperty("print_sequence", "value") == "one_at_a_time" and \
                     stack.getProperty("user_defined_print_order_enabled", "value")
        return bool(is_enabled)

    @staticmethod
    def initializePrintOrders(nodes: List[CuraSceneNode]) -> None:
        """Just created (loaded from file) nodes have print order 0.

         This method initializes print orders with max value to put nodes at the end of object list"""
        max_print_order = max(map(lambda n: n.printOrder, nodes), default=0)
        for node in nodes:
            if node.printOrder == 0:
                max_print_order += 1
                node.printOrder = max_print_order

    @staticmethod
    def updatePrintOrdersAfterGroupOperation(
            all_nodes: List[CuraSceneNode],
            group_node: CuraSceneNode,
            grouped_nodes: List[CuraSceneNode]
    ) -> None:
        group_node.printOrder = min(map(lambda n: n.printOrder, grouped_nodes))

        all_nodes.append(group_node)
        for node in grouped_nodes:
            all_nodes.remove(node)

        # reassign print orders so there won't be gaps like 1 2 5 6 7
        sorted_nodes = sorted(all_nodes, key=lambda n: n.printOrder)
        for i, node in enumerate(sorted_nodes):
            node.printOrder = i + 1

    @staticmethod
    def updatePrintOrdersAfterUngroupOperation(
            all_nodes: List[CuraSceneNode],
            group_node: CuraSceneNode,
            ungrouped_nodes: List[CuraSceneNode]
    ) -> None:
        all_nodes.remove(group_node)
        nodes_to_update_print_order = filter(lambda n: n.printOrder > group_node.printOrder, all_nodes)
        for node in nodes_to_update_print_order:
            node.printOrder += len(ungrouped_nodes) - 1

        for i, child in enumerate(ungrouped_nodes):
            child.printOrder = group_node.printOrder + i
            all_nodes.append(child)

    def _swapPrintOrders(self, node1: CuraSceneNode, node2: CuraSceneNode) -> None:
        if node1 and node2:
            node1.printOrder, node2.printOrder = node2.printOrder, node1.printOrder  # swap print orders
            self.printOrderChanged.emit()  # update object list first
            self._uiActionsOutdated.emit()  # then update UI actions

    def _getSelectedAndNeighborNodes(self
                                     ) -> (Optional[CuraSceneNode], Optional[CuraSceneNode], Optional[CuraSceneNode]):
        nodes = self._get_nodes()
        ordered_nodes = sorted(nodes, key=lambda n: n.printOrder)
        for i, node in enumerate(ordered_nodes, 1):
            node.printOrder = i

        selected_node = PrintOrderManager._getSingleSelectedNode()
        if selected_node and selected_node in ordered_nodes:
            selected_node_index = ordered_nodes.index(selected_node)
        else:
            selected_node_index = None

        if selected_node_index is not None and selected_node_index - 1 >= 0:
            previous_node = ordered_nodes[selected_node_index - 1]
        else:
            previous_node = None

        if selected_node_index is not None and selected_node_index + 1 < len(ordered_nodes):
            next_node = ordered_nodes[selected_node_index + 1]
        else:
            next_node = None

        return selected_node, previous_node, next_node

    @staticmethod
    def _getNodeName(node: CuraSceneNode, max_length: int = 30) -> str:
        node_name = node.getName() if node else ""
        truncated_node_name = node_name[:max_length]
        return truncated_node_name

    @staticmethod
    def _getSingleSelectedNode() -> Optional[CuraSceneNode]:
        if len(Selection.getAllSelectedObjects()) == 1:
            selected_node = Selection.getSelectedObject(0)
            return selected_node
        return None

    def _configureEvents(self) -> None:
        Selection.selectionChanged.connect(self._onSelectionChanged)
        self._global_stack = None
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalStackChanged)
        self._onGlobalStackChanged()

    def _onGlobalStackChanged(self) -> None:
        if self._global_stack:
            self._global_stack.propertyChanged.disconnect(self._onSettingsChanged)
            self._global_stack.containersChanged.disconnect(self._onSettingsChanged)

        self._global_stack = Application.getInstance().getGlobalContainerStack()

        if self._global_stack:
            self._global_stack.propertyChanged.connect(self._onSettingsChanged)
            self._global_stack.containersChanged.connect(self._onSettingsChanged)

    def _onSettingsChanged(self, *args: Any) -> None:
        self._settingsChanged.emit()

    def _onSelectionChanged(self) -> None:
        self._uiActionsOutdated.emit()
