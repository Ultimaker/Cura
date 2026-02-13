import threading
import asyncio
import sys
from UM.Logger import Logger

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    Logger.log("w", "Failed to import mcp.server.fastmcp. MCP Server will not start.")
    FastMCP = None


class MCPServer(threading.Thread):
    def __init__(self, dispatcher):
        super().__init__()
        self._dispatcher = dispatcher
        self.daemon = True
        self._server = None

    def run(self):
        if FastMCP is None:
            return

        Logger.log("i", "Initializing MCP Server...")

        # Create the FastMCP server
        self._server = FastMCP("CuraMCP")

        # Register tools
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

        Logger.log("i", "Starting MCP Server on stdio...")

        try:
            # Run the server using stdio transport
            # FastMCP.run() is a blocking call that runs the asyncio event loop
            self._server.run(transport="stdio")
        except Exception as e:
            Logger.log("e", f"MCP Server encountered an error: {e}")
