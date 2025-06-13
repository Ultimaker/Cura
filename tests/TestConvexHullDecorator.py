import copy
from unittest.mock import patch, MagicMock

import pytest

from UM.Math.Polygon import Polygon
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Scene.GroupDecorator import GroupDecorator
from UM.Scene.SceneNode import SceneNode
from UM.Scene.SceneNodeDecorator import SceneNodeDecorator
from cura.Scene.ConvexHullDecorator import ConvexHullDecorator

mocked_application = MagicMock()
mocked_controller = MagicMock()
# We need to mock out this function, otherwise we get a recursion
mocked_controller.isToolOperationActive = MagicMock(return_value = False)
mocked_application.getController = MagicMock(return_value = mocked_controller)


class NonPrintingDecorator(SceneNodeDecorator):
    def isNonPrintingMesh(self):
        return True


class PrintingDecorator(SceneNodeDecorator):
    def isNonPrintingMesh(self):
        return False


@pytest.fixture
def convex_hull_decorator():
    with patch("cura.CuraApplication.CuraApplication.getInstance", MagicMock(return_value = mocked_application)):
        with patch("UM.Application.Application.getInstance", MagicMock(return_value = mocked_application)):
            with patch("cura.Settings.ExtruderManager.ExtruderManager.getInstance"):
                return ConvexHullDecorator()


def test_getSetNode(convex_hull_decorator):
    node = SceneNode()
    with patch("UM.Application.Application.getInstance", MagicMock(return_value=mocked_application)):
        convex_hull_decorator.setNode(node)
    assert convex_hull_decorator.getNode() == node


def test_getConvexHullBoundaryNoNode(convex_hull_decorator):
    assert convex_hull_decorator.getConvexHullBoundary() is None


def test_getConvexHullHeadNoNode(convex_hull_decorator):
    assert convex_hull_decorator.getConvexHullHead() is None


def test_getConvexHullHeadNotPrintingMesh(convex_hull_decorator):
    node = SceneNode()
    node.addDecorator(NonPrintingDecorator())
    with patch("UM.Application.Application.getInstance", MagicMock(return_value=mocked_application)):
        convex_hull_decorator.setNode(node)
    assert convex_hull_decorator.getConvexHullHead() is None


def test_getConvexHullNoNode(convex_hull_decorator):
    assert convex_hull_decorator.getConvexHull() is None


def test_getConvexHeadFullNoNode(convex_hull_decorator):
    assert convex_hull_decorator.getConvexHullHeadFull() is None


def test_getConvexHullNotPrintingMesh(convex_hull_decorator):
    node = SceneNode()
    node.addDecorator(NonPrintingDecorator())
    with patch("UM.Application.Application.getInstance", MagicMock(return_value=mocked_application)):
        convex_hull_decorator.setNode(node)
    assert convex_hull_decorator.getConvexHull() is None


def test_getConvexHullPrintingMesh(convex_hull_decorator):
    node = SceneNode()
    node.addDecorator(PrintingDecorator())
    with patch("UM.Application.Application.getInstance", MagicMock(return_value=mocked_application)):
        convex_hull_decorator.setNode(node)
    convex_hull_decorator._compute2DConvexHull = MagicMock(return_value = Polygon.approximatedCircle(10))
    assert convex_hull_decorator.getConvexHull() == Polygon.approximatedCircle(10)

def test_getConvexHullBoundaryNotPrintingMesh(convex_hull_decorator):
    node = SceneNode()
    node.addDecorator(NonPrintingDecorator())
    with patch("UM.Application.Application.getInstance", MagicMock(return_value=mocked_application)):
        convex_hull_decorator.setNode(node)
    assert convex_hull_decorator.getConvexHullBoundary() is None


def test_getConvexHulLBoundaryPrintingMesh(convex_hull_decorator):
    node = SceneNode()
    node.addDecorator(PrintingDecorator())
    with patch("UM.Application.Application.getInstance", MagicMock(return_value=mocked_application)):
        convex_hull_decorator.setNode(node)
    # Should still be None, since print sequence is not one at a time
    assert convex_hull_decorator.getConvexHullBoundary() is None


