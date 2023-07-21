from UM.Extension import Extension
from PyQt6.QtCore import pyqtSlot, pyqtSignal, pyqtProperty, QObject
from UM.Application import Application
from UM.Logger import Logger
from UM.Message import Message
from UM.i18n import i18nCatalog

from .Bcn3DFixes import Bcn3DFixes

catalog = i18nCatalog("cura")

class BCN3DPostSlicing(QObject, Extension):
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        Extension.__init__(self)
        self._bcn3d_fixes_job = None
        Application.getInstance().getOutputDeviceManager().writeStarted.connect(self.applyPostSlice)

    def applyPostSlice(self, output_device)  -> None:
        if self._bcn3d_fixes_job is not None and self._bcn3d_fixes_job.isRunning():
            return
        container = Application.getInstance().getGlobalContainerStack()
        scene = Application.getInstance().getController().getScene()
        if hasattr(scene, "gcode_dict"):
            gcode_dict = getattr(scene, "gcode_dict")
            if gcode_dict:
                for i in gcode_dict:
                    self._bcn3d_fixes_job = Bcn3DFixes(container, gcode_dict[i])
                    self._bcn3d_fixes_job.start()