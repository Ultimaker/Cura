from UM.Backend.Command import Command
from UM.plugins.CuraBackendEngine.Commands.TransferMeshCommand import TransferMeshCommand

class TransferMeshesCommand(Command):
    def __init__(self):
        super(TransferMeshesCommand,self).__init__()
        
    def send(self, meshes):
        self._socket.sendCommand(0x00200000,len(meshes)) # Tell other side that n meshes are going to be sent.
        command = TransferMeshCommand(self._socket)
        for mesh in meshes:
            command.send(mesh)
    
    def recieve(self, num_meshes):
        meshes = []
        command = TransferMeshCommand(self._socket)
        for x in range(0,num_meshes):
            meshes.append(command.recieve())
        return meshes