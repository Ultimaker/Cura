import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock UM.Logger before importing MCPServer
mock_um = MagicMock()
sys.modules["UM"] = mock_um
sys.modules["UM.Logger"] = mock_um

# Add the plugin directory to sys.path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from MCPServer import MCPServer


class TestMCPServer(unittest.TestCase):
    def setUp(self):
        self.dispatcher_mock = MagicMock()
        self.server = MCPServer(self.dispatcher_mock)

    @patch("MCPServer.FastMCP")
    @patch("MCPServer.Logger")
    def test_run_initializes_server(self, mock_logger, mock_fastmcp):
        # Setup mock
        mock_server_instance = MagicMock()
        mock_fastmcp.return_value = mock_server_instance

        # Run the server logic (we call run directly to avoid threading issues in test)
        self.server.run()

        # Verify FastMCP was initialized
        mock_fastmcp.assert_called_with("CuraMCP")

        # Verify tools were registered
        self.assertTrue(mock_server_instance.tool.called)

        # Verify server started
        mock_server_instance.run.assert_called_with(transport="stdio")

    @patch("MCPServer.FastMCP")
    @patch("MCPServer.Logger")
    def test_ping_tool(self, mock_logger, mock_fastmcp):
        mock_server_instance = MagicMock()
        mock_fastmcp.return_value = mock_server_instance

        # Capture the tool decorator
        tool_decorator = MagicMock()
        mock_server_instance.tool.return_value = tool_decorator

        self.server.run()

        # Find the ping function registered
        # The decorator is called with the function as argument
        # We need to find which call was for 'ping'
        # This is tricky with mocks, so we might need to inspect the calls to tool_decorator

        # Alternative: We can inspect the local functions defined in run() if we could access them,
        # but they are local.
        # However, we can verify that the tool decorator was called.
        # ping, log_to_cura, get_ui_tree, click_element, set_value, invoke_action = 6 tools
        self.assertEqual(tool_decorator.call_count, 6)

    @patch("MCPServer.FastMCP")
    @patch("MCPServer.Logger")
    def test_action_tools(self, mock_logger, mock_fastmcp):
        mock_server_instance = MagicMock()
        mock_fastmcp.return_value = mock_server_instance

        captured_functions = {}

        def side_effect(func=None):
            # Handle @tool() vs @tool
            if func:
                captured_functions[func.__name__] = func
                return func
            else:

                def wrapper(f):
                    captured_functions[f.__name__] = f
                    return f

                return wrapper

        mock_server_instance.tool.side_effect = side_effect

        self.server.run()

        # Test click_element
        if "click_element" in captured_functions:
            click_func = captured_functions["click_element"]
            result = click_func("test_btn")
            self.dispatcher_mock.dispatch.assert_any_call("click", {"id": "test_btn"})
            self.assertEqual(result, "Clicked element test_btn")
        else:
            self.fail("click_element function not registered")

        # Test set_value
        if "set_value" in captured_functions:
            set_value_func = captured_functions["set_value"]
            result = set_value_func("test_input", "hello")
            self.dispatcher_mock.dispatch.assert_any_call(
                "set_value", {"id": "test_input", "value": "hello"}
            )
            self.assertEqual(result, "Set value for test_input")
        else:
            self.fail("set_value function not registered")

        # Test invoke_action
        if "invoke_action" in captured_functions:
            invoke_func = captured_functions["invoke_action"]
            result = invoke_func("test_obj", "trigger")
            self.dispatcher_mock.dispatch.assert_any_call(
                "invoke_action", {"id": "test_obj", "action": "trigger"}
            )
            self.assertEqual(result, "Invoked action trigger on test_obj")
        else:
            self.fail("invoke_action function not registered")


if __name__ == "__main__":
    unittest.main()
