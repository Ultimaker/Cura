# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import Qt #For shortcut keys.
from typing import Optional

from UM.Application import Application #To change the active view.
from UM.Event import Event #To register mouse movements.
from UM.Tool import Tool #The interface we're implementing.

class CustomSupport(Tool):
    def __init__(self):
        super().__init__()
        self._shortcut_key = Qt.Key_S
        self._previous_view = None #type: Optional[str] #This tool forces SolidView. When the tool is disabled, it goes back to the original view.

    def event(self, event: Event):
        if event.type == Event.ToolActivateEvent:
            active_view = Application.getInstance().getController().getActiveView()
            if active_view is not None:
                self._previous_view = active_view.getPluginId()
            Application.getInstance().getController().setActiveView("SolidView")
        elif event.type == Event.ToolDeactivateEvent:
            if self._previous_view is not None:
                Application.getInstance().getController().setActiveView(self._previous_view)
                self._previous_view = None