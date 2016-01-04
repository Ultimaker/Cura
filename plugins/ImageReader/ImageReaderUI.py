# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import os
import threading

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

	# There are corresponding values for these fields in ConfigUI.qml. 
	# If you change the values here, consider updating ConfigUI.qml as well.
        self.size = 120	
        self.base_height = 2
        self.peak_height = 12
        self.smoothing = 1

        self._ui_lock = threading.Lock()
        self._cancelled = False

    def getCancelled(self):
        return self._cancelled

    def waitForUIToClose(self):
        self._ui_lock.acquire()
        self._ui_lock.release()

    def showConfigUI(self):
        self._ui_lock.acquire()
        self._cancelled = False
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
        self._cancelled = False
        self._ui_view.close()
        self._ui_lock.release()

    @pyqtSlot()
    def onCancelButtonClicked(self):
        self._cancelled = True
        self._ui_view.close()
        self._ui_lock.release()

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

    @pyqtSlot(float)
    def onSmoothingChanged(self, value):
        self.smoothing = int(value)
