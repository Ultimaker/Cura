# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import numpy
import pytest

from cura.Arranging.Arrange import Arrange
from cura.Arranging.ShapeArray import ShapeArray

pytestmark = pytest.mark.skip()

def gimmeTriangle():
    """Triangle of area 12"""

    return numpy.array([[-3, 1], [3, 1], [0, -3]], dtype=numpy.int32)

def gimmeSquare():
    """Boring square"""

    return numpy.array([[-2, -2], [2, -2], [2, 2], [-2, 2]], dtype=numpy.int32)

def gimmeShapeArray(scale = 1.0):
    """Triangle of area 12"""

    vertices = gimmeTriangle()
    shape_arr = ShapeArray.fromPolygon(vertices, scale = scale)
    return shape_arr

def gimmeShapeArraySquare(scale = 1.0):
    """Boring square"""

    vertices = gimmeSquare()
    shape_arr = ShapeArray.fromPolygon(vertices, scale = scale)
    return shape_arr

def test_smoke_arrange():
    """Smoke test for Arrange"""

    Arrange.create(fixed_nodes = [])

def test_smoke_ShapeArray():
    """Smoke test for ShapeArray"""

    gimmeShapeArray()

def test_ShapeArray():
    """Test ShapeArray"""

    scale = 1
    ar = Arrange(16, 16, 8, 8, scale = scale)
    ar.centerFirst()

    shape_arr = gimmeShapeArray(scale)
    count = len(numpy.where(shape_arr.arr == 1)[0])
    assert count >= 10  # should approach 12

def test_ShapeArray_scaling():
    """Test ShapeArray with scaling"""

    scale = 2
    ar = Arrange(16, 16, 8, 8, scale = scale)
    ar.centerFirst()

    shape_arr = gimmeShapeArray(scale)
    count = len(numpy.where(shape_arr.arr == 1)[0])
    assert count >= 40  # should approach 2*2*12 = 48

def test_ShapeArray_scaling2():
    """Test ShapeArray with scaling"""

    scale = 0.5
    ar = Arrange(16, 16, 8, 8, scale = scale)
    ar.centerFirst()

    shape_arr = gimmeShapeArray(scale)
    count = len(numpy.where(shape_arr.arr == 1)[0])
    assert count >= 1  # should approach 3, but it can be inaccurate due to pixel rounding

def test_centerFirst():
    """Test centerFirst"""

    ar = Arrange(300, 300, 150, 150, scale = 1)
    ar.centerFirst()
    assert ar._priority[150][150] < ar._priority[170][150]
    assert ar._priority[150][150] < ar._priority[150][170]
    assert ar._priority[150][150] < ar._priority[170][170]
    assert ar._priority[150][150] < ar._priority[130][150]
    assert ar._priority[150][150] < ar._priority[150][130]
    assert ar._priority[150][150] < ar._priority[130][130]

def test_centerFirst_rectangular():
    """Test centerFirst"""

    ar = Arrange(400, 300, 200, 150, scale = 1)
    ar.centerFirst()
    assert ar._priority[150][200] < ar._priority[150][220]
    assert ar._priority[150][200] < ar._priority[170][200]
    assert ar._priority[150][200] < ar._priority[170][220]
    assert ar._priority[150][200] < ar._priority[180][150]
    assert ar._priority[150][200] < ar._priority[130][200]
    assert ar._priority[150][200] < ar._priority[130][180]

def test_centerFirst_rectangular2():
    """Test centerFirst"""

    ar = Arrange(10, 20, 5, 10, scale = 1)
    ar.centerFirst()
    assert ar._priority[10][5] < ar._priority[10][7]


def test_backFirst():
    """Test backFirst"""

    ar = Arrange(300, 300, 150, 150, scale = 1)
    ar.backFirst()
    assert ar._priority[150][150] < ar._priority[170][150]
    assert ar._priority[150][150] < ar._priority[170][170]
    assert ar._priority[150][150] > ar._priority[130][150]
    assert ar._priority[150][150] > ar._priority[130][130]

def test_smoke_bestSpot():
    """See if the result of bestSpot has the correct form"""

    ar = Arrange(30, 30, 15, 15, scale = 1)
    ar.centerFirst()

    shape_arr = gimmeShapeArray()
    best_spot = ar.bestSpot(shape_arr)
    assert hasattr(best_spot, "x")
    assert hasattr(best_spot, "y")
    assert hasattr(best_spot, "penalty_points")
    assert hasattr(best_spot, "priority")