def test_getConvexHulLBoundaryPrintingMeshOneAtATime(convex_hull_decorator):
    node = SceneNode()
    node.addDecorator(PrintingDecorator())
    with patch("UM.Application.Application.getInstance", MagicMock(return_value=mocked_application)):
        convex_hull_decorator.setNode(node)
    convex_hull_decorator._global_stack = MagicMock()
    convex_hull_decorator._global_stack.getProperty = MagicMock(return_value = "one_at_a_time")
    # In this test we don't care for the result of the function, just that the convex hull computation is called.
    convex_hull_decorator._compute2DConvexHull = MagicMock()
    convex_hull_decorator.getConvexHullBoundary()
    convex_hull_decorator._compute2DConvexHull.assert_called_once_with()


def value_changed(convex_hull_decorator, key):
    convex_hull_decorator._onChanged = MagicMock()
    convex_hull_decorator._onSettingValueChanged(key, "value")
    convex_hull_decorator._onChanged.assert_called_once_with()

    # This should have no effect at all
    convex_hull_decorator._onSettingValueChanged(key, "not value")
    convex_hull_decorator._onChanged.assert_called_once_with()


@pytest.mark.parametrize("key", ConvexHullDecorator._affected_settings)
def test_onSettingValueChangedAffectedSettings(convex_hull_decorator, key):
    value_changed(convex_hull_decorator, key)


@pytest.mark.parametrize("key", ConvexHullDecorator._influencing_settings)
def test_onSettingValueChangedInfluencingSettings(convex_hull_decorator, key):
    convex_hull_decorator._init2DConvexHullCache = MagicMock()
    value_changed(convex_hull_decorator, key)
    convex_hull_decorator._init2DConvexHullCache.assert_called_once_with()


def test_compute2DConvexHullNoNode(convex_hull_decorator):
    assert convex_hull_decorator._compute2DConvexHull() is None


def test_compute2DConvexHullNoMeshData(convex_hull_decorator):
    node = SceneNode()
    with patch("UM.Application.Application.getInstance", MagicMock(return_value=mocked_application)):
        convex_hull_decorator.setNode(node)

    assert convex_hull_decorator._compute2DConvexHull() == Polygon([])


def test_compute2DConvexHullMeshData(convex_hull_decorator):
    node = SceneNode()
    mb = MeshBuilder()
    mb.addCube(10, 10, 10)
    node.setMeshData(mb.build())

    convex_hull_decorator._getSettingProperty = MagicMock(return_value = 0)

    with patch("UM.Application.Application.getInstance", MagicMock(return_value=mocked_application)):
        convex_hull_decorator.setNode(node)

    mocked_stack = MagicMock()
    mocked_stack.getProperty = MagicMock(return_value=1)
    convex_hull_decorator._global_stack = mocked_stack

    assert convex_hull_decorator._compute2DConvexHull() == Polygon([[5.0, -5.0], [-5.0, -5.0], [-5.0, 5.0], [5.0, 5.0]])


def test_compute2DConvexHullMeshDataGrouped(convex_hull_decorator):
    parent_node = SceneNode()
    parent_node.addDecorator(GroupDecorator())
    node = SceneNode()
    parent_node.addChild(node)

    mb = MeshBuilder()
    mb.addCube(10, 10, 10)
    node.setMeshData(mb.build())
    mocked_stack = MagicMock()
    mocked_stack.getProperty = MagicMock(return_value=1)
    convex_hull_decorator._global_stack = mocked_stack

    convex_hull_decorator._getSettingProperty = MagicMock(return_value=0)

    with patch("UM.Application.Application.getInstance", MagicMock(return_value=mocked_application)):
        convex_hull_decorator.setNode(parent_node)
        with patch("cura.Settings.ExtruderManager.ExtruderManager.getInstance"):
            copied_decorator = copy.deepcopy(convex_hull_decorator)
            mocked_stack = MagicMock()
            mocked_stack.getProperty = MagicMock(return_value=1)
            copied_decorator._global_stack = mocked_stack
            copied_decorator._getSettingProperty = MagicMock(return_value=0)
        node.addDecorator(copied_decorator)
    assert convex_hull_decorator._compute2DConvexHull() == Polygon([[-5.0, 5.0], [5.0, 5.0], [5.0, -5.0], [-5.0, -5.0]])