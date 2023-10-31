from typing import List, TYPE_CHECKING, Optional, Tuple, Set

if TYPE_CHECKING:
    from UM.Operations.GroupedOperation import GroupedOperation


class Arranger:
    def createGroupOperationForArrange(self, add_new_nodes_in_scene: bool = False) -> Tuple["GroupedOperation", int]:
        """
        Find placement for a set of scene nodes, but don't actually move them just yet.
        :param add_new_nodes_in_scene: Whether to create new scene nodes before applying the transformations and rotations
        :return: tuple (found_solution_for_all, node_items)
            WHERE
            found_solution_for_all: Whether the algorithm found a place on the buildplate for all the objects
            node_items: A list of the nodes return by libnest2d, which contain the new positions on the buildplate
        """
        raise NotImplementedError

    def arrange(self, add_new_nodes_in_scene: bool = False) -> bool:
        """
        Find placement for a set of scene nodes, and move them by using a single grouped operation.
        :param add_new_nodes_in_scene: Whether to create new scene nodes before applying the transformations and rotations
        :return: found_solution_for_all: Whether the algorithm found a place on the buildplate for all the objects
        """
        grouped_operation, not_fit_count = self.createGroupOperationForArrange(add_new_nodes_in_scene)
        grouped_operation.push()
        return not_fit_count == 0
