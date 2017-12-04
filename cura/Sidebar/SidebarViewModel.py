# Copyright (c) 2017 Ultimaker B.V.
from PyQt5.QtCore import Qt
from UM.Qt.ListModel import ListModel
from UM.Application import Application
from UM.PluginRegistry import PluginRegistry

##  The SidebarViewModel is the default sidebar view in Cura with all the print settings and print button.
class SidebarViewModel(ListModel):
    IdRole = Qt.UserRole + 1
    NameRole = Qt.UserRole + 2
    ActiveRole = Qt.UserRole + 3

    def __init__(self, parent = None):
        super().__init__(parent)

        