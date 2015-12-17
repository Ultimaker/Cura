# Copyright (c) 2015 Ultimaker B.V.
# Copyright (c) 2013 David Braam
# Cura is released under the terms of the AGPLv3 or higher.

import os

from PyQt5.QtCore import Qt, QUrl, pyqtSignal, pyqtSlot, QObject
from PyQt5.QtQml import QQmlComponent, QQmlContext

from UM.Application import Application
from UM.PluginRegistry import PluginRegistry
from UM.Logger import Logger

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


class ImageReaderUI(QObject):
    show_config_ui_trigger = pyqtSignal()

    def __init__(self, image_reader):
        super(ImageReaderUI, self).__init__()
        self.image_reader = image_reader
        self._ui_view = None
        self.show_config_ui_trigger.connect(self._actualShowConfigUI)
        self.size = 120
        self.base_height = 2
        self.peak_height = 12
        self.smoothing = 1

    def showConfigUI(self):
        self.show_config_ui_trigger.emit()

    def _actualShowConfigUI(self):
        if self._ui_view is None:
            self._createConfigUI()
        self._ui_view.show()

    def _createConfigUI(self):
        if self._ui_view is None:
            Logger.log("d", "Creating ImageReader config UI")
            path = QUrl.fromLocalFile(os.path.join(PluginRegistry.getInstance().getPluginPath("ImageReader"), "ConfigUI.qml"))
            component = QQmlComponent(Application.getInstance()._engine, path)
            self._ui_context = QQmlContext(Application.getInstance()._engine.rootContext())
            self._ui_context.setContextProperty("manager", self)
            self._ui_view = component.create(self._ui_context)

            self._ui_view.setFlags(self._ui_view.flags() & ~Qt.WindowCloseButtonHint & ~Qt.WindowMinimizeButtonHint & ~Qt.WindowMaximizeButtonHint);

    @pyqtSlot()
    def onOkButtonClicked(self):
        self.image_reader._canceled = False
        self.image_reader._wait = False
        self._ui_view.close()

    @pyqtSlot()
    def onCancelButtonClicked(self):
        self.image_reader._canceled = True
        self.image_reader._wait = False
        self._ui_view.close()

    @pyqtSlot(str)
    def onSizeChanged(self, value):
        if (len(value) > 0):
            self.size = float(value)
        else:
            self.size = 0

    @pyqtSlot(str)
    def onBaseHeightChanged(self, value):
        if (len(value) > 0):
            self.base_height = float(value)
        else:
            self.base_height = 0

    @pyqtSlot(str)
    def onPeakHeightChanged(self, value):
        if (len(value) > 0):
            self.peak_height = float(value)
        else:
            self.peak_height = 0

    @pyqtSlot(str)
    def onSmoothingChanged(self, value):
        if (len(value) > 0):
            self.smoothing = int(value)
        else:
            self.smoothing = 0
