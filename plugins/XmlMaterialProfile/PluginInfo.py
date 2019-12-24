from UM.PluginObject import PluginObject


class PluginInfo(PluginObject):
    __instance = None # type: PluginInfo

    def __init__(self, *args, **kwags):
        super().__init__(*args, **kwags)
        if PluginInfo.__instance is not None:
            raise RuntimeError("Try to create singleton '%s' more than once" % self.__class__.__name__)
        PluginInfo.__instance = self

    @classmethod
    def getInstance(cls, *args, **kwargs) -> "USBPrinterOutputDeviceManager":
        return cls.__instance