from Cura.Wx.WxApplication import WxApplication

class PrinterApplication(WxApplication):
    def __init__(self):
        super(PrinterApplication, self).__init__()
        
    def run(self):
        super(PrinterApplication, self).run()
