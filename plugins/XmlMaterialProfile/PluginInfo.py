# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.PluginObject import PluginObject


class PluginInfo(PluginObject):
    __instance = None # type: PluginInfo

    def __init__(self, *args, **kwags):
        if PluginInfo.__instance is not None:
            raise RuntimeError("Try to create singleton '%s' more than once" % self.__class__.__name__)
        super().__init__(*args, **kwags)
        PluginInfo.__instance = self

    @classmethod
    def getInstance(cls, *args, **kwargs) -> "PluginInfo":
        return cls.__instance
