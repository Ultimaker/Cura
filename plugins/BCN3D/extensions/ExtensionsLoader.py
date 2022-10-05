
from UM.Extension import Extension
from UM.Logger import Logger

from .idex import IdexPlugin
from .api import ApiPlugin

class ExtensionsLoader(Extension):

    def __init__(self):
        super().__init__()
        Logger.info(f"Init Extensions Loader:")
        self.idex = IdexPlugin.IdexPlugin()
        self.api = ApiPlugin.ApiPlugin()