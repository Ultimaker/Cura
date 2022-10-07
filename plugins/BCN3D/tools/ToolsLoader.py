
from UM.Tool import Tool
from UM.Logger import Logger

from .print_modes import PrintModesPlugin

class ToolsLoader(Tool):

    def __init__(self):
        super().__init__()
        self.print_modes = PrintModesPlugin.PrintModesPlugin()
