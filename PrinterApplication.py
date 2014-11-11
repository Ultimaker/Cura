from Cura.Wx.WxApplication import WxApplication
from Cura.Wx.MainWindow import MainWindow

class PrinterApplication(WxApplication):
    def __init__(self):
        super(PrinterApplication, self).__init__()
        
    def run(self):
        window = MainWindow("Cura Printer")
        window.Show()
        super(PrinterApplication, self).run()
