# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QTimer
from cura.Scene.CuraSceneNode import CuraSceneNode

from UM.Application import Application
from UM.Extension import Extension
from UM.Logger import Logger


class ModelChecker(Extension):
    def __init__(self):
        super().__init__()

        self._update_timer = QTimer()
        self._update_timer.setInterval(2000)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self.checkObjects)

        self._nodes_to_check = set()

        ## Reacting to an event. ##
        Application.getInstance().mainWindowChanged.connect(self.logMessage) #When the main window is created, log a message.
        Application.getInstance().getController().getScene().sceneChanged.connect(self._onSceneChanged)

    ##  Adds a message to the log, as an example of how to listen to events.
    def logMessage(self):
        Logger.log("i", "This is an example log message. yeaaa")

    def checkObjects(self):
        Logger.log("d", "############# checking....")

    def _onSceneChanged(self, source):
        if isinstance(source, CuraSceneNode) and source.callDecoration("isSliceable"):
            Logger.log("d", "triggurrrr")
            self._nodes_to_check.add(source)
            self._update_timer.start()
