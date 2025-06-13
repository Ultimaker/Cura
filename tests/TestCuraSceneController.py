from unittest.mock import MagicMock, patch

import pytest

from UM.Scene.SceneNode import SceneNode
from cura.Machines.Models.MultiBuildPlateModel import MultiBuildPlateModel
from cura.Scene.CuraSceneController import CuraSceneController
from cura.UI.ObjectsModel import ObjectsModel


@pytest.fixture
def objects_model() -> ObjectsModel:
    return MagicMock(spec=ObjectsModel)

@pytest.fixture
def multi_build_plate_model() -> MultiBuildPlateModel:
    return MagicMock(spec=MultiBuildPlateModel)

@pytest.fixture
def mocked_application():
    mocked_application = MagicMock()
    mocked_controller = MagicMock()
    mocked_scene = MagicMock()
    mocked_application.getController = MagicMock(return_value=mocked_controller)
    mocked_controller.getScene = MagicMock(return_value=mocked_scene)
    return mocked_application


def test_setActiveBuildPlate(objects_model, multi_build_plate_model):
    with patch("UM.Application.Application.getInstance"):
        controller = CuraSceneController(objects_model, multi_build_plate_model)
    controller.setActiveBuildPlate(12)
    multi_build_plate_model.setActiveBuildPlate.assert_called_once_with(12)
    objects_model.setActiveBuildPlate.assert_called_once_with(12)

    # Doing it again shouldn't cause another change to be passed along
    controller.setActiveBuildPlate(12)
    multi_build_plate_model.setActiveBuildPlate.assert_called_once_with(12)
    objects_model.setActiveBuildPlate.assert_called_once_with(12)


def test_calcMaxBuildPlateEmptyScene(objects_model, multi_build_plate_model, mocked_application):
    mocked_root = MagicMock()
    mocked_root.callDecoration = MagicMock(return_value=0)
    mocked_application.getController().getScene().getRoot = MagicMock(return_value=mocked_root)
    with patch("UM.Application.Application.getInstance", MagicMock(return_value=mocked_application)):
        controller = CuraSceneController(objects_model, multi_build_plate_model)
        assert controller._calcMaxBuildPlate() == 0


def test_calcMaxBuildPlateFilledScene(objects_model, multi_build_plate_model, mocked_application):
    mocked_root = MagicMock()
    mocked_root.callDecoration = MagicMock(return_value = 0)
    mocked_child = MagicMock()
    mocked_child.callDecoration = MagicMock(return_value = 2)
    mocked_root.getAllChildren = MagicMock(return_value = [mocked_child])
    mocked_application.getController().getScene().getRoot = MagicMock(return_value=mocked_root)
    with patch("UM.Application.Application.getInstance", MagicMock(return_value=mocked_application)):
        controller = CuraSceneController(objects_model, multi_build_plate_model)
        assert controller._calcMaxBuildPlate() == 2


def test_updateMaxBuildPlate(objects_model, multi_build_plate_model):
    with patch("UM.Application.Application.getInstance"):
        controller = CuraSceneController(objects_model, multi_build_plate_model)
        controller._calcMaxBuildPlate = MagicMock(return_value = 12)
        controller.updateMaxBuildPlate(SceneNode())

        # Check if that went well.
        multi_build_plate_model.setMaxBuildPlate.assert_called_once_with(12)

        # Move to a different active build plate
        controller.setActiveBuildPlate(5)

        # And check what happens if we move down again!
        controller._calcMaxBuildPlate = MagicMock(return_value=2)
        controller.updateMaxBuildPlate(SceneNode())
        assert controller._active_build_plate == 0 # We don't have any items anywhere, so default to 0

