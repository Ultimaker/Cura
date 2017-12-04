# Copyright (c) 2017 Ultimaker B.V.

from UM.PluginObject import PluginObject


#   Abstract class for sidebar view objects.
#   By default the sidebar is Cura's settings, slicing and printing overview.
#   The last plugin to claim the sidebar QML target will be displayed.
class SidebarView(PluginObject):

    def __init__(self):
        super().__init__()
        print("sidebar view hello")
