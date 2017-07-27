# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import os
import threading

from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QObject
from PyQt5.QtQml import QQmlComponent, QQmlContext

from UM.FlameProfiler import pyqtSlot
from UM.Application import Application
from UM.PluginRegistry import PluginRegistry

from UM.i18n import i18nCatalog

from UM.Preferences import Preferences

catalog = i18nCatalog("cura")


class SolidWorksReaderUI(QObject):
    show_config_ui_trigger = pyqtSignal()

    def __init__(self):
        super().__init__()

        Preferences.getInstance().addPreference("cura_solidworks/choice_on_exporting_stl_quality", "always_ask")

        self._cancelled = False
        self._ui_view = None
        self.show_config_ui_trigger.connect(self._onShowConfigUI)

        self.quality = None

        self._ui_lock = threading.Lock()

    def getCancelled(self):
        return self._cancelled

    def waitForUIToClose(self):
        self._ui_lock.acquire()
        self._ui_lock.release()

    def showConfigUI(self):
        preference = Preferences.getInstance().getValue("cura_solidworks/choice_on_exporting_stl_quality")
        if preference != "always_ask":
            if preference == "always_use_fine":
                self.quality = "fine"
            elif preference == "always_use_coarse":
                self.quality = "coarse"
            else:
                self.quality = "fine"
            return

        self._ui_lock.acquire()
        self._cancelled = False
        self.show_config_ui_trigger.emit()

    @pyqtSlot(str, bool)
    def setQuality(self, quality, remember_my_choice):
        self.quality = quality
        if not remember_my_choice:
            Preferences.getInstance().setValue("cura_solidworks/choice_on_exporting_stl_quality", "always_ask")
        else:
            choice = "always_use_fine"
            if quality == "coarse":
                choice = "always_use_coarse"
            Preferences.getInstance().setValue("cura_solidworks/choice_on_exporting_stl_quality", choice)

    def _onShowConfigUI(self):
        if self._ui_view is None:
            self._createConfigUI()
        self._ui_view.show()

    def _createConfigUI(self):
        if self._ui_view is None:
            path = QUrl.fromLocalFile(os.path.join(PluginRegistry.getInstance().getPluginPath("CuraSolidWorksPlugin"), "ExportSTLUI.qml"))
            component = QQmlComponent(Application.getInstance()._engine, path)
            self._ui_context = QQmlContext(Application.getInstance()._engine.rootContext())
            self._ui_context.setContextProperty("manager", self)
            self._ui_view = component.create(self._ui_context)

            self._ui_view.setFlags(self._ui_view.flags() & ~Qt.WindowCloseButtonHint & ~Qt.WindowMinimizeButtonHint & ~Qt.WindowMaximizeButtonHint)

    @pyqtSlot()
    def onOkButtonClicked(self):
        self._cancelled = False
        self._ui_view.close()
        self._ui_lock.release()

    @pyqtSlot()
    def onCancelButtonClicked(self):
        self._cancelled = True
        self._ui_view.close()
        self._ui_lock.release()
