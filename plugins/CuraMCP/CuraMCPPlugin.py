from UM.Extension import Extension
from UM.Logger import Logger
from .MainThreadDispatcher import MainThreadDispatcher
from .MCPServer import MCPServer


class CuraMCPPlugin(Extension):
    def __init__(self):
        super().__init__()
        Logger.log("i", "CuraMCP Plugin initialized")
        self._server_thread = None
        self._dispatcher = MainThreadDispatcher()
        self._start_server()

    def _start_server(self):
        Logger.log("i", "Starting MCP Server...")
        self._server_thread = MCPServer(self._dispatcher)
        self._server_thread.start()
