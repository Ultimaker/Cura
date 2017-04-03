import pytest
import numpy
import time

from cura.Arrange import Arrange
from cura.ShapeArray import ShapeArray


def gimmeShapeArray():
    vertices = numpy.array([[-3, 1], [3, 1], [0, -3]])
    shape_arr = ShapeArray.fromPolygon(vertices)
    return shape_arr


def test_smoke_arrange():
    ar = Arrange.create(fixed_nodes = [])


def test_centerFirst():
    ar = Arrange(300, 300, 150, 150)
    ar.centerFirst()
    assert ar._priority[150][150] < ar._priority[170][150]
    assert ar._priority[150][150] < ar._priority[150][170]
    assert ar._priority[150][150] < ar._priority[170][170]
    assert ar._priority[150][150] < ar._priority[130][150]
    assert ar._priority[150][150] < ar._priority[150][130]
    assert ar._priority[150][150] < ar._priority[130][130]


def test_backFirst():
    ar = Arrange(300, 300, 150, 150)
    ar.backFirst()
    assert ar._priority[150][150] < ar._priority[150][170]
    assert ar._priority[150][150] < ar._priority[170][170]
    assert ar._priority[150][150] > ar._priority[150][130]
    assert ar._priority[150][150] > ar._priority[130][130]


def test_smoke_bestSpot():
    ar = Arrange(30, 30, 15, 15)
    ar.centerFirst()

    shape_arr = gimmeShapeArray()
    best_spot = ar.bestSpot(shape_arr)
    assert hasattr(best_spot, "x")
    assert hasattr(best_spot, "y")
    assert hasattr(best_spot, "penalty_points")
    assert hasattr(best_spot, "priority")


def test_smoke_place():
    ar = Arrange(30, 30, 15, 15)
    ar.centerFirst()

    shape_arr = gimmeShapeArray()

    assert not numpy.any(ar._occupied)
    ar.place(0, 0, shape_arr)
    assert numpy.any(ar._occupied)


def test_place_objects():
    ar = Arrange(20, 20, 10, 10)
    ar.centerFirst()
    shape_arr = gimmeShapeArray()
    print(shape_arr)

    now = time.time()
    for i in range(5):
        best_spot_x, best_spot_y, score, prio = ar.bestSpot(shape_arr)
        print(best_spot_x, best_spot_y, score)
        ar.place(best_spot_x, best_spot_y, shape_arr)
        print(ar._occupied)

    print(time.time() - now)
