# Copyright (c) 2017 Ultimaker B.V.
# PluginBrowser is released under the terms of the AGPLv3 or higher.
from UM.Extension import Extension
from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.PluginRegistry import PluginRegistry
from UM.Application import Application

from PyQt5.QtCore import QUrl, QObject, pyqtSignal
from PyQt5.QtQml import QQmlComponent, QQmlContext

import os

i18n_catalog = i18nCatalog("cura")


class ConfigDialog(QObject, Extension):
    def __init__(self, parent = None):
        super().__init__(parent)
        self._dialog = None
        self.addMenuItem(i18n_catalog.i18n("Configure"), self._openConfigDialog)

    def _openConfigDialog(self):
        if not self._dialog:
            self._createDialog()
        self._dialog.show()

    def _createDialog(self):
        path = QUrl.fromLocalFile(os.path.join(PluginRegistry.getInstance().getPluginPath(self.getPluginId()), "ConfigDialog.qml"))
        self._qml_component = QQmlComponent(Application.getInstance()._engine, path)

        # We need access to engine (although technically we can't)
        self._qml_context = QQmlContext(Application.getInstance()._engine.rootContext())
        self._qml_context.setContextProperty("manager", self)
        self._dialog = self._qml_component.create(self._qml_context)
        if self._dialog is None:
            Logger.log("e", "QQmlComponent status %s", self._qml_component.status())
            Logger.log("e", "QQmlComponent errorString %s", self._qml_component.errorString())
