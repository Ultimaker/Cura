from Cura.Wx.WxApplication import WxApplication
from Cura.Wx.MainWindow import MainWindow

from Cura.Scene.SceneObject import SceneObject

import wx

class PrinterApplication(WxApplication):
    def __init__(self):
        super(PrinterApplication, self).__init__()
        
    def run(self):
        self._plugin_registry.loadPlugins({ "type": "StorageDevice" })
        self._plugin_registry.loadPlugins({ "type": "View" })
        self._plugin_registry.loadPlugins({ "type": "MeshHandler" })
        
        self.getController().setActiveView("MeshView")

        root = self.getController().getScene().getRoot()
        mesh = SceneObject()
        mesh.setMeshData(self.getMeshFileHandler().read("plugins/STLReader/simpleTestCube.stl",self.getStorageDevice('local')))
        root.addChild(mesh)

        window = MainWindow("Cura Printer", self)
        window.getCanvas().setBackgroundColor(wx.Colour(255, 0, 0, 255))
        window.Show()
        super(PrinterApplication, self).run()
