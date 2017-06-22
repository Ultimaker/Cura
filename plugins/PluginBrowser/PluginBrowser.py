# Copyright (c) 2017 Ultimaker B.V.
# PluginBrowser is released under the terms of the AGPLv3 or higher.


from UM.Extension import Extension
from UM.i18n import i18nCatalog


i18n_catalog = i18nCatalog("cura")


class PluginBrowser(Extension):
    def __init__(self):
        super().__init__()
        self.addMenuItem(i18n_catalog.i18n("Browse plugins"), self.browsePlugins)

    def browsePlugins(self):
        pass