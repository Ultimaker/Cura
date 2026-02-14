import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock PyQt6 before importing MainThreadDispatcher
mock_pyqt_core = MagicMock()
mock_pyqt_test = MagicMock()
mock_pyqt_widgets = MagicMock()
mock_pyqt_quick = MagicMock()

sys.modules["PyQt6"] = MagicMock()
sys.modules["PyQt6.QtCore"] = mock_pyqt_core
sys.modules["PyQt6.QtTest"] = mock_pyqt_test
sys.modules["PyQt6.QtWidgets"] = mock_pyqt_widgets
sys.modules["PyQt6.QtQuick"] = mock_pyqt_quick


# Mock QObject
class MockQObject:
    def __init__(self, *args, **kwargs):
        pass


# Mock pyqtSignal
class MockSignal:
    def __init__(self, *args):
        self.args = args
        self._slots = []

    def connect(self, slot):
        self._slots.append(slot)

    def emit(self, *args):
        for slot in self._slots:
            slot(*args)


mock_pyqt_core.QObject = MockQObject
mock_pyqt_core.pyqtSignal = MockSignal
mock_pyqt_core.pyqtSlot = lambda *args: lambda func: func

# Mock UM.Logger
mock_um = MagicMock()
sys.modules["UM"] = mock_um
sys.modules["UM.Logger"] = mock_um


# Mock UM.Math.Vector
class MockVector:
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other):
        return MockVector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __mul__(self, other):
        return MockVector(self.x * other, self.y * other, self.z * other)

    def __truediv__(self, other):
        return MockVector(self.x / other, self.y / other, self.z / other)


sys.modules["UM.Math.Vector"] = MagicMock()
sys.modules["UM.Math.Vector"].Vector = MockVector

# Mock UM.Scene.Selection
mock_selection = MagicMock()
sys.modules["UM.Scene.Selection"] = mock_selection
sys.modules["UM.Scene.Selection"].Selection = mock_selection


# Mock UM.Scene.Iterator.DepthFirstIterator
def mock_depth_first_iterator(root):
    return []


sys.modules["UM.Scene.Iterator.DepthFirstIterator"] = MagicMock()
sys.modules[
    "UM.Scene.Iterator.DepthFirstIterator"
].DepthFirstIterator = mock_depth_first_iterator

# Mock cura.CuraApplication
mock_cura = MagicMock()
sys.modules["cura"] = mock_cura
sys.modules["cura.CuraApplication"] = mock_cura

# Add the plugin directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from MainThreadDispatcher import MainThreadDispatcher


class TestViewportBindings(unittest.TestCase):
    def setUp(self):
        MainThreadDispatcher.perform_action_signal = MockSignal(str, dict, object)
        self.dispatcher = MainThreadDispatcher()
        self.dispatcher._crawler = MagicMock()

        # Setup CuraApplication mock
        self.mock_app = MagicMock()
        mock_cura.CuraApplication.getInstance.return_value = self.mock_app

        self.mock_controller = MagicMock()
        self.mock_app.getController.return_value = self.mock_controller

        self.mock_scene = MagicMock()
        self.mock_controller.getScene.return_value = self.mock_scene

        self.mock_camera = MagicMock()
        self.mock_scene.getActiveCamera.return_value = self.mock_camera

        self.mock_build_volume = MagicMock()
        self.mock_app.getBuildVolume.return_value = self.mock_build_volume
        self.mock_build_volume.getDiagonalSize.return_value = 375.0

        # Mock BoundingBox for set_view
        mock_bbox = MagicMock()
        mock_bbox.center = MockVector(0, 0, 0)
        mock_bbox.size = MockVector(200, 200, 200)
        self.mock_build_volume.getBoundingBox.return_value = mock_bbox

    def test_camera_home(self):
        event = MagicMock()
        result_container = {"result": None, "error": None}
        context = (event, result_container)

        self.dispatcher._perform_action("camera_home", {}, context)

        self.mock_camera.setPosition.assert_called()
        self.mock_camera.setPerspective.assert_called_with(True)
        self.mock_camera.lookAt.assert_called()
        self.assertTrue(result_container["result"])

    def test_camera_set_view_top(self):
        event = MagicMock()
        result_container = {"result": None, "error": None}
        context = (event, result_container)

        self.dispatcher._perform_action("camera_set_view", {"view": "top"}, context)

        self.mock_camera.setPosition.assert_called()
        self.mock_camera.lookAt.assert_called()
        self.assertTrue(result_container["result"])

    def test_camera_look_at(self):
        event = MagicMock()
        result_container = {"result": None, "error": None}
        context = (event, result_container)

        self.dispatcher._perform_action(
            "camera_look_at", {"x": 10, "y": 20, "z": 30}, context
        )

        self.mock_camera.lookAt.assert_called()
        # Verify arguments if possible, but MockVector makes it tricky to check exact values without more setup
        self.assertTrue(result_container["result"])

    def test_tool_set_active(self):
        event = MagicMock()
        result_container = {"result": None, "error": None}
        context = (event, result_container)

        self.dispatcher._perform_action(
            "tool_set_active", {"tool_id": "TranslateTool"}, context
        )

        self.mock_controller.setActiveTool.assert_called_with("TranslateTool")
        self.assertTrue(result_container["result"])

    def test_tool_get_active(self):
        event = MagicMock()
        result_container = {"result": None, "error": None}
        context = (event, result_container)

        mock_tool = MagicMock()
        mock_tool.getPluginId.return_value = "RotateTool"
        self.mock_controller.getActiveTool.return_value = mock_tool

        self.dispatcher._perform_action("tool_get_active", {}, context)

        self.assertEqual(result_container["result"], "RotateTool")

    def test_selection_get(self):
        event = MagicMock()
        result_container = {"result": None, "error": None}
        context = (event, result_container)

        mock_node = MagicMock()
        mock_node.getId.return_value = "node_1"
        mock_node.getName.return_value = "Cube"
        mock_selection.getAllSelectedObjects.return_value = [mock_node]

        self.dispatcher._perform_action("selection_get", {}, context)

        self.assertEqual(len(result_container["result"]), 1)
        self.assertEqual(result_container["result"][0]["id"], "node_1")
        self.assertEqual(result_container["result"][0]["name"], "Cube")

    def test_selection_clear(self):
        event = MagicMock()
        result_container = {"result": None, "error": None}
        context = (event, result_container)

        self.dispatcher._perform_action("selection_clear", {}, context)

        mock_selection.clear.assert_called()
        self.assertTrue(result_container["result"])

    def test_selection_set(self):
        event = MagicMock()
        result_container = {"result": None, "error": None}
        context = (event, result_container)

        # Mock finding node
        mock_node = MagicMock()
        mock_node.getId.return_value = "node_1"

        # Patch _find_node_by_id since we mocked DepthFirstIterator to return empty
        with patch.object(
            self.dispatcher, "_find_node_by_id", return_value=mock_node
        ) as mock_find:
            self.dispatcher._perform_action(
                "selection_set", {"node_ids": ["node_1"]}, context
            )

            mock_selection.clear.assert_called()
            mock_find.assert_called_with("node_1")
            mock_selection.add.assert_called_with(mock_node)
            self.assertTrue(result_container["result"])


if __name__ == "__main__":
    unittest.main()
