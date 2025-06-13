from unittest.mock import patch, MagicMock

from cura.PrintOrderManager import PrintOrderManager
from cura.Scene.CuraSceneNode import CuraSceneNode


def test_getNodeName():
    node1 = CuraSceneNode(name="cat", no_setting_override=True)
    node2 = CuraSceneNode(name="dog", no_setting_override=True)
    assert PrintOrderManager._getNodeName(node1) == "cat"
    assert PrintOrderManager._getNodeName(node2) == "dog"
    assert PrintOrderManager._getNodeName(None) == ""


def test_getNodeName_truncatesLongName():
    node = CuraSceneNode(name="some_name_longer_than_30_characters", no_setting_override=True)
    assert PrintOrderManager._getNodeName(node) == "some_name_longer_than_30_chara"
    assert PrintOrderManager._getNodeName(node, max_length=10) == "some_name_"


def test_getSingleSelectedNode():
    node1 = CuraSceneNode(no_setting_override=True)
    with patch("UM.Scene.Selection.Selection.getAllSelectedObjects", MagicMock(return_value=[node1])):
        with patch("UM.Scene.Selection.Selection.getSelectedObject", MagicMock(return_value=node1)):
            assert PrintOrderManager._getSingleSelectedNode() == node1


def test_getSingleSelectedNode_returnsNoneIfNothingSelected():
    with patch("UM.Scene.Selection.Selection.getAllSelectedObjects", MagicMock(return_value=[])):
        assert PrintOrderManager._getSingleSelectedNode() is None


def test_getSingleSelectedNode_returnsNoneIfMultipleObjectsSelected():
    node1 = CuraSceneNode(no_setting_override=True)
    node2 = CuraSceneNode(no_setting_override=True)
    with patch("UM.Scene.Selection.Selection.getAllSelectedObjects", MagicMock(return_value=[node1, node2])):
        assert PrintOrderManager._getSingleSelectedNode() is None


def test_neighborNodeNamesCorrect_WhenSomeNodeSelected():
    node1 = CuraSceneNode(no_setting_override=True, name="node1")
    node2 = CuraSceneNode(no_setting_override=True, name="node2")
    node3 = CuraSceneNode(no_setting_override=True, name="node3")
    node1.printOrder = 1
    node2.printOrder = 2
    node3.printOrder = 3
    with patch.object(PrintOrderManager, "_configureEvents", return_value=None):
        with patch.object(PrintOrderManager, "_getSingleSelectedNode", return_value=node1):
            print_order_manager = PrintOrderManager(get_nodes=lambda: [node1, node2, node3])

            assert print_order_manager.previousNodeName == ""
            assert print_order_manager.nextNodeName == "node2"
            assert not print_order_manager.shouldEnablePrintBeforeAction
            assert print_order_manager.shouldEnablePrintAfterAction

            print_order_manager.swapSelectedAndNextNodes()  # swaps node1 with node2, result: [node2, node1, node3]
            assert print_order_manager.previousNodeName == "node2"
            assert print_order_manager.nextNodeName == "node3"
            assert print_order_manager.shouldEnablePrintBeforeAction
            assert print_order_manager.shouldEnablePrintAfterAction

            print_order_manager.swapSelectedAndNextNodes()  # swaps node1 with node3, result: [node2, node3, node1]
            assert print_order_manager.previousNodeName == "node3"
            assert print_order_manager.nextNodeName == ""
            assert print_order_manager.shouldEnablePrintBeforeAction
            assert not print_order_manager.shouldEnablePrintAfterAction

            print_order_manager.swapSelectedAndPreviousNodes()  # swaps node1 with node3, result: [node2, node1, node3]
            assert print_order_manager.previousNodeName == "node2"
            assert print_order_manager.nextNodeName == "node3"
            assert print_order_manager.shouldEnablePrintBeforeAction
            assert print_order_manager.shouldEnablePrintAfterAction

            print_order_manager.swapSelectedAndPreviousNodes()  # swaps node1 with node2, result: [node1, node2, node3]
            assert print_order_manager.previousNodeName == ""
            assert print_order_manager.nextNodeName == "node2"
            assert not print_order_manager.shouldEnablePrintBeforeAction
            assert print_order_manager.shouldEnablePrintAfterAction


