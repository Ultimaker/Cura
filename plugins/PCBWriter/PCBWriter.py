#  Copyright (c) 2024 Ultimaker B.V.
#  Cura is released under the terms of the LGPLv3 or higher.
import json
import re

from threading import Lock

from typing import Optional, cast, List, Dict, Pattern, Set

from UM.Mesh.MeshWriter import MeshWriter
from UM.Math.Vector import Vector
from UM.Logger import Logger
from UM.Math.Matrix import Matrix
from UM.Application import Application
from UM.Message import Message
from UM.Resources import Resources
from UM.Scene.SceneNode import SceneNode
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.EmptyInstanceContainer import EmptyInstanceContainer
from PyQt6.QtQml import qmlRegisterType

from cura.CuraApplication import CuraApplication
from cura.CuraPackageManager import CuraPackageManager
from cura.Settings import CuraContainerStack
from cura.Utils.Threading import call_on_qt_thread
from cura.Snapshot import Snapshot

from PyQt6.QtCore import QBuffer

import pySavitar as Savitar

import numpy
import datetime

import zipfile
import UM.Application

from .PCBDialog import PCBDialog
from .SettingsExportModel import SettingsExportModel
from .SettingsExportGroup import SettingsExportGroup

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

class PCBWriter(MeshWriter):
    def __init__(self):
        super().__init__()

        qmlRegisterType(SettingsExportModel, "PCBWriter", 1, 0, "SettingsExportModel")
        qmlRegisterType(SettingsExportGroup, "PCBWriter", 1, 0, "SettingsExportGroup")
        #qmlRegisterUncreatableType(SettingsExportGroup.Category, "PCBWriter", 1, 0, "SettingsExportGroup.Category")

        self._config_dialog = None
        self._main_thread_lock = Lock()

    def write(self, stream, nodes, mode = MeshWriter.OutputMode.BinaryMode) -> bool:
        self._main_thread_lock.acquire()
        # Start configuration window in main application thread
        CuraApplication.getInstance().callLater(self._write, stream, nodes, mode)
        self._main_thread_lock.acquire()  # Block until lock has been released, meaning the config is over

        self._main_thread_lock.release()
        return True

    def _write(self, stream, nodes, mode):
        self._config_dialog = PCBDialog()
        self._config_dialog.finished.connect(self._onDialogClosed)
        self._config_dialog.show()

    def _onDialogClosed(self):
        self._main_thread_lock.release()
