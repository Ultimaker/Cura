from UM.Backend.Backend import Backend
from UM.Application import Application
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Preferences import Preferences

from . import Cura_pb2

class CuraEngineBackend(Backend):
    def __init__(self):
        super().__init__()

        self._scene = Application.getInstance().getController().getScene()
        self._scene.sceneChanged.connect(self._onSceneChanged)

        self._message_handlers[Cura_pb2.SlicedObjectList] = self._onSlicedObjectListMessage
        self._message_handlers[Cura_pb2.Progress] = self._onProgressMessage
        self._message_handlers[Cura_pb2.GCode] = self._onGCodeMessage
        self._message_handlers[Cura_pb2.ObjectPrintTime] = self._onObjectPrintTimeMessage

    def getEngineCommand(self):
        return [Preferences.getPreference("BackendLocation"), '--connect', "127.0.0.1:{0}".format(self._port)]

    def _onSceneChanged(self, source):
        if (type(source) is not SceneNode) or (source is self._scene.getRoot()):
            return

        objects = []
        for node in DepthFirstIterator(self._scene.getRoot()):
            if type(node) is SceneNode and node.getMeshData():
                objects.append(node)

        msg = Cura_pb2.ObjectList()
        for object in objects:
            meshData = object.getMeshData()

            obj = msg.objects.add()
            obj.vertices = meshData.getVerticesAsByteArray()

            if meshData.hasNormals():
                obj.normals = meshData.getNormalsAsByteArray()

            if meshData.hasIndices():
                obj.indices = meshData.getIndicesAsByteArray()

        self._socket.sendMessage(msg)

    def _onSlicedObjectListMessage(self, message):
        print('Received Sliced Objects')

        for object in message.objects:
            print('Object:', object.id)
            for layer in object.layers:
                print('  Layer:', layer.id)

    def _onProgressMessage(self, message):
        self.processingProgress.emit(message.amount)

    def _onGCodeMessage(self, message):
        pass

    def _onObjectPrintTimeMessage(self, message):
        pass

    def _createSocket(self):
        super()._createSocket()
        
        self._socket.registerMessageType(1, Cura_pb2.ObjectList)
        self._socket.registerMessageType(2, Cura_pb2.SlicedObjectList)
        self._socket.registerMessageType(3, Cura_pb2.Progress)
        self._socket.registerMessageType(4, Cura_pb2.GCode)
        self._socket.registerMessageType(5, Cura_pb2.ObjectPrintTime)
