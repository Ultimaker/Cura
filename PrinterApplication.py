from Cura.WxApplication import WxApplication

import wx

class PrinterApplication(WxApplication):
    def __init__(self):
        super(PrinterApplication, self).__init__()
        
    def run(self):
        frame = wx.Frame(None, wx.ID_ANY, "Hello World")
        frame.Show(True)
        super(PrinterApplication, self).run()
