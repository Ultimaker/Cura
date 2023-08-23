import math
from typing import List, TYPE_CHECKING, Optional, Tuple, Set

if TYPE_CHECKING:
    from UM.Scene.SceneNode import SceneNode

from UM.Application import Application
from UM.Math import AxisAlignedBox
from UM.Math.Vector import Vector
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.TranslateOperation import TranslateOperation
from cura.Arranging.Arranger import Arranger


class GridArrange(Arranger):
    def __init__(self, nodes_to_arrange: List["SceneNode"], build_volume: "BuildVolume", fixed_nodes: List["SceneNode"] = None):
        if fixed_nodes is None:
            fixed_nodes = []
        self._nodes_to_arrange = nodes_to_arrange
        self._build_volume = build_volume
        self._build_volume_bounding_box = build_volume.getBoundingBox()
        self._fixed_nodes = fixed_nodes

        self._offset_x: float = 10
        self._offset_y: float = 10
        self._grid_width = 0
        self._grid_height = 0
        for node in self._nodes_to_arrange:
            bounding_box = node.getBoundingBox()
            self._grid_width = max(self._grid_width, bounding_box.width)
            self._grid_height = max(self._grid_height, bounding_box.depth)

        coord_initial_leftover_x = self._build_volume_bounding_box.right + 2 * self._grid_width
        coord_initial_leftover_y = (self._build_volume_bounding_box.back + self._build_volume_bounding_box.front) * 0.5
        self._initial_leftover_grid_x, self._initial_leftover_grid_y = self.coordSpaceToGridSpace(coord_initial_leftover_x, coord_initial_leftover_y)
        self._initial_leftover_grid_x = math.floor(self._initial_leftover_grid_x)
        self._initial_leftover_grid_y = math.floor(self._initial_leftover_grid_y)

    def createGroupOperationForArrange(self, add_new_nodes_in_scene: bool = True) -> Tuple[GroupedOperation, int]:
        # Find grid indexes that intersect with fixed objects
        fixed_nodes_grid_ids = set()
        for node in self._fixed_nodes:
            fixed_nodes_grid_ids = fixed_nodes_grid_ids.union(self.intersectingGridIdxInclusive(node.getBoundingBox()))

        build_plate_grid_ids = self.intersectingGridIdxExclusive(self._build_volume_bounding_box)

        # Filter out the corner grid squares if the build plate shape is elliptic
        if self._build_volume.getShape() == "elliptic":
            build_plate_grid_ids = set(filter(lambda grid_id: self.checkGridUnderDiscSpace(grid_id[0], grid_id[1]), build_plate_grid_ids))

        allowed_grid_idx = build_plate_grid_ids.difference(fixed_nodes_grid_ids)

        # Find the sequence in which items are placed
        coord_build_plate_center_x = self._build_volume_bounding_box.width * 0.5 + self._build_volume_bounding_box.left
        coord_build_plate_center_y = self._build_volume_bounding_box.depth * 0.5 + self._build_volume_bounding_box.back
        grid_build_plate_center_x, grid_build_plate_center_y = self.coordSpaceToGridSpace(coord_build_plate_center_x, coord_build_plate_center_y)

        def distToCenter(grid_id: Tuple[int, int]) -> float:
            grid_x, grid_y = grid_id
            distance_squared = (grid_build_plate_center_x - grid_x) ** 2 + (grid_build_plate_center_y - grid_y) ** 2
            return distance_squared

        sequence: List[Tuple[int, int]] = list(allowed_grid_idx)
        sequence.sort(key=distToCenter)
        scene_root = Application.getInstance().getController().getScene().getRoot()
        grouped_operation = GroupedOperation()

        for grid_id, node in zip(sequence, self._nodes_to_arrange):
            grouped_operation.addOperation(AddSceneNodeOperation(node, scene_root))
            grid_x, grid_y = grid_id
            operation = self.moveNodeOnGrid(node, grid_x, grid_y)
            grouped_operation.addOperation(operation)

        leftover_nodes = self._nodes_to_arrange[len(sequence):]

        left_over_grid_y = self._initial_leftover_grid_y
        for node in leftover_nodes:
            if add_new_nodes_in_scene:
                grouped_operation.addOperation(AddSceneNodeOperation(node, scene_root))
            # find the first next grid position that isn't occupied by a fixed node
            while (self._initial_leftover_grid_x, left_over_grid_y) in fixed_nodes_grid_ids:
                left_over_grid_y = left_over_grid_y - 1

            operation = self.moveNodeOnGrid(node, self._initial_leftover_grid_x, left_over_grid_y)
            grouped_operation.addOperation(operation)
            left_over_grid_y = left_over_grid_y - 1
        return grouped_operation, len(leftover_nodes)

    def moveNodeOnGrid(self, node: "SceneNode", grid_x: int, grid_y: int) -> "Operation.Operation":
        coord_grid_x, coord_grid_y = self.gridSpaceToCoordSpace(grid_x, grid_y)
        center_grid_x = coord_grid_x + (0.5 * (self._grid_width + self._offset_x))
        center_grid_y = coord_grid_y + (0.5 * (self._grid_height + self._offset_y))

        bounding_box = node.getBoundingBox()
        center_node_x = (bounding_box.left + bounding_box.right) * 0.5
        center_node_y = (bounding_box.back + bounding_box.front) * 0.5

        delta_x = center_grid_x - center_node_x
        delta_y = center_grid_y - center_node_y

        return TranslateOperation(node, Vector(delta_x, 0, delta_y))

    def getGridCornerPoints(self, bounding_box: "BoundingVolume") -> Tuple[float, float, float, float]:
        coord_x1 = bounding_box.left
        coord_x2 = bounding_box.right
        coord_y1 = bounding_box.back
        coord_y2 = bounding_box.front
        grid_x1, grid_y1 = self.coordSpaceToGridSpace(coord_x1, coord_y1)
        grid_x2, grid_y2 = self.coordSpaceToGridSpace(coord_x2, coord_y2)
        return grid_x1, grid_y1, grid_x2, grid_y2

    def intersectingGridIdxInclusive(self, bounding_box: "BoundingVolume") -> Set[Tuple[int, int]]:
        grid_x1, grid_y1, grid_x2, grid_y2 = self.getGridCornerPoints(bounding_box)
        grid_idx = set()
        for grid_x in range(math.floor(grid_x1), math.ceil(grid_x2)):
            for grid_y in range(math.floor(grid_y1), math.ceil(grid_y2)):
                grid_idx.add((grid_x, grid_y))
        return grid_idx

    def intersectingGridIdxExclusive(self, bounding_box: "BoundingVolume") -> Set[Tuple[int, int]]:
        grid_x1, grid_y1, grid_x2, grid_y2 = self.getGridCornerPoints(bounding_box)
        grid_idx = set()
        for grid_x in range(math.ceil(grid_x1), math.floor(grid_x2)):
            for grid_y in range(math.ceil(grid_y1), math.floor(grid_y2)):
                grid_idx.add((grid_x, grid_y))
        return grid_idx

    def gridSpaceToCoordSpace(self, x: float, y: float) -> Tuple[float, float]:
        grid_x = x * (self._grid_width + self._offset_x) + self._build_volume_bounding_box.left
        grid_y = y * (self._grid_height + self._offset_y) + self._build_volume_bounding_box.back
        return grid_x, grid_y

    def coordSpaceToGridSpace(self, grid_x: float, grid_y: float) -> Tuple[float, float]:
        coord_x = (grid_x - self._build_volume_bounding_box.left) / (self._grid_width + self._offset_x)
        coord_y = (grid_y - self._build_volume_bounding_box.back) / (self._grid_height + self._offset_y)
        return coord_x, coord_y

    def checkGridUnderDiscSpace(self, grid_x: int, grid_y: int) -> bool:
        left, back = self.gridSpaceToCoordSpace(grid_x, grid_y)
        right, front = self.gridSpaceToCoordSpace(grid_x + 1, grid_y + 1)
        corners = [(left, back), (right, back), (right, front), (left, front)]
        return all([self.checkPointUnderDiscSpace(x, y) for x, y in corners])

    def checkPointUnderDiscSpace(self, x: float, y: float) -> bool:
        disc_x, disc_y = self.coordSpaceToDiscSpace(x, y)
        distance_to_center_squared = disc_x ** 2 + disc_y ** 2
        return distance_to_center_squared <= 1.0

    def coordSpaceToDiscSpace(self, x: float, y: float) -> Tuple[float, float]:
        # Transform coordinate system to
        #
        #       coord_build_plate_left = -1
        #       |               coord_build_plate_right = 1
        #       v     (0,1)     v
        #       ┌───────┬───────┐  < coord_build_plate_back = -1
        #       │       │       │
        #       │       │(0,0)  │
        # (-1,0)├───────o───────┤(1,0)
        #       │       │       │
        #       │       │       │
        #       └───────┴───────┘  < coord_build_plate_front = +1
        #             (0,-1)
        disc_x = ((x - self._build_volume_bounding_box.left) / self._build_volume_bounding_box.width) * 2.0 - 1.0
        disc_y = ((y - self._build_volume_bounding_box.back) / self._build_volume_bounding_box.depth) * 2.0 - 1.0
        return disc_x, disc_y

    def drawDebugSvg(self):
        with open("Builvolume_test.svg", "w") as f:
            build_volume_bounding_box = self._build_volume_bounding_box

            f.write(
                f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='{build_volume_bounding_box.left - 100} {build_volume_bounding_box.back - 100} {build_volume_bounding_box.width + 200} {build_volume_bounding_box.depth + 200}'>\n")

            ellipse = True
            if ellipse:
                f.write(
                    f"""
                    <ellipse
                        cx='{(build_volume_bounding_box.left + build_volume_bounding_box.right) * 0.5}'
                        cy='{(build_volume_bounding_box.back + build_volume_bounding_box.front) * 0.5}'
                        rx='{build_volume_bounding_box.width * 0.5}' 
                        ry='{build_volume_bounding_box.depth * 0.5}' 
                        fill=\"blue\"
                    />
                    """)
            else:
                f.write(
                    f"""
                    <rect
                        x='{build_volume_bounding_box.left}'
                        y='{build_volume_bounding_box.back}'
                        width='{build_volume_bounding_box.width}' 
                        height='{build_volume_bounding_box.depth}' 
                        fill=\"lightgrey\"
                    />
                    """)

            for grid_x in range(0, 100):
                for grid_y in range(0, 100):
                    # if (grid_x, grid_y) in intersecting_grid_idx:
                    #     fill_color = "red"
                    # elif (grid_x, grid_y) in build_plate_grid_idx:
                    #     fill_color = "green"
                    # else:
                    #     fill_color = "orange"

                    coord_grid_x, coord_grid_y = self.gridSpaceToCoordSpace(grid_x, grid_y)
                    f.write(
                        f"""
                        <rect
                            x="{coord_grid_x}"
                            y="{coord_grid_y}"
                            width="{self._grid_width}" 
                            height="{self._grid_height}" 
                            fill="#ff00ff88"
                            stroke="black"
                        />
                        """)
                    f.write(f"""
                        <text 
                            font-size="8"
                            x="{coord_grid_x + self._grid_width * 0.5}" 
                            y="{coord_grid_y + self._grid_height * 0.5}"
                        >
                            {grid_x},{grid_y}
                        </text>
                        """)
            for node in self._fixed_nodes:
                bounding_box = node.getBoundingBox()
                f.write(f"""
                    <rect
                        x="{bounding_box.left}" 
                        y="{bounding_box.back}"
                        width="{bounding_box.width}"
                        height="{bounding_box.depth}" 
                        fill="red" 
                    />
                """)
            for node in self._nodes_to_arrange:
                bounding_box = node.getBoundingBox()
                f.write(f"""
                    <rect
                        x="{bounding_box.left}" 
                        y="{bounding_box.back}"
                        width="{bounding_box.width}"
                        height="{bounding_box.depth}" 
                        fill="rgba(0,0,0,0.1)" 
                        stroke="blue"
                        stroke-width="3"
                    />
                """)

            for x in range(math.floor(self._build_volume_bounding_box.left), math.floor(self._build_volume_bounding_box.right), 50):
                for y in range(math.floor(self._build_volume_bounding_box.back), math.floor(self._build_volume_bounding_box.front), 50):
                    color = "green" if self.checkPointUnderDiscSpace(x, y) else "red"
                    f.write(f"""
                      <circle cx="{x}" cy="{y}" r="10" fill="{color}" />
                    """)
            f.write(f"</svg>")