def test_neighborNodeNamesEmpty_WhenNothingSelected():
    node1 = CuraSceneNode(no_setting_override=True, name="node1")
    node2 = CuraSceneNode(no_setting_override=True, name="node2")
    node3 = CuraSceneNode(no_setting_override=True, name="node3")
    node1.printOrder = 1
    node2.printOrder = 2
    node3.printOrder = 3
    with patch.object(PrintOrderManager, "_configureEvents", return_value=None):
        with patch.object(PrintOrderManager, "_getSingleSelectedNode", return_value=None):
            print_order_manager = PrintOrderManager(get_nodes=lambda: [node1, node2, node3])
            assert print_order_manager.previousNodeName == ""
            assert print_order_manager.nextNodeName == ""
            assert not print_order_manager.shouldEnablePrintBeforeAction
            assert not print_order_manager.shouldEnablePrintAfterAction


def test_initializePrintOrders():
    node1 = CuraSceneNode(no_setting_override=True)
    node2 = CuraSceneNode(no_setting_override=True)

    # assume print orders are 0
    assert node1.printOrder == 0
    assert node2.printOrder == 0

    PrintOrderManager.initializePrintOrders([node1, node2])

    # assert print orders initialized
    assert node1.printOrder == 1
    assert node2.printOrder == 2

    node3 = CuraSceneNode(no_setting_override=True)
    node4 = CuraSceneNode(no_setting_override=True)
    # assume print orders are 0
    assert node3.printOrder == 0
    assert node4.printOrder == 0

    PrintOrderManager.initializePrintOrders([node2, node1, node3, node4])

    # assert print orders not changed for node1 and node2 and initialized for node3 and node4
    assert node1.printOrder == 1
    assert node2.printOrder == 2
    assert node3.printOrder == 3
    assert node4.printOrder == 4


def test_updatePrintOrdersAfterGroupOperation():
    node1 = CuraSceneNode(no_setting_override=True)
    node2 = CuraSceneNode(no_setting_override=True)
    node3 = CuraSceneNode(no_setting_override=True)
    node4 = CuraSceneNode(no_setting_override=True)
    node5 = CuraSceneNode(no_setting_override=True)
    node1.printOrder = 1
    node2.printOrder = 2
    node3.printOrder = 3
    node4.printOrder = 4
    node5.printOrder = 5

    all_nodes = [node1, node2, node3, node4, node5]
    grouped_nodes = [node2, node4]
    group_node = CuraSceneNode(no_setting_override=True)

    PrintOrderManager.updatePrintOrdersAfterGroupOperation(all_nodes, group_node, grouped_nodes)

    assert node1.printOrder == 1
    assert group_node.printOrder == 2
    assert node3.printOrder == 3
    assert node5.printOrder == 4


def test_updatePrintOrdersAfterUngroupOperation():
    node1 = CuraSceneNode(no_setting_override=True)
    node2 = CuraSceneNode(no_setting_override=True)
    node3 = CuraSceneNode(no_setting_override=True)
    node1.printOrder = 1
    node2.printOrder = 2
    node3.printOrder = 3

    all_nodes = [node1, node2, node3]
    node4 = CuraSceneNode(no_setting_override=True)
    node5 = CuraSceneNode(no_setting_override=True)

    group_node = node2
    ungrouped_nodes = [node4, node5]
    PrintOrderManager.updatePrintOrdersAfterUngroupOperation(all_nodes, group_node, ungrouped_nodes)

    assert node1.printOrder == 1
    assert node4.printOrder == 2
    assert node5.printOrder == 3
    assert node3.printOrder == 4

    assert node1 in all_nodes
    assert node2 not in all_nodes
    assert node3 in all_nodes
    assert node4 in all_nodes
    assert node5 in all_nodes