def test_bestSpot():
    """Real life test"""

    ar = Arrange(16, 16, 8, 8, scale = 1)
    ar.centerFirst()

    shape_arr = gimmeShapeArray()
    best_spot = ar.bestSpot(shape_arr)
    assert best_spot.x == 0
    assert best_spot.y == 0
    ar.place(best_spot.x, best_spot.y, shape_arr)

    # Place object a second time
    best_spot = ar.bestSpot(shape_arr)
    assert best_spot.x is not None  # we found a location
    assert best_spot.x != 0 or best_spot.y != 0  # it can't be on the same location
    ar.place(best_spot.x, best_spot.y, shape_arr)

def test_bestSpot_rectangular_build_plate():
    """Real life test rectangular build plate"""

    ar = Arrange(16, 40, 8, 20, scale = 1)
    ar.centerFirst()

    shape_arr = gimmeShapeArray()
    best_spot = ar.bestSpot(shape_arr)
    ar.place(best_spot.x, best_spot.y, shape_arr)
    assert best_spot.x == 0
    assert best_spot.y == 0

    # Place object a second time
    best_spot2 = ar.bestSpot(shape_arr)
    assert best_spot2.x is not None  # we found a location
    assert best_spot2.x != 0 or best_spot2.y != 0  # it can't be on the same location
    ar.place(best_spot2.x, best_spot2.y, shape_arr)

    # Place object a 3rd time
    best_spot3 = ar.bestSpot(shape_arr)
    assert best_spot3.x is not None  # we found a location
    assert best_spot3.x != best_spot.x or best_spot3.y != best_spot.y  # it can't be on the same location
    assert best_spot3.x != best_spot2.x or best_spot3.y != best_spot2.y  # it can't be on the same location
    ar.place(best_spot3.x, best_spot3.y, shape_arr)

    best_spot_x = ar.bestSpot(shape_arr)
    ar.place(best_spot_x.x, best_spot_x.y, shape_arr)

    best_spot_x = ar.bestSpot(shape_arr)
    ar.place(best_spot_x.x, best_spot_x.y, shape_arr)

    best_spot_x = ar.bestSpot(shape_arr)
    ar.place(best_spot_x.x, best_spot_x.y, shape_arr)

def test_bestSpot_scale():
    """Real life test"""

    scale = 0.5
    ar = Arrange(16, 16, 8, 8, scale = scale)
    ar.centerFirst()

    shape_arr = gimmeShapeArray(scale)
    best_spot = ar.bestSpot(shape_arr)
    assert best_spot.x == 0
    assert best_spot.y == 0
    ar.place(best_spot.x, best_spot.y, shape_arr)

    # Place object a second time
    best_spot = ar.bestSpot(shape_arr)
    assert best_spot.x is not None  # we found a location
    assert best_spot.x != 0 or best_spot.y != 0  # it can't be on the same location
    ar.place(best_spot.x, best_spot.y, shape_arr)

def test_bestSpot_scale_rectangular():
    """Real life test"""

    scale = 0.5
    ar = Arrange(16, 40, 8, 20, scale = scale)
    ar.centerFirst()

    shape_arr = gimmeShapeArray(scale)

    shape_arr_square = gimmeShapeArraySquare(scale)
    best_spot = ar.bestSpot(shape_arr_square)
    assert best_spot.x == 0
    assert best_spot.y == 0
    ar.place(best_spot.x, best_spot.y, shape_arr_square)

    # Place object a second time
    best_spot = ar.bestSpot(shape_arr)
    assert best_spot.x is not None  # we found a location
    assert best_spot.x != 0 or best_spot.y != 0  # it can't be on the same location
    ar.place(best_spot.x, best_spot.y, shape_arr)

    best_spot = ar.bestSpot(shape_arr_square)
    ar.place(best_spot.x, best_spot.y, shape_arr_square)

def test_smoke_place():
    """Try to place an object and see if something explodes"""

    ar = Arrange(30, 30, 15, 15)
    ar.centerFirst()

    shape_arr = gimmeShapeArray()

    assert not numpy.any(ar._occupied)
    ar.place(0, 0, shape_arr)
    assert numpy.any(ar._occupied)

def test_checkShape():
    """See of our center has less penalty points than out of the center"""

    ar = Arrange(30, 30, 15, 15)
    ar.centerFirst()

    shape_arr = gimmeShapeArray()
    points = ar.checkShape(0, 0, shape_arr)
    points2 = ar.checkShape(5, 0, shape_arr)
    points3 = ar.checkShape(0, 5, shape_arr)
    assert points2 > points
    assert points3 > points

