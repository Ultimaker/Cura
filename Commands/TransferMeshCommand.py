from Cura.Backend.Command import Command
from Cura.plugins.CuraBackendEngine.Commands.TransferVertCommand import TransferVertCommand

class TransferMeshCommand(Command):
    def __init__(self):
        super(TransferMeshCommand,self).__init__()
    
    def send(self, mesh_data):
        vertices = mesh_data.getVerticesList()
        self._socket.sendCommand(0x00200001, len(vertices)) # Tell other side that mesh with num vertices is going to be sent.
        
        command = TransferVertCommand(self._socket)
        command.send(vertices)
        
        
    def recieve(self):
        command_id, data = self._socket.getNextCommand()
        if(command_id is not 0x00200001):
            print("Wrong command!")
            return None
        unpacked_data = struct('