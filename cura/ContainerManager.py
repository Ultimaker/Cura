# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal

import UM.Settings

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

class ContainerManager(QObject):
    def __init__(self, parent = None):
        super().__init__(parent)

    @pyqtSlot(str)
    def duplicateContainer(self, container_id):
        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id = container_id)
        if not containers:
            return

        new_name = UM.Settings.ContainerRegistry.getInstance().uniqueName(containers[0].getName())
        new_material = containers[0].duplicate(new_name)
        UM.Settings.ContainerRegistry.getInstance().addContainer(new_material)

    @pyqtSlot(str, str)
    def renameContainer(self, container_id, new_name):
        pass

    @pyqtSlot(str)
    def removeContainer(self, container_id):
        pass

def createContainerManager(engine, js_engine):
    return ContainerManager()
