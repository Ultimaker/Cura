# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtSignal, pyqtProperty, QObject, QVariant


class PrintJobOutputModel(QObject):

    def __init__(self, parent=None):
        super().__init__(parent)