import pytest

from unittest.mock import patch, MagicMock

from UM.Scene.GroupDecorator import GroupDecorator
from UM.Scene.SceneNode import SceneNode
from cura.Scene.BuildPlateDecorator import BuildPlateDecorator
from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator
from cura.UI.ObjectsModel import ObjectsModel


@pytest.fixture()
def objects_model(application):
    with patch("UM.Application.Application.getInstance", MagicMock(return_value=application)):
        return ObjectsModel()


@pytest.fixture()
def group_scene_node():
    node = SceneNode()
    node.addDecorator(GroupDecorator())
    return node


@pytest.fixture()
def slicable_scene_node():
    node = SceneNode()
    node.addDecorator(SliceableObjectDecorator())
    return node


def test_setActiveBuildPlate(objects_model):
    objects_model._update = MagicMock()

    objects_model.setActiveBuildPlate(12)
    assert objects_model._update.call_count == 1

    objects_model.setActiveBuildPlate(12)
    assert objects_model._update.call_count == 1


class Test_shouldNodeBeHandled:
    def test_nonSlicableSceneNode(self, objects_model):
        # An empty SceneNode should not be handled by this model
        assert not objects_model._shouldNodeBeHandled(SceneNode())

    def test_groupedNode(self, objects_model, slicable_scene_node, application):
        with patch("UM.Application.Application.getInstance", MagicMock(return_value=application)):
            # A node without a build plate number should not be handled.
            assert not objects_model._shouldNodeBeHandled(slicable_scene_node)

    def test_childNode(self, objects_model, group_scene_node, slicable_scene_node, application):
        slicable_scene_node.setParent(group_scene_node)
        with patch("UM.Application.Application.getInstance", MagicMock(return_value=application)):
            # A child node of a group node should not be handled.
            assert not objects_model._shouldNodeBeHandled(slicable_scene_node)

    def test_slicableNodeWithoutFiltering(self, objects_model, slicable_scene_node, application):
        mocked_preferences = MagicMock(name="preferences")
        mocked_preferences.getValue = MagicMock(return_value = False)
        application.getPreferences = MagicMock(return_value = mocked_preferences)

        with patch("UM.Application.Application.getInstance", MagicMock(return_value=application)):
            # A slicable node should be handled by this model.
            assert objects_model._shouldNodeBeHandled(slicable_scene_node)

    def test_slicableNodeWithFiltering(self, objects_model, slicable_scene_node, application):
        mocked_preferences = MagicMock(name="preferences")
        mocked_preferences.getValue = MagicMock(return_value = True)
        application.getPreferences = MagicMock(return_value = mocked_preferences)

        buildplate_decorator = BuildPlateDecorator()
        buildplate_decorator.setBuildPlateNumber(-1)
        slicable_scene_node.addDecorator(buildplate_decorator)

        with patch("UM.Application.Application.getInstance", MagicMock(return_value=application)):
            # A slicable node with the same buildplate number should be handled.
            assert objects_model._shouldNodeBeHandled(slicable_scene_node)