def test_checkShape_rectangular():
    """See of our center has less penalty points than out of the center"""

    ar = Arrange(20, 30, 10, 15)
    ar.centerFirst()

    shape_arr = gimmeShapeArray()
    points = ar.checkShape(0, 0, shape_arr)
    points2 = ar.checkShape(5, 0, shape_arr)
    points3 = ar.checkShape(0, 5, shape_arr)
    assert points2 > points
    assert points3 > points

def test_checkShape_place():
    """Check that placing an object on occupied place returns None."""

    ar = Arrange(30, 30, 15, 15)
    ar.centerFirst()

    shape_arr = gimmeShapeArray()
    ar.checkShape(3, 6, shape_arr)
    ar.place(3, 6, shape_arr)
    points2 = ar.checkShape(3, 6, shape_arr)

    assert points2 is None

def test_smoke_place_objects():
    """Test the whole sequence"""

    ar = Arrange(20, 20, 10, 10, scale = 1)
    ar.centerFirst()
    shape_arr = gimmeShapeArray()

    for i in range(5):
        best_spot_x, best_spot_y, score, prio = ar.bestSpot(shape_arr)
        ar.place(best_spot_x, best_spot_y, shape_arr)

# Test some internals
def test_compare_occupied_and_priority_tables():
    ar = Arrange(10, 15, 5, 7)
    ar.centerFirst()
    assert ar._priority.shape == ar._occupied.shape

def test_arrayFromPolygon():
    """Polygon -> array"""

    vertices = numpy.array([[-3, 1], [3, 1], [0, -3]])
    array = ShapeArray.arrayFromPolygon([5, 5], vertices)
    assert numpy.any(array)

def test_arrayFromPolygon2():
    """Polygon -> array"""

    vertices = numpy.array([[-3, 1], [3, 1], [2, -3]])
    array = ShapeArray.arrayFromPolygon([5, 5], vertices)
    assert numpy.any(array)

def test_fromPolygon():
    """Polygon -> array"""

    vertices = numpy.array([[0, 0.5], [0, 0], [0.5, 0]])
    array = ShapeArray.fromPolygon(vertices, scale=0.5)
    assert numpy.any(array.arr)

def test_check():
    """Line definition -> array with true/false"""

    base_array = numpy.zeros([5, 5], dtype=float)
    p1 = numpy.array([0, 0])
    p2 = numpy.array([4, 4])
    check_array = ShapeArray._check(p1, p2, base_array)
    assert numpy.any(check_array)
    assert check_array[3][0]
    assert not check_array[0][3]

def test_check2():
    """Line definition -> array with true/false"""

    base_array = numpy.zeros([5, 5], dtype=float)
    p1 = numpy.array([0, 3])
    p2 = numpy.array([4, 3])
    check_array = ShapeArray._check(p1, p2, base_array)
    assert numpy.any(check_array)
    assert not check_array[3][0]
    assert check_array[3][4]

def test_parts_of_fromNode():
    """Just adding some stuff to ensure fromNode works as expected. Some parts should actually be in UM"""

    from UM.Math.Polygon import Polygon
    p = Polygon(numpy.array([[-2, -2], [2, -2], [2, 2], [-2, 2]], dtype=numpy.int32))
    offset = 1
    p_offset = p.getMinkowskiHull(Polygon.approximatedCircle(offset))
    assert len(numpy.where(p_offset._points[:, 0] >= 2.9)) > 0
    assert len(numpy.where(p_offset._points[:, 0] <= -2.9)) > 0
    assert len(numpy.where(p_offset._points[:, 1] >= 2.9)) > 0
    assert len(numpy.where(p_offset._points[:, 1] <= -2.9)) > 0

def test_parts_of_fromNode2():
    from UM.Math.Polygon import Polygon
    p = Polygon(numpy.array([[-2, -2], [2, -2], [2, 2], [-2, 2]], dtype=numpy.int32) * 2)  # 4x4
    offset = 13.3
    scale = 0.5
    p_offset = p.getMinkowskiHull(Polygon.approximatedCircle(offset))
    shape_arr1 = ShapeArray.fromPolygon(p._points, scale = scale)
    shape_arr2 = ShapeArray.fromPolygon(p_offset._points, scale = scale)
    assert shape_arr1.arr.shape[0] >= (4 * scale) - 1  # -1 is to account for rounding errors
    assert shape_arr2.arr.shape[0] >= (2 * offset + 4) * scale - 1