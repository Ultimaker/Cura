from unittest.mock import patch

from cura.HitChecker import HitChecker
from cura.OneAtATimeIterator import OneAtATimeIterator
from cura.Scene.CuraSceneNode import CuraSceneNode


def test_anyTwoNodesBlockEachOther_True():
    node1 = CuraSceneNode(no_setting_override=True)
    node2 = CuraSceneNode(no_setting_override=True)
    # node1 and node2 block each other
    hit_map = {
        node1: {node1: 0, node2: 1},
        node2: {node1: 1, node2: 0}
    }

    with patch.object(HitChecker, "_buildHitMap", return_value=hit_map):
        hit_checker = HitChecker([node1, node2])
        assert hit_checker.anyTwoNodesBlockEachOther([node1, node2])
        assert hit_checker.anyTwoNodesBlockEachOther([node2, node1])


def test_anyTwoNodesBlockEachOther_False():
    node1 = CuraSceneNode(no_setting_override=True)
    node2 = CuraSceneNode(no_setting_override=True)
    # node1 blocks node2, but node2 doesn't block node1
    hit_map = {
        node1: {node1: 0, node2: 1},
        node2: {node1: 0, node2: 0}
    }

    with patch.object(HitChecker, "_buildHitMap", return_value=hit_map):
        hit_checker = HitChecker([node1, node2])
        assert not hit_checker.anyTwoNodesBlockEachOther([node1, node2])
        assert not hit_checker.anyTwoNodesBlockEachOther([node2, node1])


def test_canPrintBefore():
    node1 = CuraSceneNode(no_setting_override=True)
    node2 = CuraSceneNode(no_setting_override=True)
    node3 = CuraSceneNode(no_setting_override=True)
    # nodes can be printed only in order node1 -> node2 -> node3
    hit_map = {
        node1: {node1: 0, node2: 0, node3: 0},
        node2: {node1: 1, node2: 0, node3: 0},
        node3: {node1: 1, node2: 1, node3: 0},
    }

    with patch.object(HitChecker, "_buildHitMap", return_value=hit_map):
        hit_checker = HitChecker([node1, node2, node3])

        assert hit_checker.canPrintBefore(node1, [node2])
        assert hit_checker.canPrintBefore(node1, [node3])
        assert hit_checker.canPrintBefore(node1, [node2, node3])
        assert hit_checker.canPrintBefore(node1, [node3, node2])

        assert hit_checker.canPrintBefore(node2, [node3])
        assert not hit_checker.canPrintBefore(node2, [node1])
        assert not hit_checker.canPrintBefore(node2, [node1, node3])
        assert not hit_checker.canPrintBefore(node2, [node3, node1])

        assert not hit_checker.canPrintBefore(node3, [node1])
        assert not hit_checker.canPrintBefore(node3, [node2])
        assert not hit_checker.canPrintBefore(node3, [node1, node2])
        assert not hit_checker.canPrintBefore(node3, [node2, node1])


def test_canPrintAfter():
    node1 = CuraSceneNode(no_setting_override=True)
    node2 = CuraSceneNode(no_setting_override=True)
    node3 = CuraSceneNode(no_setting_override=True)
    
    # nodes can be printed only in order node1 -> node2 -> node3
    hit_map = {
        node1: {node1: 0, node2: 0, node3: 0},
        node2: {node1: 1, node2: 0, node3: 0},
        node3: {node1: 1, node2: 1, node3: 0},
    }

    with patch.object(HitChecker, "_buildHitMap", return_value=hit_map):
        hit_checker = HitChecker([node1, node2, node3])

        assert not hit_checker.canPrintAfter(node1, [node2])
        assert not hit_checker.canPrintAfter(node1, [node3])
        assert not hit_checker.canPrintAfter(node1, [node2, node3])
        assert not hit_checker.canPrintAfter(node1, [node3, node2])

        assert hit_checker.canPrintAfter(node2, [node1])
        assert not hit_checker.canPrintAfter(node2, [node3])
        assert not hit_checker.canPrintAfter(node2, [node1, node3])
        assert not hit_checker.canPrintAfter(node2, [node3, node1])

        assert hit_checker.canPrintAfter(node3, [node1])
        assert hit_checker.canPrintAfter(node3, [node2])
        assert hit_checker.canPrintAfter(node3, [node1, node2])
        assert hit_checker.canPrintAfter(node3, [node2, node1])


def test_calculateScore():
    node1 = CuraSceneNode(no_setting_override=True)
    node2 = CuraSceneNode(no_setting_override=True)
    node3 = CuraSceneNode(no_setting_override=True)

    hit_map = {
        node1: {node1: 0, node2: 0, node3: 0},  # sum is 0
        node2: {node1: 1, node2: 0, node3: 0},  # sum is 1
        node3: {node1: 1, node2: 1, node3: 0},  # sum is 2
    }

    with patch.object(HitChecker, "_buildHitMap", return_value=hit_map):
        hit_checker = HitChecker([node1, node2, node3])

        # score is a diff between sums
        assert hit_checker.calculateScore(node1, node2) == -1
        assert hit_checker.calculateScore(node2, node1) == 1
        assert hit_checker.calculateScore(node1, node3) == -2
        assert hit_checker.calculateScore(node3, node1) == 2
        assert hit_checker.calculateScore(node2, node3) == -1
        assert hit_checker.calculateScore(node3, node2) == 1


def test_canPrintNodesInProvidedOrder():
    node1 = CuraSceneNode(no_setting_override=True)
    node2 = CuraSceneNode(no_setting_override=True)
    node3 = CuraSceneNode(no_setting_override=True)

    # nodes can be printed only in order node1 -> node2 -> node3
    hit_map = {
        node1: {node1: 0, node2: 0, node3: 0}, # 0
        node2: {node1: 1, node2: 0, node3: 0}, # 1
        node3: {node1: 1, node2: 1, node3: 0}, # 2
    }

    with patch.object(HitChecker, "_buildHitMap", return_value=hit_map):
        hit_checker = HitChecker([node1, node2, node3])
        assert hit_checker.canPrintNodesInProvidedOrder([node1, node2, node3])
        assert not hit_checker.canPrintNodesInProvidedOrder([node1, node3, node2])
        assert not hit_checker.canPrintNodesInProvidedOrder([node2, node1, node3])
        assert not hit_checker.canPrintNodesInProvidedOrder([node2, node3, node1])
        assert not hit_checker.canPrintNodesInProvidedOrder([node3, node1, node2])
        assert not hit_checker.canPrintNodesInProvidedOrder([node3, node2, node1])