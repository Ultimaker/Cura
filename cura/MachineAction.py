# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os
from typing import Optional

from PyQt5.QtCore import QObject, QUrl, pyqtSlot, pyqtProperty, pyqtSignal

from UM.Logger import Logger
from UM.PluginObject import PluginObject
from UM.PluginRegistry import PluginRegistry


class MachineAction(QObject, PluginObject):
    """Machine actions are actions that are added to a specific machine type.

    Examples of such actions are updating the firmware, connecting with remote devices or doing bed leveling. A
    machine action can also have a qml, which should contain a :py:class:`cura.MachineAction.MachineAction` item.
    When activated, the item will be displayed in a dialog and this object will be added as "manager" (so all
    pyqtSlot() functions can be called by calling manager.func())
    """

    def __init__(self, key: str, label: str = "") -> None:
        """Create a new Machine action.

        :param key: unique key of the machine action
        :param label: Human readable label used to identify the machine action.
        """

        super().__init__()
        self._key = key
        self._label = label
        self._qml_url = ""
        self._view = None
        self._finished = False

    labelChanged = pyqtSignal()
    onFinished = pyqtSignal()

    def getKey(self) -> str:
        return self._key

    def needsUserInteraction(self) -> bool:
        """Whether this action needs to ask the user anything.

         If not, we shouldn't present the user with certain screens which otherwise show up.

        :return: Defaults to true to be in line with the old behaviour.
        """

        return True

    @pyqtProperty(str, notify = labelChanged)
    def label(self) -> str:
        return self._label

    def setLabel(self, label: str) -> None:
        if self._label != label:
            self._label = label
            self.labelChanged.emit()

    @pyqtSlot()
    def reset(self) -> None:
        """Reset the action to it's default state.
        
        This should not be re-implemented by child classes, instead re-implement _reset.

        :py:meth:`cura.MachineAction.MachineAction._reset`
        """

        self._finished = False
        self._reset()

    def _reset(self) -> None:
        """Protected implementation of reset.
        
        See also :py:meth:`cura.MachineAction.MachineAction.reset`
        """

        pass

    @pyqtSlot()
    def setFinished(self) -> None:
        self._finished = True
        self._reset()
        self.onFinished.emit()

    @pyqtProperty(bool, notify = onFinished)
    def finished(self) -> bool:
        return self._finished

    def _createViewFromQML(self) -> Optional["QObject"]:
        """Protected helper to create a view object based on provided QML."""

        plugin_path = PluginRegistry.getInstance().getPluginPath(self.getPluginId())
        if plugin_path is None:
            Logger.log("e", "Cannot create QML view: cannot find plugin path for plugin [%s]", self.getPluginId())
            return None
        path = os.path.join(plugin_path, self._qml_url)

        from cura.CuraApplication import CuraApplication
        view = CuraApplication.getInstance().createQmlComponent(path, {"manager": self})
        return view

    @pyqtProperty(QUrl, constant = True)
    def qmlPath(self) -> "QUrl":
        plugin_path = PluginRegistry.getInstance().getPluginPath(self.getPluginId())
        if plugin_path is None:
            Logger.log("e", "Cannot create QML view: cannot find plugin path for plugin [%s]", self.getPluginId())
            return QUrl("")
        path = os.path.join(plugin_path, self._qml_url)
        return QUrl.fromLocalFile(path)

    @pyqtSlot(result = QObject)
    def getDisplayItem(self) -> Optional["QObject"]:
        return self._createViewFromQML()
