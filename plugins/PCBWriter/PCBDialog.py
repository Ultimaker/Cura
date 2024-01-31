# Copyright (c) 2024 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt6.QtCore import pyqtSignal, QObject, pyqtProperty, QCoreApplication, QUrl, pyqtSlot
from PyQt6.QtGui import QDesktopServices
from typing import List, Optional, Dict, cast

from cura.Machines.Models.MachineListModel import MachineListModel
from cura.Machines.Models.IntentTranslations import intent_translations
from cura.Settings.GlobalStack import GlobalStack
from UM.Application import Application
from UM.FlameProfiler import pyqtSlot
from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.Message import Message
from UM.PluginRegistry import PluginRegistry
from UM.Settings.ContainerRegistry import ContainerRegistry

import os
import threading
import time

from cura.CuraApplication import CuraApplication

i18n_catalog = i18nCatalog("cura")


class PCBDialog(QObject):
    finished = pyqtSignal()

    def __init__(self, parent = None) -> None:
        super().__init__(parent)

        plugin_path = os.path.dirname(__file__)
        dialog_path = os.path.join(plugin_path, 'PCBDialog.qml')
        self._view = CuraApplication.getInstance().createQmlComponent(dialog_path, {"manager": self})

    def show(self) -> None:
        self._view.show()

    @pyqtSlot()
    def notifyClosed(self):
        self.finished.emit()
