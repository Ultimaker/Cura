from Cura.Backend.Command import Command

class TransferVerticeListCommand(Command):
    def __init__(self):
        super(TransferVertCommand,self).__init__()
         
    def send(self, vertices):
        self._socet.sendCommandPacked(0x00200002, vertices.toString()) # Send vertex list