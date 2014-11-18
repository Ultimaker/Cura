from Cura.Backend.Command import Command

class TransferVertCommand(Command):
    def __init__(self):
        super(TransferVertCommand,self).__init__()
         
    def send(self, vertex):
        self._socket.sendData(self._id, vertex.toString())