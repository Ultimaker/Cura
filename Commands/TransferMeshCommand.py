from Cura.Backend.Command import Command
from Cura.plugins.CuraBackendEngine.Commands.TransferVertCommand import TransferVertCommand

class TransferMeshCommand(Command):
    def __init__(self):
        super(TransferMeshCommand,self).__init__()
    
    def send(self, mesh_data):
        vertices = mesh_data.getVertices()
        command = TransferVertCommand(self._socket)
        for vertex in vertices:
            command.send(vertex)