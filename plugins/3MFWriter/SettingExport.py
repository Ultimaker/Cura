#  Copyright (c) 2024 Ultimaker B.V.
#  Cura is released under the terms of the LGPLv3 or higher.

from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal


class SettingExport(QObject):

    def __init__(self, id, name, value, value_name, selectable, show):
        super().__init__()
        self.id = id
        self._name = name
        self._value = value
        self._value_name = value_name
        self._selected = selectable
        self._selectable = selectable
        self._show_in_menu = show

    @pyqtProperty(str, constant=True)
    def name(self):
        return self._name

    @pyqtProperty(str, constant=True)
    def value(self):
        return self._value

    @pyqtProperty(str, constant=True)
    def valuename(self):
        return str(self._value_name)

    selectedChanged = pyqtSignal(bool)

    def setSelected(self, selected):
        if selected != self._selected:
            self._selected = selected
            self.selectedChanged.emit(self._selected)

    @pyqtProperty(bool, fset = setSelected, notify = selectedChanged)
    def selected(self):
        return self._selected

    @pyqtProperty(bool, constant=True)
    def selectable(self):
        return self._selectable

    @pyqtProperty(bool, constant=True)
    def isVisible(self):
        return self._show_in_menu
