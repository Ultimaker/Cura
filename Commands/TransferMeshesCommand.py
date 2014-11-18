from Cura.Backend.Command import Command
from Cura.plugins.CuraBackendEngine.Commands.TransferMeshCommand import TransferMeshCommand

class TransferMeshesCommand(Command):
    def __init__(self):
        super(TransferMeshesCommand,self).__init__()
        
    def send(self, meshes):
        command = TransferMeshCommand(self._socket)
        for mesh in meshes:
            command.send(mesh)
            