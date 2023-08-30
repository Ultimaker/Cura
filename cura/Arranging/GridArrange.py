import math
from typing import List, TYPE_CHECKING, Tuple, Set

if TYPE_CHECKING:
    from UM.Scene.SceneNode import SceneNode
    from cura.BuildVolume import BuildVolume

from UM.Application import Application
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

        self._margin_x: float = 1
        self._margin_y: float = 1

        self._grid_width = 0
        self._grid_height = 0
        for node in self._nodes_to_arrange:
            bounding_box = node.getBoundingBox()
            self._grid_width = max(self._grid_width, bounding_box.width)
            self._grid_height = max(self._grid_height, bounding_box.depth)
        self._grid_width += self._margin_x
        self._grid_height += self._margin_y

        # Round up the grid size to the nearest cm
        grid_precision = 10  # 1cm
        self._grid_width = math.ceil(self._grid_width / grid_precision) * grid_precision
        self._grid_height = math.ceil(self._grid_height / grid_precision) * grid_precision

        self._offset_x = 0
        self._offset_y = 0
        self._findOptimalGridOffset()

        coord_initial_leftover_x = self._build_volume_bounding_box.right + 2 * self._grid_width
        coord_initial_leftover_y = (self._build_volume_bounding_box.back + self._build_volume_bounding_box.front) * 0.5
        self._initial_leftover_grid_x, self._initial_leftover_grid_y = self.coordSpaceToGridSpace(coord_initial_leftover_x, coord_initial_leftover_y)
        self._initial_leftover_grid_x = math.floor(self._initial_leftover_grid_x)
        self._initial_leftover_grid_y = math.floor(self._initial_leftover_grid_y)

        # Find grid indexes that intersect with fixed objects
        self._fixed_nodes_grid_ids = set()
        for node in self._fixed_nodes:
            self._fixed_nodes_grid_ids = self._fixed_nodes_grid_ids.union(
                self.intersectingGridIdxInclusive(node.getBoundingBox()))

        #grid indexes that are in disallowed area
        for polygon in self._build_volume.getDisallowedAreas():
            self._fixed_nodes_grid_ids = self._fixed_nodes_grid_ids.union(
            self._getIntersectingGridIdForPolygon(polygon))

        self._build_plate_grid_ids = self.intersectingGridIdxExclusive(self._build_volume_bounding_box)

        # Filter out the corner grid squares if the build plate shape is elliptic
        if self._build_volume.getShape() == "elliptic":
            self._build_plate_grid_ids = set(
                filter(lambda grid_id: self.checkGridUnderDiscSpace(grid_id[0], grid_id[1]),
                       self._build_plate_grid_ids))

        self._allowed_grid_idx = self._build_plate_grid_ids.difference(self._fixed_nodes_grid_ids)

    def createGroupOperationForArrange(self, add_new_nodes_in_scene: bool = False) -> Tuple[GroupedOperation, int]:
        # Find the sequence in which items are placed
        coord_build_plate_center_x = self._build_volume_bounding_box.width * 0.5 + self._build_volume_bounding_box.left
        coord_build_plate_center_y = self._build_volume_bounding_box.depth * 0.5 + self._build_volume_bounding_box.back
        grid_build_plate_center_x, grid_build_plate_center_y = self.coordSpaceToGridSpace(coord_build_plate_center_x, coord_build_plate_center_y)

        sequence: List[Tuple[int, int]] = list(self._allowed_grid_idx)
        sequence.sort(key=lambda grid_id: (grid_build_plate_center_x - grid_id[0]) ** 2 + (
                    grid_build_plate_center_y - grid_id[1]) ** 2)
        scene_root = Application.getInstance().getController().getScene().getRoot()
        grouped_operation = GroupedOperation()

        for grid_id, node in zip(sequence, self._nodes_to_arrange):
            if add_new_nodes_in_scene:
                grouped_operation.addOperation(AddSceneNodeOperation(node, scene_root))
            grid_x, grid_y = grid_id
            operation = self._moveNodeOnGrid(node, grid_x, grid_y)
            grouped_operation.addOperation(operation)

        leftover_nodes = self._nodes_to_arrange[len(sequence):]

        left_over_grid_y = self._initial_leftover_grid_y
        for node in leftover_nodes:
            if add_new_nodes_in_scene:
                grouped_operation.addOperation(AddSceneNodeOperation(node, scene_root))
            # find the first next grid position that isn't occupied by a fixed node
            while (self._initial_leftover_grid_x, left_over_grid_y) in self._fixed_nodes_grid_ids:
                left_over_grid_y = left_over_grid_y - 1

            operation = self._moveNodeOnGrid(node, self._initial_leftover_grid_x, left_over_grid_y)
            grouped_operation.addOperation(operation)
            left_over_grid_y = left_over_grid_y - 1

        return grouped_operation, len(leftover_nodes)

    def _findOptimalGridOffset(self):
        if len(self._fixed_nodes) == 0:
            self._offset_x = 0
            self._offset_y = 0
            return

        if len(self._fixed_nodes) == 1:
            center_grid_x = 0.5 * self._grid_width + self._build_volume_bounding_box.left
            center_grid_y = 0.5 * self._grid_height + self._build_volume_bounding_box.back

            bounding_box = self._fixed_nodes[0].getBoundingBox()
            center_node_x = (bounding_box.left + bounding_box.right) * 0.5
            center_node_y = (bounding_box.back + bounding_box.front) * 0.5

            self._offset_x = center_node_x - center_grid_x
            self._offset_y = center_node_y - center_grid_y

            return

        # If there are multiple fixed nodes, an optimal solution is not always possible
        # We will try to find an offset that minimizes the number of grid intersections
        # with fixed nodes. The algorithm below achieves this by utilizing a scanline
        # algorithm. In this algorithm each axis is solved separately as offsetting
        # is completely independent in each axis. The comments explaining the algorithm
        # below are for the x-axis, but the same applies for the y-axis.
        #
        # Each node either occupies ceil((node.right - node.right) / grid_width) or
        # ceil((node.right - node.right) / grid_width) + 1 grid squares. We will call
        # these the node's "footprint".
        #
        #                      ┌────────────────┐
        #   minimum food print │      NODE      │
        #                      └────────────────┘
        # │    grid 1   │    grid 2    │    grid 3    │    grid 4    |    grid 5    |
        #                             ┌────────────────┐
        #          maximum food print │      NODE      │
        #                             └────────────────┘
        #
        # The algorithm will find the grid offset such that the number of nodes with
        # a _minimal_ footprint is _maximized_.

        # The scanline algorithm works as follows, we create events for both end points
        # of each node's footprint. The event have two properties,
        # - the coordinate: the amount the endpoint can move to the
        #      left before it crosses a grid line
        # - the change: either +1 or -1, indicating whether crossing the grid line
        #      would result in a minimal footprint node becoming a maximal footprint
        class Event:
            def __init__(self, coord: float, change: float):
                self.coord = coord
                self.change = change

        # create events for both the horizontal and vertical axis
        events_horizontal: List[Event] = []
        events_vertical: List[Event] = []

        for node in self._fixed_nodes:
            bounding_box = node.getBoundingBox()

            left = bounding_box.left - self._build_volume_bounding_box.left
            right = bounding_box.right - self._build_volume_bounding_box.left
            back = bounding_box.back - self._build_volume_bounding_box.back
            front = bounding_box.front - self._build_volume_bounding_box.back

            value_left = math.ceil(left / self._grid_width) * self._grid_width - left
            value_right = math.ceil(right / self._grid_width) * self._grid_width - right
            value_back = math.ceil(back / self._grid_height) * self._grid_height - back
            value_front = math.ceil(front / self._grid_height) * self._grid_height - front

            # give nodes a weight according to their size. This
            # weight is heuristically chosen to be proportional to
            # the number of grid squares the node-boundary occupies
            weight = bounding_box.width + bounding_box.depth

            events_horizontal.append(Event(value_left, weight))
            events_horizontal.append(Event(value_right, -weight))
            events_vertical.append(Event(value_back, weight))
            events_vertical.append(Event(value_front, -weight))

        events_horizontal.sort(key=lambda event: event.coord)
        events_vertical.sort(key=lambda event: event.coord)

        def findOptimalShiftAxis(events: List[Event], interval: float) -> float:
            # executing the actual scanline algorithm
            # iteratively go through events (left to right) and keep track of the
            # current footprint. The optimal location is the one with the minimal
            # footprint. If there are multiple locations with the same minimal
            # footprint, the optimal location is the one with the largest range
            # between the left and right endpoint of the footprint.
            prev_offset = events[-1].coord - interval
            current_minimal_footprint_count = 0

            best_minimal_footprint_count = float('inf')
            best_offset_span = float('-inf')
            best_offset = 0.0

            for event in events:
                offset_span = event.coord - prev_offset

                if current_minimal_footprint_count < best_minimal_footprint_count or (
                        current_minimal_footprint_count == best_minimal_footprint_count and offset_span > best_offset_span):
                    best_minimal_footprint_count = current_minimal_footprint_count
                    best_offset_span = offset_span
                    best_offset = event.coord

                current_minimal_footprint_count += event.change
                prev_offset = event.coord

            return best_offset - best_offset_span * 0.5

        center_grid_x = 0.5 * self._grid_width
        center_grid_y = 0.5 * self._grid_height

        optimal_center_x = self._grid_width - findOptimalShiftAxis(events_horizontal, self._grid_width)
        optimal_center_y = self._grid_height - findOptimalShiftAxis(events_vertical, self._grid_height)

        self._offset_x = optimal_center_x - center_grid_x
        self._offset_y = optimal_center_y - center_grid_y

    def _moveNodeOnGrid(self, node: "SceneNode", grid_x: int, grid_y: int) -> "Operation.Operation":
        coord_grid_x, coord_grid_y = self._gridSpaceToCoordSpace(grid_x, grid_y)
        center_grid_x = coord_grid_x + (0.5 * self._grid_width)
        center_grid_y = coord_grid_y + (0.5 * self._grid_height)

        bounding_box = node.getBoundingBox()
        center_node_x = (bounding_box.left + bounding_box.right) * 0.5
        center_node_y = (bounding_box.back + bounding_box.front) * 0.5

        delta_x = center_grid_x - center_node_x
        delta_y = center_grid_y - center_node_y

        return TranslateOperation(node, Vector(delta_x, 0, delta_y))

    def _getGridCornerPoints(self, bounding_box: "BoundingVolume") -> Tuple[float, float, float, float]:
        coord_x1 = bounding_box.left
        coord_x2 = bounding_box.right
        coord_y1 = bounding_box.back
        coord_y2 = bounding_box.front
        grid_x1, grid_y1 = self.coordSpaceToGridSpace(coord_x1, coord_y1)
        grid_x2, grid_y2 = self.coordSpaceToGridSpace(coord_x2, coord_y2)
        return grid_x1, grid_y1, grid_x2, grid_y2

    def _getIntersectingGridIdForPolygon(self, polygon)-> Set[Tuple[int, int]]:
        #       (x0, y0)
        #       |
        #       v
        #       ┌─────────────┐
        #       │             │
        #       │             │
        #       └─────────────┘  < (x1, y1)
        x0 = float('inf')
        y0 = float('inf')
        x1 = float('-inf')
        y1 = float('-inf')
        grid_idx = set()
        for [x, y] in polygon.getPoints():
            x0 = min(x0, x)
            y0 = min(y0, y)
            x1 = max(x1, x)
            y1 = max(y1, y)
        grid_x1, grid_y1 = self.coordSpaceToGridSpace(x0, y0)
        grid_x2, grid_y2 = self.coordSpaceToGridSpace(x1, y1)

        for grid_x in range(math.floor(grid_x1), math.ceil(grid_x2)):
            for grid_y in range(math.floor(grid_y1), math.ceil(grid_y2)):
                grid_idx.add((grid_x, grid_y))
        return grid_idx

    def intersectingGridIdxInclusive(self, bounding_box: "BoundingVolume") -> Set[Tuple[int, int]]:
        grid_x1, grid_y1, grid_x2, grid_y2 = self._getGridCornerPoints(bounding_box)
        grid_idx = set()
        for grid_x in range(math.floor(grid_x1), math.ceil(grid_x2)):
            for grid_y in range(math.floor(grid_y1), math.ceil(grid_y2)):
                grid_idx.add((grid_x, grid_y))
        return grid_idx

    def intersectingGridIdxExclusive(self, bounding_box: "BoundingVolume") -> Set[Tuple[int, int]]:
        grid_x1, grid_y1, grid_x2, grid_y2 = self._getGridCornerPoints(bounding_box)
        grid_idx = set()
        for grid_x in range(math.ceil(grid_x1), math.floor(grid_x2)):
            for grid_y in range(math.ceil(grid_y1), math.floor(grid_y2)):
                grid_idx.add((grid_x, grid_y))
        return grid_idx

    def _gridSpaceToCoordSpace(self, x: float, y: float) -> Tuple[float, float]:
        grid_x = x * self._grid_width + self._build_volume_bounding_box.left + self._offset_x
        grid_y = y * self._grid_height + self._build_volume_bounding_box.back + self._offset_y
        return grid_x, grid_y

    def coordSpaceToGridSpace(self, grid_x: float, grid_y: float) -> Tuple[float, float]:
        coord_x = (grid_x - self._build_volume_bounding_box.left - self._offset_x) / self._grid_width
        coord_y = (grid_y - self._build_volume_bounding_box.back - self._offset_y) / self._grid_height
        return coord_x, coord_y

    def checkGridUnderDiscSpace(self, grid_x: int, grid_y: int) -> bool:
        left, back = self._gridSpaceToCoordSpace(grid_x, grid_y)
        right, front = self._gridSpaceToCoordSpace(grid_x + 1, grid_y + 1)
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

    def _drawDebugSvg(self):
        with open("Builvolume_test.svg", "w") as f:
            build_volume_bounding_box = self._build_volume_bounding_box

            f.write(
                f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='{build_volume_bounding_box.left - 100} {build_volume_bounding_box.back - 100} {build_volume_bounding_box.width + 200} {build_volume_bounding_box.depth + 200}'>\n")

            if self._build_volume.getShape() == "elliptic":
                f.write(
                    f"""
                    <ellipse
                        cx='{(build_volume_bounding_box.left + build_volume_bounding_box.right) * 0.5}'
                        cy='{(build_volume_bounding_box.back + build_volume_bounding_box.front) * 0.5}'
                        rx='{build_volume_bounding_box.width * 0.5}' 
                        ry='{build_volume_bounding_box.depth * 0.5}' 
                        fill=\"lightgrey\"
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

            for polygon in self._build_volume.getDisallowedAreas():
                    # Extract individual points and convert them to tuples

                path_data = ""
                for [x,y] in polygon.getPoints():
                        path_data += f"{x},{y} "

                f.write(
                        f"""
                        <polygon 
                        points='{path_data}' 
                        fill='#ff648888' 
                        stroke='black' 
                        stroke-width='2' 
                        />
                    """)

            for grid_x in range(-10, 100):
                for grid_y in range(-10, 100):
                    if (grid_x, grid_y) in self._allowed_grid_idx:
                        fill_color = "rgba(0, 255, 0, 0.5)"
                    elif (grid_x, grid_y) in self._build_plate_grid_ids:
                        fill_color = "rgba(255, 165, 0, 0.5)"
                    else:
                        fill_color = "rgba(255, 0, 0, 0.5)"

                    coord_grid_x, coord_grid_y = self._gridSpaceToCoordSpace(grid_x, grid_y)
                    f.write(
                        f"""
                        <rect
                            x="{coord_grid_x + self._margin_x * 0.5}"
                            y="{coord_grid_y + self._margin_y * 0.5}"
                            width="{self._grid_width - self._margin_x}" 
                            height="{self._grid_height - self._margin_y}" 
                            fill="{fill_color}"
                            stroke="black"
                        />
                        """)
                    f.write(f"""
                        <text 
                            font-size="4"
                            text-anchor="middle"
                            alignment-baseline="middle"
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

            f.write(f"""
                <circle 
                    cx="{self._offset_x}" 
                    cy="{self._offset_y}" 
                    r="2" 
                    stroke="red"
                    fill="none" 
                />""")

            # coord_build_plate_center_x = self._build_volume_bounding_box.width * 0.5 + self._build_volume_bounding_box.left
            # coord_build_plate_center_y = self._build_volume_bounding_box.depth * 0.5 + self._build_volume_bounding_box.back
            # f.write(f"""
            #     <circle
            #         cx="{coord_build_plate_center_x}"
            #         cy="{coord_build_plate_center_y}"
            #         r="2"
            #         stroke="blue"
            #         fill="none"
            #     />""")

            f.write(f"</svg>")
