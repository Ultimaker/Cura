import pytest
import copy
from unittest.mock import patch, MagicMock

from UM.Scene.GroupDecorator import GroupDecorator
from UM.Scene.SceneNode import SceneNode
from cura.Scene.BuildPlateDecorator import BuildPlateDecorator
from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator
from cura.UI.ObjectsModel import ObjectsModel, _NodeInfo


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

@pytest.fixture()
def application_with_mocked_scene(application):
    mocked_controller = MagicMock(name = "Controller")
    mocked_scene = MagicMock(name = "Scene")
    mocked_controller.getScene = MagicMock(return_value = mocked_scene)
    application.getController = MagicMock(return_value = mocked_controller)
    return application


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


class Test_renameNodes:
    def test_emptyDict(self, objects_model):
        assert objects_model._renameNodes({}) == []

    def test_singleItemNoRename(self, objects_model):
        node = SceneNode()
        assert objects_model._renameNodes({"zomg": _NodeInfo(index_to_node={1: node})}) == [node]

    def test_singleItemRename(self, objects_model):
        node = SceneNode()
        result = objects_model._renameNodes({"zomg": _NodeInfo(nodes_to_rename=[node])})
        assert result == [node]
        assert node.getName() == "zomg(1)"

    def test_singleItemRenameWithIndex(self, objects_model):
        node = SceneNode()
        objects_model._renameNodes({"zomg": _NodeInfo(index_to_node = {1: node}, nodes_to_rename=[node])})
        assert node.getName() == "zomg(2)"

    def test_multipleItemsRename(self, objects_model):
        node1 = SceneNode()
        node2 = SceneNode()
        result = objects_model._renameNodes({"zomg": _NodeInfo(nodes_to_rename=[node1, node2])})
        assert result == [node1, node2]
        assert node1.getName() == "zomg(1)"
        assert node2.getName() == "zomg(2)"

    def test_renameGroup(self, objects_model, group_scene_node):
        result = objects_model._renameNodes({"zomg": _NodeInfo(nodes_to_rename=[group_scene_node], is_group=True)})
        assert result == [group_scene_node]
        assert group_scene_node.getName() == "zomg#1"


class Test_Update:
    def test_updateWithGroup(self, objects_model, application_with_mocked_scene, group_scene_node):
        objects_model._shouldNodeBeHandled = MagicMock(return_value = True)
        application_with_mocked_scene.getController().getScene().getRoot = MagicMock(return_value = group_scene_node)
        with patch("UM.Application.Application.getInstance", MagicMock(return_value=application_with_mocked_scene)):
            objects_model._update()
            assert objects_model.items == [{
                'name': 'Group #1',
                'selected': False,
                'outside_build_area': False,
                'buildplate_number': None,
                'node': group_scene_node,
                "extruder_number": -1,
                "per_object_settings_count": 0,
                "mesh_type": ""
            }]

    def test_updateWithNonGroup(self, objects_model, application_with_mocked_scene, slicable_scene_node):
        objects_model._shouldNodeBeHandled = MagicMock(return_value=True)
        slicable_scene_node.setName("YAY(1)")
        application_with_mocked_scene.getController().getScene().getRoot = MagicMock(return_value=slicable_scene_node)
        with patch("UM.Application.Application.getInstance", MagicMock(return_value=application_with_mocked_scene)):
            objects_model._update()
            assert objects_model.items == [{
                'name': 'YAY(1)',
                'selected': False,
                'outside_build_area': False,
                'buildplate_number': None,
                'node': slicable_scene_node,
                "extruder_number": -1,
                "per_object_settings_count": 0,
                "mesh_type": ""
            }]

    def test_updateWithNonTwoNodes(self, objects_model, application_with_mocked_scene, slicable_scene_node):
        objects_model._shouldNodeBeHandled = MagicMock(return_value=True)
        slicable_scene_node.setName("YAY")
        copied_node = copy.deepcopy(slicable_scene_node)
        copied_node.setParent(slicable_scene_node)
        application_with_mocked_scene.getController().getScene().getRoot = MagicMock(return_value=slicable_scene_node)
        with patch("UM.Application.Application.getInstance", MagicMock(return_value=application_with_mocked_scene)):
            objects_model._update()
            assert objects_model.items == [{
                'name': 'YAY',
                'selected': False,
                'outside_build_area': False,
                'buildplate_number': None,
                'node': slicable_scene_node,
                "extruder_number": -1,
                "per_object_settings_count": 0,
                "mesh_type": ""
            }, {
                'name': 'YAY(1)',
                'selected': False,
                'outside_build_area': False,
                'buildplate_number': None,
                'node': copied_node,
                "extruder_number": -1,
                "per_object_settings_count": 0,
                "mesh_type": ""
            }]

    def test_updateWithNonTwoGroups(self, objects_model, application_with_mocked_scene, group_scene_node):
        objects_model._shouldNodeBeHandled = MagicMock(return_value=True)
        group_scene_node.setName("Group #1")
        copied_node = copy.deepcopy(group_scene_node)
        copied_node.setParent(group_scene_node)
        application_with_mocked_scene.getController().getScene().getRoot = MagicMock(return_value=group_scene_node)
        with patch("UM.Application.Application.getInstance", MagicMock(return_value=application_with_mocked_scene)):
            objects_model._update()
            assert objects_model.items == [{
                'name': 'Group #1',
                'selected': False,
                'outside_build_area': False,
                'buildplate_number': None,
                'node': group_scene_node,
                "extruder_number": -1,
                "per_object_settings_count": 0,
                "mesh_type": ""
            }, {
                'name': 'Group #2',
                'selected': False,
                'outside_build_area': False,
                'buildplate_number': None,
                'node': copied_node,
                "extruder_number": -1,
                "per_object_settings_count": 0,
                "mesh_type": ""
            }]

    def test_updateOutsideBuildplate(self, objects_model, application_with_mocked_scene, group_scene_node):
        objects_model._shouldNodeBeHandled = MagicMock(return_value=True)
        group_scene_node.setName("Group")
        group_scene_node.isOutsideBuildArea = MagicMock(return_value = True)
        application_with_mocked_scene.getController().getScene().getRoot = MagicMock(return_value=group_scene_node)
        with patch("UM.Application.Application.getInstance", MagicMock(return_value=application_with_mocked_scene)):
            objects_model._update()
            assert objects_model.items == [{
                'name': 'Group #1',
                'selected': False,
                'outside_build_area': True,
                'buildplate_number': None,
                'node': group_scene_node,
                "extruder_number": -1,
                "per_object_settings_count": 0,
                "mesh_type": ""
            }]

