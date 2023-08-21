import math
from typing import List, TYPE_CHECKING, Optional, Tuple, Set

from UM.Application import Application
from UM.Math import AxisAlignedBox
from UM.Math.Vector import Vector
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.TranslateOperation import TranslateOperation


class GridArrange:
    offset_x: float = 10
    offset_y: float = 10

    _grid_width: float
    _grid_height: float

    _nodes_to_arrange: List["SceneNode"]
    _fixed_nodes: List["SceneNode"]
    _build_volume_bounding_box = AxisAlignedBox

    def __init__(self, nodes_to_arrange: List["SceneNode"], build_volume: "BuildVolume", fixed_nodes: List["SceneNode"] = []):
        print("len(nodes_to_arrange)", len(nodes_to_arrange))
        self._nodes_to_arrange = nodes_to_arrange
        self._build_volume_bounding_box = build_volume.getBoundingBox()
        self._fixed_nodes = fixed_nodes

    def arrange(self) -> Tuple[GroupedOperation, int]:
        self._grid_width = 0
        self._grid_height = 0
        for node in self._nodes_to_arrange:
            bounding_box = node.getBoundingBox()
            self._grid_width = max(self._grid_width, bounding_box.width)
            self._grid_height = max(self._grid_height, bounding_box.depth)

        # Find grid indexes that intersect with fixed objects
        fixed_nodes_grid_ids = set()
        for node in self._fixed_nodes:
            fixed_nodes_grid_ids = fixed_nodes_grid_ids.union(self.intersectingGridIdxInclusive(node.getBoundingBox()))

        build_plate_grid_ids = self.intersectingGridIdxExclusive(self._build_volume_bounding_box)
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

            coord_grid_x, coord_grid_y = self.gridSpaceToCoordSpace(grid_x, grid_y)
            center_grid_x = coord_grid_x+(0.5 * self._grid_width)
            center_grid_y = coord_grid_y+(0.5 * self._grid_height)

            bounding_box = node.getBoundingBox()
            center_node_x = (bounding_box.left + bounding_box.right) * 0.5
            center_node_y = (bounding_box.back + bounding_box.front) * 0.5

            delta_x = center_grid_x - center_node_x
            delta_y = center_grid_y - center_node_y
            grouped_operation.addOperation(TranslateOperation(node, Vector(delta_x, 0, delta_y)))

        self.drawDebugSvg()

        return grouped_operation, 0

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
        grid_x = x * (self._grid_width + self.offset_x) + self._build_volume_bounding_box.left
        grid_y = y * (self._grid_height + self.offset_y) + self._build_volume_bounding_box.back
        return grid_x, grid_y

    def coordSpaceToGridSpace(self, grid_x: float, grid_y: float) -> Tuple[float, float]:
        coord_x = (grid_x - self._build_volume_bounding_box.left) / (self._grid_width + self.offset_x)
        coord_y = (grid_y - self._build_volume_bounding_box.back) / (self._grid_height + self.offset_y)
        return coord_x, coord_y

    def drawDebugSvg(self):
        with open("Builvolume_test.svg", "w") as f:
            build_volume_bounding_box = self._build_volume_bounding_box

            f.write(
                f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='{build_volume_bounding_box.left - 100} {build_volume_bounding_box.back - 100} {build_volume_bounding_box.width + 200} {build_volume_bounding_box.depth + 200}'>\n")

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

            for grid_x in range(-10, 10):
                for grid_y in range(-10, 10):
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
                            fill="green"
                            stroke="black"
                        />
                        """)
                    f.write(f"""
                        <text 
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
            f.write(f"</svg>")
