from unittest.mock import MagicMock

import numpy
import pytest

from UM.Math.Matrix import Matrix
from UM.Math.Vector import Vector
from UM.Scene.SceneNode import SceneNode
from cura.Scene.ConvexHullNode import ConvexHullNode
from cura.Scene.ConvexHullDecorator import ConvexHullDecorator


def make_footprint():
    source = MagicMock()
    source.getWorldTransformation.return_value = Matrix()
    source.getMeshData.return_value = object()
    shadow = ConvexHullNode.__new__(ConvexHullNode)
    SceneNode.__init__(shadow)
    shadow._node = source
    shadow._source_mesh = source.getMeshData()
    shadow._source_world_transform = Matrix()
    return source, shadow


def test_translation_follows_model_without_mutating_cached_transform():
    source, shadow = make_footprint()
    for x in range(100):
        source.getWorldTransformation.return_value.setTranslation(Vector(x, 7, -x))
        assert shadow.getWorldTransformation(copy = False).getTranslation() == Vector(x, 0, -x)
    assert shadow._world_transformation.getTranslation() == Vector()


def test_rotation_and_mesh_replacement_use_geometry_refresh():
    source, shadow = make_footprint()
    data = numpy.eye(4)
    data[0, 0] = 2
    source.getWorldTransformation.return_value = Matrix(data)
    assert shadow.getTranslationDelta() is None
    source.getWorldTransformation.return_value = Matrix()
    source.getMeshData.return_value = object()
    assert shadow.getTranslationDelta() is None


def test_translation_roundoff_does_not_force_geometry_rebuild():
    source, shadow = make_footprint()
    data = numpy.eye(4)
    data[0, 0] += 1e-14
    data[:3, 3] = [5, 0, 9]
    source.getWorldTransformation.return_value = Matrix(data)
    assert shadow.getTranslationDelta() == Vector(5, 0, 9)


def test_unchanged_group_translates_but_child_changes_invalidate_cache():
    source = SceneNode()
    child = SceneNode()
    child._mesh_data = object()
    source._children = [child]
    child._parent = source
    shadow = ConvexHullNode.__new__(ConvexHullNode)
    SceneNode.__init__(shadow)
    shadow._node = source
    shadow._source_mesh = None
    shadow._source_world_transform = Matrix()
    shadow._source_descendants = ((child, child.getMeshData(), source, child.getLocalTransformation()),)
    source._world_transformation.setTranslation(Vector(12, 0, 7))
    assert shadow.getTranslationDelta() == Vector(12, 0, 7)
    child._transformation.setTranslation(Vector(1, 0, 0))
    assert shadow.getTranslationDelta() is None
def test_geometry_timer_is_throttled_instead_of_debounced():
    decorator = ConvexHullDecorator.__new__(ConvexHullDecorator)
    timer = MagicMock()
    timer.isActive.return_value = True
    timer.remainingTime.return_value = 8
    decorator._recompute_convex_hull_timer = timer
    decorator._convex_hull_node = None
    for _ in range(100):
        decorator.recomputeConvexHullDelayed()
    timer.start.assert_not_called()
    timer.isActive.return_value = False
    decorator.recomputeConvexHullDelayed()
    timer.start.assert_called_once_with(16)


def test_pending_debounce_is_promoted_when_shape_changes():
    decorator = ConvexHullDecorator.__new__(ConvexHullDecorator)
    timer = MagicMock()
    timer.isActive.return_value = True
    timer.remainingTime.return_value = 150
    decorator._recompute_convex_hull_timer = timer
    decorator._convex_hull_node = None
    decorator.recomputeConvexHullDelayed()
    timer.start.assert_called_once_with(16)
