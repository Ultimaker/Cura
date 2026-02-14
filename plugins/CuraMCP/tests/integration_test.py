import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import threading

# --- Mocking Dependencies ---

# Mock PyQt6
mock_pyqt_core = MagicMock()
mock_pyqt_test = MagicMock()
mock_pyqt_widgets = MagicMock()
mock_pyqt_quick = MagicMock()

sys.modules["PyQt6"] = MagicMock()
sys.modules["PyQt6.QtCore"] = mock_pyqt_core
sys.modules["PyQt6.QtTest"] = mock_pyqt_test
sys.modules["PyQt6.QtWidgets"] = mock_pyqt_widgets
sys.modules["PyQt6.QtQuick"] = mock_pyqt_quick


# Mock QObject and Signals
class MockQObject:
    def __init__(self, *args, **kwargs):
        pass


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
mock_pyqt_core.Qt.MouseButton.LeftButton = 1

# Mock UM
mock_um = MagicMock()
sys.modules["UM"] = mock_um
sys.modules["UM.Logger"] = mock_um


# Mock UM.Math.Vector
class MockVector:
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

    def __eq__(self, other):
        if isinstance(other, MockVector):
            return self.x == other.x and self.y == other.y and self.z == other.z
        return False

    def __repr__(self):
        return f"Vector({self.x}, {self.y}, {self.z})"

    def __add__(self, other):
        return MockVector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return MockVector(self.x * other, self.y * other, self.z * other)
        return NotImplemented

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return MockVector(self.x / other, self.y / other, self.z / other)
        return NotImplemented


sys.modules["UM.Math.Vector"] = MagicMock()
sys.modules["UM.Math.Vector"].Vector = MockVector


# Mock UM.Scene.Selection
class MockSelection:
    _selected_objects = []

    @classmethod
    def getAllSelectedObjects(cls):
        return cls._selected_objects

    @classmethod
    def clear(cls):
        cls._selected_objects = []

    @classmethod
    def add(cls, obj):
        if obj not in cls._selected_objects:
            cls._selected_objects.append(obj)


sys.modules["UM.Scene.Selection"] = MagicMock()
sys.modules["UM.Scene.Selection"].Selection = MockSelection


# Mock UM.Scene.Iterator.DepthFirstIterator
class MockDepthFirstIterator:
    def __init__(self, root):
        self.root = root
        self.nodes = [root]  # Simplified traversal
        # Add children if root has them
        if hasattr(root, "getChildren"):
            self.nodes.extend(root.getChildren())

    def __iter__(self):
        return iter(self.nodes)


sys.modules["UM.Scene.Iterator.DepthFirstIterator"] = MagicMock()
sys.modules[
    "UM.Scene.Iterator.DepthFirstIterator"
].DepthFirstIterator = MockDepthFirstIterator

# Mock cura.CuraApplication
mock_cura = MagicMock()
sys.modules["cura"] = mock_cura
sys.modules["cura.CuraApplication"] = mock_cura

# Mock mcp.server.fastmcp
mock_mcp = MagicMock()
sys.modules["mcp"] = mock_mcp
sys.modules["mcp.server"] = mock_mcp
sys.modules["mcp.server.fastmcp"] = mock_mcp

# Add plugin directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from MCPServer import MCPServer
from MainThreadDispatcher import MainThreadDispatcher


