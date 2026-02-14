import threading
import asyncio
import sys
from typing import Optional, Any
from UM.Logger import Logger

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    Logger.log("w", "Failed to import mcp.server.fastmcp. MCP Server will not start.")
    FastMCP = None


class MCPServer(threading.Thread):
    """
    A thread that runs the Model Context Protocol (MCP) server.
    It exposes tools that can be called by an MCP client (e.g., an LLM).
    """

    def __init__(self, dispatcher: Any) -> None:
        """
        Initialize the MCP Server thread.

        :param dispatcher: The MainThreadDispatcher to execute actions on the main thread.
        """
        super().__init__()
        self._dispatcher = dispatcher
        self.daemon = True
        self._server: Optional[Any] = None

    def run(self) -> None:
        """
        Run the MCP server. This method is executed in a separate thread.
        """
        if FastMCP is None:
            return

        Logger.log("i", "Initializing MCP Server...")

        try:
            # Create the FastMCP server
            self._server = FastMCP("CuraMCP")

            # Register tools
            self._register_tools()

            Logger.log("i", "Starting MCP Server on stdio...")

            # Run the server using stdio transport
            # FastMCP.run() is a blocking call that runs the asyncio event loop
            self._server.run(transport="stdio")
        except Exception as e:
            Logger.log("e", f"MCP Server encountered an error: {e}")

    def _register_tools(self) -> None:
        """
        Register the tools available to the MCP client.
        """
        if self._server is None:
            return

        @self._server.tool()
        def ping() -> str:
            """Ping the server to check connectivity."""
            return "pong"

        @self._server.tool()
        def log_to_cura(message: str) -> str:
            """Log a message to the Cura application log."""
            try:
                self._dispatcher.dispatch("log", {"msg": message})
                return "Message logged to Cura"
            except Exception as e:
                return f"Error logging to Cura: {str(e)}"

        @self._server.tool()
        def get_ui_tree() -> str:
            """
            Get the current UI tree of the application.
            Returns a JSON string representation of the QML object hierarchy.
            """
            try:
                tree = self._dispatcher.dispatch("get_ui_tree")
                import json

                return json.dumps(tree, indent=2)
            except Exception as e:
                return f"Error getting UI tree: {str(e)}"

        @self._server.tool()
        def click_element(element_id: str) -> str:
            """
            Click a UI element by its ID.
            """
            try:
                self._dispatcher.dispatch("click", {"id": element_id})
                return f"Clicked element {element_id}"
            except Exception as e:
                return f"Error clicking element {element_id}: {str(e)}"

        @self._server.tool()
        def set_value(element_id: str, value: Any) -> str:
            """
            Set a value for a UI element property (e.g., text input).
            """
            try:
                self._dispatcher.dispatch(
                    "set_value", {"id": element_id, "value": value}
                )
                return f"Set value for {element_id}"
            except Exception as e:
                return f"Error setting value for {element_id}: {str(e)}"

        @self._server.tool()
        def invoke_action(element_id: str, action_name: str) -> str:
            """
            Invoke a specific action/method on a UI element.
            """
            try:
                self._dispatcher.dispatch(
                    "invoke_action", {"id": element_id, "action": action_name}
                )
                return f"Invoked action {action_name} on {element_id}"
            except Exception as e:
                return f"Error invoking action {action_name} on {element_id}: {str(e)}"

        @self._server.tool()
        def camera_home() -> str:
            """Reset camera position and direction to default."""
            try:
                self._dispatcher.dispatch("camera_home")
                return "Camera homed"
            except Exception as e:
                return f"Error homing camera: {str(e)}"

        @self._server.tool()
        def camera_set_view(view: str) -> str:
            """
            Set camera to a standard view.
            :param view: One of "top", "bottom", "front", "back", "left", "right", "iso".
            """
            try:
                self._dispatcher.dispatch("camera_set_view", {"view": view})
                return f"Camera set to {view} view"
            except Exception as e:
                return f"Error setting camera view: {str(e)}"

        @self._server.tool()
        def camera_look_at(x: float, y: float, z: float) -> str:
            """
            Point the camera at a specific coordinate.
            """
            try:
                self._dispatcher.dispatch("camera_look_at", {"x": x, "y": y, "z": z})
                return f"Camera looking at ({x}, {y}, {z})"
            except Exception as e:
                return f"Error setting camera look at: {str(e)}"

        @self._server.tool()
        def tool_set_active(tool_id: str) -> str:
            """
            Activate a specific tool (e.g., "TranslateTool", "RotateTool", "ScaleTool").
            """
            try:
                self._dispatcher.dispatch("tool_set_active", {"tool_id": tool_id})
                return f"Active tool set to {tool_id}"
            except Exception as e:
                return f"Error setting active tool: {str(e)}"

        @self._server.tool()
        def tool_get_active() -> str:
            """
            Get the ID of the currently active tool.
            """
            try:
                tool_id = self._dispatcher.dispatch("tool_get_active")
                return f"Active tool: {tool_id}"
            except Exception as e:
                return f"Error getting active tool: {str(e)}"

        @self._server.tool()
        def selection_get() -> str:
            """
            Get a list of selected objects (IDs and names).
            """
            try:
                selection = self._dispatcher.dispatch("selection_get")
                import json

                return json.dumps(selection, indent=2)
            except Exception as e:
                return f"Error getting selection: {str(e)}"

        @self._server.tool()
        def selection_clear() -> str:
            """
            Clear the current selection.
            """
            try:
                self._dispatcher.dispatch("selection_clear")
                return "Selection cleared"
            except Exception as e:
                return f"Error clearing selection: {str(e)}"

        @self._server.tool()
        def selection_set(node_ids: list[str]) -> str:
            """
            Set the selection to a specific list of object IDs.
            """
            try:
                self._dispatcher.dispatch("selection_set", {"node_ids": node_ids})
                return f"Selection set to {node_ids}"
            except Exception as e:
                return f"Error setting selection: {str(e)}"
