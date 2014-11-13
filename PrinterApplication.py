from Cura.Wx.WxApplication import WxApplication
from Cura.Wx.MainWindow import MainWindow

class PrinterApplication(WxApplication):
    def __init__(self):
        super(PrinterApplication, self).__init__()
        
    def run(self):
        self._plugin_registry.loadPlugins({ "type": "StorageDevice" })
        self._plugin_registry.loadPlugins({ "type": "View" })
        
        self.getController().setActiveView("MeshView")
        
        window = MainWindow("Cura Printer", self)
        window.Show()
        super(PrinterApplication, self).run()
