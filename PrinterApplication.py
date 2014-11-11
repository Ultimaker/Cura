from Cura.Application import Application

class PrinterApplication(Application):
    def __init__(self):
        super(PrinterApplication, self).__init__()
        
    def run(self):
        print("Shoopdawoop")
