import numpy

from cura.Arranging.Arrange import Arrange
from cura.Arranging.ShapeArray import ShapeArray


def gimmeShapeArray():
    vertices = numpy.array([[-3, 1], [3, 1], [0, -3]])
    shape_arr = ShapeArray.fromPolygon(vertices)
    return shape_arr


##  Smoke test for Arrange
def test_smoke_arrange():
    ar = Arrange.create(fixed_nodes = [])


##  Smoke test for ShapeArray
def test_smoke_ShapeArray():
    shape_arr = gimmeShapeArray()


##  Test centerFirst
def test_centerFirst():
    ar = Arrange(300, 300, 150, 150)
    ar.centerFirst()
    assert ar._priority[150][150] < ar._priority[170][150]
    assert ar._priority[150][150] < ar._priority[150][170]
    assert ar._priority[150][150] < ar._priority[170][170]
    assert ar._priority[150][150] < ar._priority[130][150]
    assert ar._priority[150][150] < ar._priority[150][130]
    assert ar._priority[150][150] < ar._priority[130][130]


##  Test backFirst
def test_backFirst():
    ar = Arrange(300, 300, 150, 150)
    ar.backFirst()
    assert ar._priority[150][150] < ar._priority[150][170]
    assert ar._priority[150][150] < ar._priority[170][170]
    assert ar._priority[150][150] > ar._priority[150][130]
    assert ar._priority[150][150] > ar._priority[130][130]


##  See if the result of bestSpot has the correct form
def test_smoke_bestSpot():
    ar = Arrange(30, 30, 15, 15)
    ar.centerFirst()

    shape_arr = gimmeShapeArray()
    best_spot = ar.bestSpot(shape_arr)
    assert hasattr(best_spot, "x")
    assert hasattr(best_spot, "y")
    assert hasattr(best_spot, "penalty_points")
    assert hasattr(best_spot, "priority")


##  Try to place an object and see if something explodes
def test_smoke_place():
    ar = Arrange(30, 30, 15, 15)
    ar.centerFirst()

    shape_arr = gimmeShapeArray()

    assert not numpy.any(ar._occupied)
    ar.place(0, 0, shape_arr)
    assert numpy.any(ar._occupied)


##  See of our center has less penalty points than out of the center
def test_checkShape():
    ar = Arrange(30, 30, 15, 15)
    ar.centerFirst()

    shape_arr = gimmeShapeArray()
    points = ar.checkShape(0, 0, shape_arr)
    points2 = ar.checkShape(5, 0, shape_arr)
    points3 = ar.checkShape(0, 5, shape_arr)
    assert points2 > points
    assert points3 > points


## Check that placing an object on occupied place returns None.
def test_checkShape_place():
    ar = Arrange(30, 30, 15, 15)
    ar.centerFirst()

    shape_arr = gimmeShapeArray()
    points = ar.checkShape(3, 6, shape_arr)
    ar.place(3, 6, shape_arr)
    points2 = ar.checkShape(3, 6, shape_arr)

    assert points2 is None


##  Test the whole sequence
def test_smoke_place_objects():
    ar = Arrange(20, 20, 10, 10)
    ar.centerFirst()
    shape_arr = gimmeShapeArray()

    for i in range(5):
        best_spot_x, best_spot_y, score, prio = ar.bestSpot(shape_arr)
        ar.place(best_spot_x, best_spot_y, shape_arr)


##  Polygon -> array
def test_arrayFromPolygon():
    vertices = numpy.array([[-3, 1], [3, 1], [0, -3]])
    array = ShapeArray.arrayFromPolygon([5, 5], vertices)
    assert numpy.any(array)


##  Polygon -> array
def test_arrayFromPolygon2():
    vertices = numpy.array([[-3, 1], [3, 1], [2, -3]])
    array = ShapeArray.arrayFromPolygon([5, 5], vertices)
    assert numpy.any(array)


##  Polygon -> array
def test_fromPolygon():
    vertices = numpy.array([[0, 0.5], [0, 0], [0.5, 0]])
    array = ShapeArray.fromPolygon(vertices, scale=0.5)
    assert numpy.any(array.arr)


##  Line definition -> array with true/false
def test_check():
    base_array = numpy.zeros([5, 5], dtype=float)
    p1 = numpy.array([0, 0])
    p2 = numpy.array([4, 4])
    check_array = ShapeArray._check(p1, p2, base_array)
    assert numpy.any(check_array)
    assert check_array[3][0]
    assert not check_array[0][3]


##  Line definition -> array with true/false
def test_check2():
    base_array = numpy.zeros([5, 5], dtype=float)
    p1 = numpy.array([0, 3])
    p2 = numpy.array([4, 3])
    check_array = ShapeArray._check(p1, p2, base_array)
    assert numpy.any(check_array)
    assert not check_array[3][0]
    assert check_array[3][4]