class TestIntegration(unittest.TestCase):
    def setUp(self):
        # Reset mocks
        MockSelection.clear()

        # Setup Cura Application Mock
        self.mock_app = MagicMock()
        mock_cura.CuraApplication.getInstance.return_value = self.mock_app

        # Setup Controller, Scene, Camera
        self.mock_controller = MagicMock()
        self.mock_scene = MagicMock()
        self.mock_camera = MagicMock()
        self.mock_build_volume = MagicMock()

        self.mock_app.getController.return_value = self.mock_controller
        self.mock_controller.getScene.return_value = self.mock_scene
        self.mock_scene.getActiveCamera.return_value = self.mock_camera
        self.mock_app.getBuildVolume.return_value = self.mock_build_volume

        # Setup Build Volume
        self.mock_build_volume.getDiagonalSize.return_value = 375.0
        mock_bbox = MagicMock()
        mock_bbox.center = MockVector(0, 0, 0)
        mock_bbox.size = MockVector(200, 200, 200)
        self.mock_build_volume.getBoundingBox.return_value = mock_bbox

        # Setup Scene Nodes for Selection Test
        self.mock_root = MagicMock()
        self.mock_scene.getRoot.return_value = self.mock_root

        self.node1 = MagicMock()
        self.node1.getId.return_value = "node1"
        self.node1.getName.return_value = "Node 1"

        self.node2 = MagicMock()
        self.node2.getId.return_value = "node2"
        self.node2.getName.return_value = "Node 2"

        self.mock_root.getChildren.return_value = [self.node1, self.node2]

        # Setup Dispatcher
        # We need to ensure the signal emits immediately in the same thread for testing
        MainThreadDispatcher.perform_action_signal = MockSignal(str, dict, object)
        self.dispatcher = MainThreadDispatcher()

        # Mock QMLCrawler inside Dispatcher
        self.dispatcher._crawler = MagicMock()
        self.mock_ui_element = MagicMock()
        self.dispatcher._crawler.find_element.return_value = self.mock_ui_element
        self.dispatcher._crawler.get_ui_tree.return_value = {"root": {"children": []}}

        # Setup MCPServer
        self.server = MCPServer(self.dispatcher)

        # Capture registered tools
        self.registered_tools = {}

        # Mock FastMCP instance and tool decorator
        self.mock_fastmcp_instance = MagicMock()
        mock_mcp.FastMCP.return_value = self.mock_fastmcp_instance

        def tool_decorator(func=None):
            if func:
                self.registered_tools[func.__name__] = func
                return func
            else:

                def wrapper(f):
                    self.registered_tools[f.__name__] = f
                    return f

                return wrapper

        self.mock_fastmcp_instance.tool.side_effect = tool_decorator

        # Initialize server (registers tools)
        self.server.run()

    def test_get_ui_tree(self):
        """Test get_ui_tree tool"""
        tool = self.registered_tools.get("get_ui_tree")
        self.assertIsNotNone(tool)

        result = tool()
        import json

        expected = json.dumps({"root": {"children": []}}, indent=2)
        self.assertEqual(result, expected)
        self.dispatcher._crawler.get_ui_tree.assert_called_once()

    def test_click_element(self):
        """Test click_element tool"""
        tool = self.registered_tools.get("click_element")
        self.assertIsNotNone(tool)

        # Mock QTest
        with patch("MainThreadDispatcher.QTest") as mock_qtest:
            result = tool("test_btn")

            self.assertEqual(result, "Clicked element test_btn")
            self.dispatcher._crawler.find_element.assert_called_with("test_btn")
            mock_qtest.mouseClick.assert_called()

    def test_camera_home(self):
        """Test camera_home tool"""
        tool = self.registered_tools.get("camera_home")
        self.assertIsNotNone(tool)

        result = tool()

        self.assertEqual(result, "Camera homed")
        self.mock_camera.setPosition.assert_called()
        self.mock_camera.setPerspective.assert_called_with(True)
        self.mock_camera.lookAt.assert_called_with(MockVector(0, 0, 0))

    def test_selection_set(self):
        """Test selection_set tool"""
        tool = self.registered_tools.get("selection_set")
        self.assertIsNotNone(tool)

        # Test selecting node1
        result = tool(["node1"])

        self.assertEqual(result, "Selection set to ['node1']")
        self.assertIn(self.node1, MockSelection.getAllSelectedObjects())
        self.assertNotIn(self.node2, MockSelection.getAllSelectedObjects())

        # Test selecting node2
        result = tool(["node2"])
        self.assertEqual(result, "Selection set to ['node2']")
        self.assertIn(self.node2, MockSelection.getAllSelectedObjects())
        # Selection.clear() is called inside selection_set, so node1 should be gone
        # But wait, MockSelection.clear() clears the list.
        # Let's verify the logic in MainThreadDispatcher:
        # Selection.clear()
        # for node_id in node_ids: Selection.add(node)

        self.assertNotIn(self.node1, MockSelection.getAllSelectedObjects())

    def test_camera_set_view(self):
        """Test camera_set_view tool"""
        tool = self.registered_tools.get("camera_set_view")
        self.assertIsNotNone(tool)

        result = tool("top")
        self.assertEqual(result, "Camera set to top view")
        self.mock_camera.setPosition.assert_called()
        self.mock_camera.lookAt.assert_called()


if __name__ == "__main__":
    unittest.main()
