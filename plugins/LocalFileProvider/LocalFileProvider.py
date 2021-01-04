# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os.path

from UM.FileProvider import FileProvider  # The plug-in type we're going to implement.
from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.PluginRegistry import PluginRegistry  # To get resources from the plug-in folder.
from cura.CuraApplication import CuraApplication  # To create QML elements.

i18n_catalog = i18nCatalog("cura")


class LocalFileProvider(FileProvider):
    """
    Allows the user to open files from their local file system.

    These files will then be interpreted through the file handlers.
    """

    def __init__(self):
        super().__init__()
        self.menu_item_display_text = i18n_catalog.i18nc("@menu Open files from local disk", "Local disk")
        self.shortcut = "Ctrl+O"

        self._dialog = None  # Lazy-load this QML element.

    def _load_file_dialog(self):
        """
        Loads the file dialog QML element into the QML context so that it can be shown.
        :return:
        """
        plugin_path = PluginRegistry.getInstance().getPluginPath(self.getPluginId())
        if plugin_path is None:
            plugin_path = os.path.dirname(__file__)
        path = os.path.join(plugin_path, "OpenLocalFile.qml")
        self._dialog = CuraApplication.getInstance().createQmlComponent(path)
        if self._dialog is None:
            Logger.log("e", "Unable to create open file dialogue.")

    def run(self):
        if self._dialog is None:
            self._load_file_dialog()
            if self._dialog is None:
                return  # Will already have logged an error in _load_file_dialog.
        self._dialog.show()