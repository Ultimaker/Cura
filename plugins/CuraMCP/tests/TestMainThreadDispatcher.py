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

# Add the plugin directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Now import the module under test
from MainThreadDispatcher import MainThreadDispatcher


class TestMainThreadDispatcher(unittest.TestCase):
    def setUp(self):
        # Reset the signal for each test
        MainThreadDispatcher.perform_action_signal = MockSignal(str, dict, object)
        self.dispatcher = MainThreadDispatcher()
        self.dispatcher._crawler = MagicMock()

    def test_dispatch_success(self):
        # We need to mock the emit behavior to simulate the slot execution
        # Since dispatch calls emit and waits, we need to ensure the slot is called or simulated

        # However, dispatch uses threading.Event.wait(), which will block if we don't set the event.
        # In a real scenario, the slot runs on the main thread.
        # Here, we can mock the emit method on the instance's signal to execute the logic immediately.

        original_emit = self.dispatcher.perform_action_signal.emit

        def side_effect(action, args, context):
            event, result_container = context
            result_container["result"] = "success"
            event.set()

        self.dispatcher.perform_action_signal.emit = side_effect

        result = self.dispatcher.dispatch("test_action", {"key": "value"})
        self.assertEqual(result, "success")

    def test_dispatch_error(self):
        def side_effect(action, args, context):
            event, result_container = context
            result_container["error"] = ValueError("Test error")
            event.set()

        self.dispatcher.perform_action_signal.emit = side_effect

        with self.assertRaises(ValueError):
            self.dispatcher.dispatch("test_action")

    @patch("MainThreadDispatcher.Logger")
    def test_perform_action_log(self, mock_logger):
        event = MagicMock()
        result_container = {"result": None, "error": None}
        context = (event, result_container)

        # Call the slot directly
        self.dispatcher._perform_action("log", {"msg": "test message"}, context)

        # Verify logger was called
        # Note: The actual implementation calls Logger.log("i", ...)
        # We need to check if Logger.log was called with correct arguments
        mock_logger.log.assert_called()
        args, _ = mock_logger.log.call_args
        self.assertEqual(args[0], "i")
        self.assertIn("test message", args[1])

        self.assertTrue(result_container["result"])
        self.assertIsNone(result_container["error"])
        event.set.assert_called()

    @patch("MainThreadDispatcher.Logger")
    def test_perform_action_unknown(self, mock_logger):
        event = MagicMock()
        result_container = {"result": None, "error": None}
        context = (event, result_container)

        self.dispatcher._perform_action("unknown", {}, context)

        mock_logger.log.assert_called()
        args, _ = mock_logger.log.call_args
        self.assertEqual(args[0], "w")
        self.assertIn("Unknown action", args[1])

        self.assertIsInstance(result_container["error"], ValueError)
        event.set.assert_called()

    def test_perform_action_click(self):
        event = MagicMock()
        result_container = {"result": None, "error": None}
        context = (event, result_container)

        mock_element = MagicMock()
        self.dispatcher._crawler.find_element.return_value = mock_element

        # We need to mock QTest or whatever mechanism is used for clicking
        # Since we are testing _perform_action, we expect it to call find_element
        # and then perform the click.

        # For now, let's assume it uses QTest.mouseClick if available, or some fallback.
        # We can patch QTest in the module scope if needed, but for now let's just check find_element.

        with patch("MainThreadDispatcher.QTest") as mock_qtest:
            self.dispatcher._perform_action("click", {"id": "test_btn"}, context)

            self.dispatcher._crawler.find_element.assert_called_with("test_btn")
            mock_qtest.mouseClick.assert_called_with(
                mock_element, mock_pyqt_core.Qt.MouseButton.LeftButton
            )

            self.assertTrue(result_container["result"])
            event.set.assert_called()

    def test_perform_action_set_value(self):
        event = MagicMock()
        result_container = {"result": None, "error": None}
        context = (event, result_container)

        mock_element = MagicMock()
        self.dispatcher._crawler.find_element.return_value = mock_element

        self.dispatcher._perform_action(
            "set_value", {"id": "test_input", "value": "hello"}, context
        )

        self.dispatcher._crawler.find_element.assert_called_with("test_input")
        mock_element.setProperty.assert_called_with(
            "text", "hello"
        )  # Assuming default property is text for now, or we pass property name

        self.assertTrue(result_container["result"])
        event.set.assert_called()

    def test_perform_action_invoke_action(self):
        event = MagicMock()
        result_container = {"result": None, "error": None}
        context = (event, result_container)

        mock_element = MagicMock()
        self.dispatcher._crawler.find_element.return_value = mock_element

        with patch("MainThreadDispatcher.QMetaObject") as mock_meta:
            self.dispatcher._perform_action(
                "invoke_action", {"id": "test_obj", "action": "trigger"}, context
            )

            self.dispatcher._crawler.find_element.assert_called_with("test_obj")
            mock_meta.invokeMethod.assert_called_with(mock_element, "trigger")

            self.assertTrue(result_container["result"])
            event.set.assert_called()


if __name__ == "__main__":
    unittest.main()
