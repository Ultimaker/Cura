# Copyright (c) 2017 Ultimaker B.V.

from PyQt5.QtCore import QObject

from cura.Sidebar.SidebarView import SidebarView

class SettingsSidebarView(QObject, SidebarView):

    def __init__(self):
        super().__init__()
