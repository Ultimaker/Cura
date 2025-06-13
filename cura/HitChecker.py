from typing import List, Dict
from cura.Scene.CuraSceneNode import CuraSceneNode


class HitChecker:
    """Checks if nodes can be printed without causing any collisions and interference"""

    def __init__(self, nodes: List[CuraSceneNode]) -> None:
        self._hit_map = self._buildHitMap(nodes)

    def anyTwoNodesBlockEachOther(self, nodes: List[CuraSceneNode]) -> bool:
        """Returns True if any 2 nodes block each other"""
        for a in nodes:
            for b in nodes:
                if self._hit_map[a][b] and self._hit_map[b][a]:
                    return True
        return False

    def canPrintBefore(self, node: CuraSceneNode, other_nodes: List[CuraSceneNode]) -> bool:
        """Returns True if node doesn't block other_nodes and can be printed before them"""
        no_hits = all(not self._hit_map[node][other_node] for other_node in other_nodes)
        return no_hits

    def canPrintAfter(self, node: CuraSceneNode, other_nodes: List[CuraSceneNode]) -> bool:
        """Returns True if node doesn't hit other nodes and can be printed after them"""
        no_hits = all(not self._hit_map[other_node][node] for other_node in other_nodes)
        return no_hits

    def calculateScore(self, a: CuraSceneNode, b: CuraSceneNode) -> int:
        """Calculate score simply sums the number of other objects it 'blocks'

        :param a: node
        :param b: node
        :return: sum of the number of other objects
        """

        score_a = sum(self._hit_map[a].values())
        score_b = sum(self._hit_map[b].values())
        return score_a - score_b

    def canPrintNodesInProvidedOrder(self, ordered_nodes: List[CuraSceneNode]) -> bool:
        """Returns True If nodes don't have any hits in provided order"""
        for node_index, node in enumerate(ordered_nodes):
            nodes_before = ordered_nodes[:node_index - 1] if node_index - 1 >= 0 else []
            nodes_after = ordered_nodes[node_index + 1:] if node_index + 1 < len(ordered_nodes) else []
            if not self.canPrintBefore(node, nodes_after) or not self.canPrintAfter(node, nodes_before):
                return False
        return True

    @staticmethod
    def _buildHitMap(nodes: List[CuraSceneNode]) -> Dict[CuraSceneNode, CuraSceneNode]:
        """Pre-computes all hits between all objects

        :nodes: nodes that need to be checked for collisions
        :return: dictionary where hit_map[node1][node2] is False if there node1 can be printed before node2
        """
        hit_map = {j: {i: HitChecker._checkHit(j, i) for i in nodes} for j in nodes}
        return hit_map

    @staticmethod
    def _checkHit(a: CuraSceneNode, b: CuraSceneNode) -> bool:
        """Checks if a can be printed before b

        :param a: node
        :param b: node
        :return: False if a can be printed before b
        """

        if a == b:
            return False

        a_hit_hull = a.callDecoration("getConvexHullBoundary")
        b_hit_hull = b.callDecoration("getConvexHullHeadFull")
        overlap = a_hit_hull.intersectsPolygon(b_hit_hull)

        if overlap:
            return True

        # Adhesion areas must never overlap, regardless of printing order
        # This would cause over-extrusion
        a_hit_hull = a.callDecoration("getAdhesionArea")
        b_hit_hull = b.callDecoration("getAdhesionArea")
        overlap = a_hit_hull.intersectsPolygon(b_hit_hull)

        if overlap:
            return True
        else:
            return False
